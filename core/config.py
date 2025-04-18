import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_TITLE: str = "NLP Keyword Extractor with Gemini"
    APP_DESCRIPTION: str = "Extract keywords and generate multiple-choice questions using spaCy and Gemini AI"
    APP_VERSION: str = "1.0.0"

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()