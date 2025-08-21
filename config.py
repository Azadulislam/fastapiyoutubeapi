from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    youtube_api_key: str
    youtube_api_url: str

    class Config:
        env_file = ".env"

settings = Settings()
