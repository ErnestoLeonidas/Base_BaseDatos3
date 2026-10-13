"""Configuración de la aplicación, leída desde variables de entorno (.env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    oracle_user: str
    oracle_password: str
    oracle_dsn: str
    app_env: str = "desarrollo"

    @property
    def sqlalchemy_database_uri(self) -> URL:
        """Construye la URL de conexión para SQLAlchemy usando el driver thin de oracledb.

        `oracle_dsn` viene en formato Easy Connect ("host:puerto/servicio"). Se usa
        `service_name` como parámetro de consulta (y no la ruta de la URL) porque el
        dialecto de SQLAlchemy interpreta la ruta como SID, no como nombre de servicio.
        """
        host_port, _, service_name = self.oracle_dsn.partition("/")
        host, _, port = host_port.partition(":")
        return URL.create(
            "oracle+oracledb",
            username=self.oracle_user,
            password=self.oracle_password,
            host=host,
            port=int(port) if port else None,
            query={"service_name": service_name} if service_name else {},
        )


@lru_cache
def obtener_settings() -> Settings:
    return Settings()


settings = obtener_settings()
