from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL_SYNC: str
    DATABASE_URL_ASYNC: str
    
    BOT_TOKEN: str
    
    WEBHOOK_URL: str | None = None
    WEBHOOK_PATH: str ='/webhook'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
