from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Number of threads in the pool for concurrent MT5 requests
    max_workers: int = 20

    # Request timeout in seconds for MT5 operations
    mt5_timeout: int = 30

    # How many days back to fetch deal history by default
    history_days: int = 90

    # API host and port
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
