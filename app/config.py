from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL_SYNC: str
    DATABASE_URL_ASYNC: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
