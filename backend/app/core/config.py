from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"

    database_url: str

    @field_validator("database_url")
    @classmethod
    def _forzar_driver_psycopg(cls, valor: str) -> str:
        # Railway inyecta DATABASE_URL como postgres:// o postgresql://
        # (formato psycopg2). El proyecto usa psycopg 3, así que hay que
        # forzar el dialecto +psycopg o SQLAlchemy intenta cargar psycopg2,
        # que ni siquiera está instalado.
        if valor.startswith("postgres://"):
            return valor.replace("postgres://", "postgresql+psycopg://", 1)
        if valor.startswith("postgresql://"):
            return valor.replace("postgresql://", "postgresql+psycopg://", 1)
        return valor

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:4200"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # Token fijo (no JWT) para tareas de sistema (cron/scheduler), p. ej.
    # POST /api/v1/tareas/expirar-reservas. Vacío por defecto: en ese caso
    # require_service_token() rechaza cualquier llamada, así que hay que
    # configurarlo explícitamente en el entorno para habilitar la tarea.
    tareas_token: str = ""

    # Modo generativo del probador (Vertex AI). Sin vertex_project_id
    # configurado, VertexAIProbadorGenerativo falla al primer uso: el modo
    # espejo (Flutter, sin backend) sigue funcionando igual, es el
    # generativo el que queda inhabilitado hasta configurar el proyecto de
    # GCP. Las credenciales van por GOOGLE_APPLICATION_CREDENTIALS, nunca acá.
    vertex_project_id: str = ""
    vertex_location: str = "us-central1"
    vertex_modelo: str = "gemini-3.1-flash-image"


@lru_cache
def get_settings() -> Settings:
    return Settings()
