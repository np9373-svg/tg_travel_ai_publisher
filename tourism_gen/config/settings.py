from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    OPENAI_KEY : str
    YC_API_KEY: str
    FOLDER_ID: str
    OPENAI_BASE_URL: str

    model_config = {
        "env_file": BASE_DIR / ".env"
    }


settings = Settings()
