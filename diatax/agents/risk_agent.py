from typing import Tuple, Any
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState
from diatax.services.llm_service import LLMService

class RiskAgent(BaseAgent):
    """
    Risk Agent: Performs SAST (Static Application Security Testing) 
    to find common vulnerabilities in source code.
    """
    agent_name = "RiskAgent"
    role = "Cybersecurity Auditor"

    def __init__(self, model: str, llm_service: LLMService):
        super().__init__(model)
        self.llm_service = llm_service

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        """
        Analyzes code to detect security risks.
        """
        try:
            if not state.raw_code:
                return state, AgentResponse(status="error", data={}, message="No source code in state to audit.")

            system_prompt = (
                "You are a cybersecurity expert. Perform a security audit (SAST) "
                "on the following code. Identify vulnerabilities such as injections, "
                "path traversal, sensitive data exposure, etc. Return a JSON object with "
                "a key 'found_risks' which is a list of objects, each containing: "
                "'severity' (High, Medium, Low), 'location' (line or function), "
                "'description', and 'suggested_solution'."
            )
            
            user_prompt = f"Perform a security audit on the following code:\n\n{state.raw_code}"

            audit_result = self.llm_service.send_request(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.model,
                schema={"type": "object"}
            )

            return state, AgentResponse(status="success", data=audit_result, message="Security audit completed.")

        except Exception as e:
            return state, AgentResponse(status="error", data={}, message=f"Unexpected error in RiskAgent: {str(e)}")
