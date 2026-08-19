"""
Centralized application configuration.

All environment-dependent values live here so the rest of the codebase
never touches os.environ directly. Backed by pydantic-settings, which
reads from a .env file in development and from real environment
variables in production (Docker, Railway, Render, etc).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CareCompass"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql://carecompass:carecompass@localhost:5432/carecompass"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:5173"

    cms_care_compare_base_url: str = "https://data.cms.gov/provider-data/api/1/datastore/query"
    google_maps_api_key: str = ""

    openai_api_key:str =""
    openai_model: str ="gpt-5.6"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so we parse the environment exactly once per process."""
    return Settings()
