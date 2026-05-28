from abc import ABC, abstractmethod
from typing import Tuple, Any
from diatax.core.models import WorkflowState, AgentResponse

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Provides a common interface for the multi-agent system.
    """
    agent_name: str = "BaseAgent"
    role: str = "General Assistant"

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        """
        Main logic of the agent. Receives the shared state and returns 
        the updated state and a standard response.
        """
        pass
