from pydantic import BaseModel, Field
from typing import Any, Union, Dict, Optional

class AgentResponse(BaseModel):
    """
    Modelo genérico para todas las respuestas de los agentes.
    Asegura consistencia en la comunicación entre capas.
    """
    status: str  # e.g., "success", "error", "pending"
    data: Union[Dict[str, Any], str]
    message: str = ""

class WorkflowState(BaseModel):
    """
    La 'Pizarra' (Shared State) del sistema.
    Nota: Su estabilidad depende de la entrega de datos estructurados por parte de los agentes.
    """
    codigo_crudo: Optional[str] = None
    contexto_graphify: Optional[Dict[str, Any]] = None
    analisis_tecnico: Optional[Dict[str, Any]] = None
    borrador_markdown: Optional[str] = None
    contexto_readme: str = ""
    ruta_referencia: str = "."
    mapa_dependencias: Optional[Dict[str, Any]] = None
    resultados_diataxis: Dict[str, str] = Field(default_factory=dict)
    feedback_juez: Optional[str] = None
    contexto_usuario: Optional[str] = None
    documento_web: Optional[str] = None
    documento_web_html: Optional[str] = None
    documento_web_css: Optional[str] = None
    intentos_escritura: int = 0
    documento_final_aprobado: bool = False
