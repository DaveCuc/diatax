from abc import ABC, abstractmethod
from typing import Tuple
from diatax.core.models import AgentResponse, WorkflowState

class BaseAgent(ABC):
    """
    Clase abstracta que define el contrato obligatorio para todos los agentes.
    Incluye metadatos de identidad y operación sobre la Pizarra (WorkflowState).
    """
    nombre_agente: str
    rol: str

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        """
        Método principal que opera sobre la Pizarra.
        Recibe el estado actual, lo modifica y devuelve el estado actualizado junto con una respuesta.
        """
        pass
