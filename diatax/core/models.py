from pydantic import BaseModel, Field
from typing import Any, Union, Dict, Optional

class AgentResponse(BaseModel):
    """
    Generic model for all agent responses.
    Ensures consistency in communication between layers.
    """
    status: str  # e.g., "success", "error", "pending"
    data: Union[Dict[str, Any], str]
    message: str = ""

class WorkflowState(BaseModel):
    """
    The 'Blackboard' (Shared State) of the system.
    Note: Its stability depends on agents delivering structured data.
    """
    raw_code: Optional[str] = None
    graphify_context: Optional[Dict[str, Any]] = None
    technical_analysis: Optional[Dict[str, Any]] = None
    markdown_draft: Optional[str] = None
    readme_context: str = ""
    reference_path: str = "."
    dependency_map: Optional[Dict[str, Any]] = None
    diataxis_results: Dict[str, str] = Field(default_factory=dict)
    judge_feedback: Optional[str] = None
    user_context: Optional[str] = None
    web_document: Optional[str] = None
    web_document_html: Optional[str] = None
    web_document_css: Optional[str] = None
    writing_attempts: int = 0
    final_document_approved: bool = False
    has_graph: bool = False
    output_language: str = "english"
