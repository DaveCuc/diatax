from typing import Tuple, Dict, Any
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState
from diatax.services.llm_service import LLMService
from diatax.core.exceptions import LLMError

class BaseJudge(BaseAgent):
    """
    Base class for Diátaxis Judges.
    """
    def __init__(self, model: str, llm_service: LLMService):
        super().__init__(model)
        self.llm_service = llm_service

    def _execute_judging(self, state: WorkflowState, criteria: str) -> Tuple[WorkflowState, AgentResponse]:
        try:
            if not state.markdown_draft:
                return state, AgentResponse(status="error", data={}, message="No markdown draft to judge.")

            system_prompt = (
                f"You are a quality judge for technical documentation. "
                f"Evaluate if the following document meets these criteria:\n{criteria}\n\n"
                "Return a JSON with: 'approved' (boolean), 'feedback' (string), "
                "and 'improvements' (list of strings)."
            )
            
            user_prompt = f"Evaluate this document:\n\n{state.markdown_draft}"

            evaluation = self.llm_service.send_request(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.model,
                schema={"type": "object"}
            )

            state.final_document_approved = evaluation.get("approved", False)
            state.judge_feedback = evaluation.get("feedback", "")
            
            return state, AgentResponse(status="success", data=evaluation, message="Judging completed.")

        except LLMError as e:
            return state, AgentResponse(status="error", data={}, message=str(e))

class ReferenceJudge(BaseJudge):
    agent_name = "ReferenceJudge"
    role = "Technical Accuracy Auditor"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        criteria = "Must be objective, precise, and contain all technical details without tutorials or guides."
        return self._execute_judging(state, criteria)

class HowToJudge(BaseJudge):
    agent_name = "HowToJudge"
    role = "Practicality Auditor"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        criteria = "Must be a sequence of steps to solve a specific problem. No theory, just action."
        return self._execute_judging(state, criteria)

class TutorialJudge(BaseJudge):
    agent_name = "TutorialJudge"
    role = "Learning Experience Auditor"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        criteria = "Must be educational, easy to follow for a beginner, and provide a successful first experience."
        return self._execute_judging(state, criteria)

class ExplanationJudge(BaseJudge):
    agent_name = "ExplanationJudge"
    role = "Conceptual Clarity Auditor"

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        criteria = "Must provide context, background, and deep understanding of 'why', not just 'how'."
        return self._execute_judging(state, criteria)
