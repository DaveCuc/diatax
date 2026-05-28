from typing import Tuple, Any
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState
from diatax.services.llm_service import LLMService

class Researcher(BaseAgent):
    """
    Researcher Agent: Analyzes source code and dependency map 
    to extract technical metadata and identify logic gaps.
    """
    agent_name = "Researcher"
    role = "Technical System Architect"

    def __init__(self, model: str, llm_service: LLMService):
        super().__init__(model)
        self.llm_service = llm_service

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        """
        Analyzes code or graphify context to provide a technical foundation.
        """
        try:
            input_data = ""
            if state.graphify_context:
                input_data = f"GRAPHIFY CONTEXT:\n{state.graphify_context}"
            elif state.raw_code:
                input_data = f"SOURCE CODE:\n{state.raw_code}"
            else:
                return state, AgentResponse(status="error", data={}, message="No input data (code or graphify) in state.")

            system_prompt = (
                "You are an expert technical architect. Analyze the provided project structure and source code. "
                "You must provide a high-level summary and technical map of the entire project. "
                "Output your response strictly as a JSON object inside a ```json markdown block.\n\n"
                "JSON Schema:\n"
                "{\n"
                "  \"metadata\": { \"version\": \"string\", \"author\": \"string\" },\n"
                "  \"summary\": \"string\",\n"
                "  \"tech_stack\": [\"string\"],\n"
                "  \"code_gaps\": [\"string\"]\n"
                "}"
            )
            
            user_prompt = f"Analyze this project structure and content:\n\n{input_data}"

            analysis = self.llm_service.send_request(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.model,
                schema={"type": "object"}
            )

            state.technical_analysis = analysis
            return state, AgentResponse(status="success", data=analysis, message="Technical analysis completed.")

        except Exception as e:
            return state, AgentResponse(status="error", data={}, message=f"Error during IA analysis: {str(e)}")
