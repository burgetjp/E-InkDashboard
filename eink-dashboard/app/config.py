from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8000
    noaa_grid: str = "PSR/166,61"
    refresh_hour_interval: int = 1

    model_config = {"env_file": ".env"}


settings = Settings()
