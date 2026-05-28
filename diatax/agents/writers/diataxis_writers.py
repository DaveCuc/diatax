from typing import Tuple, Dict, Any
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState
from diatax.services.llm_service import LLMService
from diatax.core.exceptions import LLMError

class BaseWriter(BaseAgent):
    """
    Base class for Diátaxis Writers.
    """
    def __init__(self, model: str, llm_service: LLMService):
        super().__init__(model)
        self.llm_service = llm_service

    def _execute_writing(self, state: WorkflowState, instructions: str) -> Tuple[WorkflowState, AgentResponse]:
        try:
            state.writing_attempts += 1
            
            system_prompt = (
                f"You are an expert technical writer specializing in the Diátaxis framework. "
                f"Your mission is to write a document according to these specific instructions:\n{instructions}\n\n"
                f"LANGUAGE REQUIREMENT: All documentation must be written in {state.output_language}. "
                "Maintain technical terms in English if necessary, but explain them in the target language.\n\n"
                "Use GitHub Flavored Markdown. Be professional, clear, and concise."
            )
            
            user_prompt = (
                f"TECHNICAL ANALYSIS SUMMARY:\n{state.technical_analysis}\n\n"
                f"SOURCE CODE / PROJECT CONTEXT:\n{state.raw_code or 'See Technical Analysis'}\n\n"
                f"PROJECT README CONTEXT:\n{state.readme_context}\n\n"
                f"USER REQUEST/CLARIFICATIONS:\n{state.user_context}\n\n"
                f"PREVIOUS FEEDBACK (if any):\n{state.judge_feedback}\n\n"
                "Based on all the project data provided above, write the document now. "
                "Ensure you cover the whole project structure, not just one part."
            )

            result = self.llm_service.send_request(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.model
            )

            state.markdown_draft = result.get("text", "")
            return state, AgentResponse(status="success", data=state.markdown_draft, message="Document written.")

        except LLMError as e:
            return state, AgentResponse(status="error", data="", message=str(e))

class ReferenceWriter(BaseWriter):
    agent_name = "ReferenceWriter"
    role = "Technical Documenter"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        instructions = (
            "Write a Technical Reference. Principles:\n"
            "1. Information-oriented: Focus on neutral, technical description and facts.\n"
            "2. Austere and authoritative: Accurate, complete, and reliable information without distraction or interpretation.\n"
            "3. Mirror the machinery: The structure of the documentation should reflect the architecture of the code (APIs, classes, functions).\n"
            "4. Content: List facts, parameters, return values, flags, and limitations. No instructions or tutorials."
        )
        return self._execute_writing(state, instructions)

class HowToWriter(BaseWriter):
    agent_name = "HowToWriter"
    role = "Practical Guide Writer"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        instructions = (
            "Write a How-to Guide. Principles:\n"
            "1. Goal-oriented: Address a specific real-world task or problem.\n"
            "2. For competent users: Assume the user knows what they want to achieve. Focus on action.\n"
            "3. Action and only action: Provide a logical sequence of executable steps. No theory or teaching.\n"
            "4. Practical usability: Omit the unnecessary. Focus on smooth progress and flow."
        )
        return self._execute_writing(state, instructions)

class TutorialWriter(BaseWriter):
    agent_name = "TutorialWriter"
    role = "Educational Instructor"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        instructions = (
            "Write a Tutorial (Lesson). Principles:\n"
            "1. Learning-oriented: Take the student by the hand through a learning experience.\n"
            "2. Practical learning: The user must DO something meaningful. Every step should produce a visible result early and often.\n"
            "3. Minimise explanation: Do not explain 'why' here. Focus on the concrete task. No choices or alternatives.\n"
            "4. Narrative of expectations: Tell the user what to expect after each action (e.g., 'The output should look like...')."
        )
        return self._execute_writing(state, instructions)

class ExplanationWriter(BaseWriter):
    agent_name = "ExplanationWriter"
    role = "Conceptual Analyst"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        instructions = (
            "Write an Explanation. Principles:\n"
            "1. Understanding-oriented: Deepen the reader's understanding of the 'why'.\n"
            "2. Context and background: Provide the bigger picture, design decisions, and technical constraints.\n"
            "3. Make connections: Explain how things join together. Discuss alternatives and perspectives.\n"
            "4. Reflection: Offer context that shines a new light on the subject matter. It is a discursive guide."
        )
        return self._execute_writing(state, instructions)
