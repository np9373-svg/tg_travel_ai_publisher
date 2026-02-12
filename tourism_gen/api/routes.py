from fastapi import APIRouter
from models.schemas import GenerateRequest, GenerateResponse
from services.generator import generate_content

router = APIRouter(prefix="", tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest) -> GenerateResponse:
    return generate_content(payload)
