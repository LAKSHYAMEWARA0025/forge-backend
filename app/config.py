from pydantic import BaseSettings

class Settings(BaseSettings):
    ASSEMBLYAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    DB_URL: str = "sqlite:///./app.db"

settings = Settings()
