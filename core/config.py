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

    class Config:
        env_file = ".env"


settings = Settings()