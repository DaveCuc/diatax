from typing import Tuple
import json
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState
from diatax.services.llm_service import LLMService
from diatax.core.exceptions import LLMError

class RiskAgent(BaseAgent):
    """
    Agente de Riesgos: Auditor de ciberseguridad experto.
    Analiza el código en busca de vulnerabilidades y fallas de seguridad.
    """
    nombre_agente = "RiskAgent"
    rol = "Auditor de Seguridad (DevSecOps)"

    def __init__(self, model: str, llm_service: LLMService):
        super().__init__(model)
        self.llm_service = llm_service

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        """
        Analiza el código crudo en busca de riesgos de seguridad.
        """
        if not state.codigo_crudo:
            return state, AgentResponse(
                status="error",
                data={},
                message="No hay código fuente en el estado para auditar."
            )

        system_prompt = (
            "DIRECTIVA DE SEGURIDAD: Eres un auditor de ciberseguridad experto (DevSecOps). "
            "Tu tarea es analizar el código fuente proporcionado e identificar exclusivamente "
            "riesgos de seguridad, vulnerabilidades (OWASP Top 10), malas prácticas de manejo de memoria, "
            "o exposición de datos sensibles. No documentes qué hace el código, solo busca fallas.\n\n"
            "Debes retornar OBLIGATORIAMENTE un objeto JSON con la siguiente estructura:\n"
            "{\n"
            "  \"riesgos_encontrados\": [\n"
            "    {\n"
            "      \"gravedad\": \"Alta/Media/Baja\",\n"
            "      \"descripcion\": \"...\",\n"
            "      \"linea_o_funcion\": \"...\",\n"
            "      \"solucion_sugerida\": \"...\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = f"Realiza una auditoría de seguridad del siguiente código:\n\n{state.codigo_crudo}"

        try:
            audit_result = self.llm_service.enviar_peticion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema={"type": "object"}
            )
            
            # Si la IA devuelve algo mal estructurado, el LLMService ya aplica resiliencia básica.
            return state, AgentResponse(
                status="success",
                data=audit_result,
                message="Auditoría de seguridad completada."
            )

        except LLMError as e:
            return state, AgentResponse(status="error", data={}, message=str(e))
        except Exception as e:
            return state, AgentResponse(status="error", data={}, message=f"Error inesperado en RiskAgent: {str(e)}")
