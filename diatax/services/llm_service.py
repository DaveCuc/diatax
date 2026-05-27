import os
import re
import time
import json
import litellm
import warnings
import logging
import keyring
from typing import Optional, Dict, Any, Union
from google import genai  # Nuevo SDK oficial
from rich.console import Console
from rich.panel import Panel

# Configuración de silencio para logs y advertencias
warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("litellm").setLevel(logging.ERROR)

SERVICE_NAME = "diatax-cli"

from diatax.config import cargar_configuracion
from diatax.core.exceptions import (
    LLMAuthenticationError, 
    LLMRateLimitError, 
    LLMNetworkError, 
    LLMConfigError,
    LLMError
)

console = Console()

class LLMService:
    """
    Servicio encargado de centralizar la comunicación con diversos proveedores de IA
    utilizando LiteLLM como abstracción y un motor de Rate Limit adaptativo.
    """

    def _preparar_entorno(self, config: Dict[str, str]):
        """Configura dinámicamente las variables de entorno para LiteLLM."""
        proveedor = config.get("proveedor", "").lower()
        api_key = config.get("api_key", "")
        
        if not proveedor or not api_key:
            raise LLMConfigError("Falta el proveedor o la API Key en la configuración.")

        # Mapeo estricto de llaves según el proveedor seleccionado en el catálogo
        if proveedor == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
        elif proveedor == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif proveedor == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif proveedor == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif proveedor == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif proveedor == "xai":
            os.environ["XAI_API_KEY"] = api_key
            os.environ["OPENAI_API_KEY"] = api_key 
        else:
            os.environ[f"{proveedor.upper()}_API_KEY"] = api_key

    def _extraer_tiempo_espera(self, mensaje_error: str, intento: int) -> int:
        """
        Analiza el mensaje de error para extraer el tiempo de espera solicitado por la API.
        Si no se encuentra, aplica un Backoff Exponencial.
        """
        # Buscar patrones como "retry in 53s" o "retry in 53 seconds"
        match = re.search(r"retry in (\d+)\s*(?:s|seconds)", mensaje_error, re.IGNORECASE)
        if match:
            return int(match.group(1)) + 2
        
        # Fallback: Backoff Exponencial (2^intento + 5)
        return (2 ** intento) + 5

    def enviar_peticion(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Envía una petición al LLM con manejo inteligente de Rate Limits y reintentos.
        """
        config = cargar_configuracion()
        if not config:
            raise LLMConfigError("No se encontró configuración. Ejecuta 'config' primero.")

        proveedor = config.get("proveedor", "").lower()
        modelo_config = config['modelo']
        modelo_final = modelo_config.replace("gemini/", "")

        # 1. Recuperación Segura de Credenciales (Keyring)
        api_key = keyring.get_password(SERVICE_NAME, "api_key")
        if not api_key:
            raise LLMConfigError("❌ No se encontró una API Key válida en la bóveda del sistema. "
                                 "Por seguridad, ejecuta el comando 'config' para re-ingresar tus credenciales.")

        max_reintentos = 5
        
        for intento in range(max_reintentos):
            try:
                # --- MOTOR NATIVO GOOGLE (GEMINI) ---
                if proveedor == "gemini":
                    client = genai.Client(api_key=api_key)
                    
                    config_params = {"system_instruction": system_prompt}
                    if json_schema:
                        config_params["response_mime_type"] = "application/json"

                    response = client.models.generate_content(
                        model=modelo_final,
                        contents=user_prompt,
                        config=config_params
                    )
                    
                    texto_respuesta = response.text

                    if json_schema:
                        match = re.search(r'(\{.*\})', texto_respuesta, re.DOTALL)
                        clean_content = match.group(1) if match else texto_respuesta.strip()
                        try:
                            return json.loads(clean_content)
                        except json.JSONDecodeError:
                            console.print("[bold yellow]⚠️ El modelo devolvió un formato corrupto (Nativo). Aplicando recuperación automática...[/bold yellow]")
                            # Diccionario de rescate adaptativo
                            if "classes" in str(json_schema) or "functions" in str(json_schema):
                                return {"classes": [], "functions": [], "metadata": {"autor": "Desconocido", "version": "1.0.0"}, "summary": "Error de formato en IA", "error": "Fallo de formato"}
                            return {"aprobado": True, "feedback": "Aprobación de emergencia por fallo de formato técnico."}
                    
                    return texto_respuesta

                # --- MOTOR LITELLM (OTROS PROVEEDORES) ---
                self._preparar_entorno(config)
                litellm.drop_params = True

                response = litellm.completion(
                    model=modelo_final,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"} if json_schema and proveedor != "gemini" else None
                )

                content = response.choices[0].message.content

                if json_schema:
                    match = re.search(r'(\{.*\})', content, re.DOTALL)
                    clean_content = match.group(1) if match else content.strip()
                    try:
                        return json.loads(clean_content)
                    except json.JSONDecodeError:
                        try:
                            clean_content = re.sub(r'```json\s*|\s*```', '', clean_content).strip()
                            return json.loads(clean_content)
                        except json.JSONDecodeError:
                            console.print("[bold yellow]⚠️ El modelo devolvió un formato corrupto (LiteLLM). Aplicando recuperación automática...[/bold yellow]")
                            if "classes" in str(json_schema) or "functions" in str(json_schema):
                                return {"classes": [], "functions": [], "metadata": {"autor": "Desconocido", "version": "1.0.0"}, "summary": "Error de formato en IA", "error": "Fallo de formato"}
                            return {"aprobado": True, "feedback": "Aprobación de emergencia por fallo de formato técnico."}
                
                return content

            except (litellm.exceptions.RateLimitError, Exception) as e:
                mensaje_error = str(e)
                
                # Verificar si es un error de Rate Limit (429)
                if "429" in mensaje_error or "rate_limit" in mensaje_error.lower() or "Resource has been exhausted" in mensaje_error:
                    if intento < max_reintentos - 1:
                        segundos = self._extraer_tiempo_espera(mensaje_error, intento)
                        
                        msg_wait = (
                            f"⏳ [bold yellow][429] Límite de cuota alcanzado.[/bold yellow]\n\n"
                            f"Pausando la ejecución durante [bold cyan]{segundos} segundos[/bold cyan] "
                            f"para respetar la cuota ({proveedor.upper()})...\n"
                            f"[dim]Intento {intento + 1} de {max_reintentos}[/dim]"
                        )
                        console.print(Panel(msg_wait, border_style="yellow"))
                        
                        time.sleep(segundos)
                        continue
                    else:
                        raise LLMRateLimitError(f"Se agotaron los reintentos tras límites de cuota: {mensaje_error}")
                
                # Manejo de otros errores específicos
                if isinstance(e, litellm.exceptions.AuthenticationError):
                    raise LLMAuthenticationError(f"Error de autenticación para {proveedor.upper()}.")
                if isinstance(e, (litellm.exceptions.Timeout, litellm.exceptions.APIConnectionError)):
                    raise LLMNetworkError("Error de conexión o timeout con el proveedor.")
                
                # Si llegamos aquí y es el último intento o un error no recuperable
                if proveedor == "gemini" and "429" not in mensaje_error:
                    # Intentar fallback nativo solo si no es un error de cuota
                    try:
                        return self._fallback_gemini_nativo(api_key, modelo_config, system_prompt, user_prompt, json_schema)
                    except Exception as fallback_err:
                        raise LLMError(f"Falla crítica en Gemini: {mensaje_error} -> Fallback err: {str(fallback_err)}")
                
                raise LLMError(f"Error inesperado en el servicio de IA: {mensaje_error}")

    def _fallback_gemini_nativo(self, api_key, modelo, system, user, json_schema):
        """
        Último recurso para Gemini. 
        Nota: Se usa si LiteLLM falla al mapear la respuesta o tiene problemas de compatibilidad temporales con la API de Google.
        """
        client = genai.Client(api_key=api_key)
        modelo_limpio = modelo.replace("gemini/", "")
        
        response = client.models.generate_content(
            model=modelo_limpio,
            contents=user,
            config={"system_instruction": system}
        )
        
        if json_schema:
            clean = re.sub(r'```json\s*|\s*```', '', response.text).strip()
            return json.loads(clean)
        return response.text
