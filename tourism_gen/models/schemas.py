from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Status = Literal["success", "summary_too_short", "error"]

class GenerateRequest(BaseModel):
    summary: List[str] = Field(
        ...,
        description="Список тезисов (фактов) саммари"
    )
    link: str

class GenerateData(BaseModel):
    text: str
    image_base64: str

class GenerateResponse(BaseModel):
    status: Status
    data: Optional[GenerateData] = None
    error_message: Optional[str] = None
