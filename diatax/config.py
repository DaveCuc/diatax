import json
import os
import sys
import keyring
from pathlib import Path
from rich.console import Console

console = Console()

# Ruta donde se guardará la configuración (~/.diatax_config.json)
CONFIG_FILE = Path.home() / ".diatax_config.json"
SERVICE_NAME = "diatax-cli"

def guardar_configuracion(proveedor: str, modelo: str, api_key: str):
    """
    Guarda la configuración general en JSON y la API Key en el Keyring del sistema.
    Implementa política Fail-Secure: si la bóveda falla, no guarda nada.
    """
    config_data = {
        "proveedor": proveedor,
        "modelo": modelo
    }

    # 1. Guardar API Key en la bóveda del sistema (FAIL-SECURE)
    try:
        keyring.set_password(SERVICE_NAME, "api_key", api_key)
    except Exception as e:
        console.print(f"[bold red]❌ Error crítico de seguridad: El llavero del sistema no está disponible. "
                      f"Por tu protección, la API Key no se guardará en texto plano.[/bold red]")
        sys.exit(1)

    # 2. Guardar el resto en el archivo JSON
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except (PermissionError, OSError) as e:
        console.print(f"[bold red]❌ Error de sistema: No se pudo escribir el archivo de configuración. "
                      f"Detalle: {str(e)}[/bold red]")
        sys.exit(1)

def cargar_configuracion():
    """
    Lee la configuración general y recupera la API Key del Keyring.
    Diferencia entre estados normales y fallos de sistema críticos.
    """
    try:
        if not CONFIG_FILE.exists():
            return {}

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Recuperar la API Key desde el Keyring
        api_key = keyring.get_password(SERVICE_NAME, "api_key")
        if api_key:
            config["api_key"] = api_key

        return config

    except json.JSONDecodeError:
        console.print("[bold yellow]⚠️ Archivo de configuración corrupto detectado. "
                      "Se ignorará para evitar errores.[/bold yellow]")
        return {}
    except (PermissionError, OSError) as e:
        console.print(f"[bold red]❌ Error de sistema: No se puede acceder a la configuración "
                      f"(bloqueo de disco o permisos). Deteniendo para no sobrescribir datos. "
                      f"Detalle: {str(e)}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]⚠️ Error inesperado al leer la configuración: {str(e)}[/bold red]")
        return None