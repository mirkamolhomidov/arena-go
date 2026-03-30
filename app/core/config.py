from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL_SYNC: str
    DATABASE_URL_ASYNC: str
    
    BOT_TOKEN: str
    ERROR_BOT_TOKEN: str | None = None
    ERROR_BOT_CHAT_ID: str | None = None
    
    WEBHOOK_URL: str | None = None
    WEBHOOK_PATH: str ='/webhook'
    BASE_URL: str
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    SQL_ECHO: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
