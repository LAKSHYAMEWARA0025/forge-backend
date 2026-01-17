from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ASSEMBLYAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_PUBLISHABLE_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
