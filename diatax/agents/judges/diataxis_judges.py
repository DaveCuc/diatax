from typing import Tuple
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState
from diatax.services.llm_service import LLMService
from diatax.core.exceptions import LLMError
import json

class DiataxisJudge(BaseAgent):
    """Clase base para jueces Diátaxis."""
    def __init__(self, model: str, llm_service: LLMService):
        super().__init__(model)
        self.llm_service = llm_service

    def _execute_judging(self, state: WorkflowState, quadrant: str, rules: str) -> Tuple[WorkflowState, AgentResponse]:
        if not state.borrador_markdown:
            return state, AgentResponse(status="error", data={}, message="No hay borrador para evaluar.")

        system_prompt = (
            f"Eres un Editor Senior experto en Diátaxis, encargado de validar el cuadrante: {quadrant}. "
            f"Reglas estrictas de validación: {rules}. "
            "Debes retornar OBLIGATORIAMENTE un JSON con: "
            "'aprobado' (bool), 'feedback' (str) y 'puntos_mejora' (lista)."
        )

        user_prompt = f"Evalúa este borrador Markdown:\n\n{state.borrador_markdown}"

        try:
            evaluacion = self.llm_service.enviar_peticion(system_prompt, user_prompt, json_schema={"type": "object"})
            
            if evaluacion.get("aprobado"):
                state.documento_final_aprobado = True
                state.feedback_juez = None
                return state, AgentResponse(status="success", data=evaluacion, message=f"Documentación de {quadrant} aprobada.")
            else:
                state.feedback_juez = evaluacion.get("feedback")
                state.documento_final_aprobado = False
                return state, AgentResponse(status="success", data=evaluacion, message=f"Documentación de {quadrant} requiere mejoras.")
        except LLMError as e:
            return state, AgentResponse(status="error", data={}, message=str(e))

class TutorialJudge(DiataxisJudge):
    nombre_agente = "TutorialJudge"
    rol = "Juez de Tutoriales"
    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        return self._execute_judging(state, "Tutoriales", "Debe ser orientado al aprendizaje, paso a paso, sin asumir conocimientos previos profundos.")

class HowToJudge(DiataxisJudge):
    nombre_agente = "HowToJudge"
    rol = "Juez de Guías (How-to)"
    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        return self._execute_judging(state, "Guías (How-to)", "Debe resolver un problema concreto, ser directo y orientado a la acción.")

class ReferenceJudge(DiataxisJudge):
    nombre_agente = "ReferenceJudge"
    rol = "Juez de Referencia"
    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        return self._execute_judging(state, "Referencia", "Debe ser técnico, neutral, completo y estrictamente informativo.")

class ExplanationJudge(DiataxisJudge):
    nombre_agente = "ExplanationJudge"
    rol = "Juez de Explicación"
    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        return self._execute_judging(state, "Explicación", "Debe profundizar en el 'por qué', dar contexto y facilitar la comprensión teórica.")
