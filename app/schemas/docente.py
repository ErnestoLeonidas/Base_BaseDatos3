"""Schemas de Docente: request (creación/actualización) y response."""

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.rut import normalizar_rut

_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PATRON_PASSWORD = re.compile(r"^(?=.*[A-Za-zÁÉÍÓÚÑáéíóúñ])(?=.*\d).{8,}$")


class EstadoDocente(StrEnum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


def _normalizar_nombre(valor: str) -> str:
    return " ".join(valor.strip().split()).title()


def _validar_email(valor: str) -> str:
    valor = valor.strip().lower()
    if not _PATRON_EMAIL.match(valor):
        raise ValueError("El formato del correo electrónico no es válido.")
    return valor


class DocenteCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institucion_id": 1,
                "rut": "12.345.678-5",
                "nombres": "María José",
                "apellido_paterno": "Pérez",
                "apellido_materno": "Soto",
                "email": "maria.perez@colegio.cl",
                "telefono": "+56912345678",
                "password": "Clave1234",
            }
        }
    )

    institucion_id: int = Field(..., description="Id de la institución a la que pertenece el docente.")
    rut: str = Field(..., description="RUT chileno, con o sin puntos, con guion.")
    nombres: str = Field(..., min_length=2, max_length=150)
    apellido_paterno: str = Field(..., min_length=2, max_length=100)
    apellido_materno: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=150)
    telefono: str | None = Field(default=None, max_length=20)
    password: str = Field(..., description="Mínimo 8 caracteres, con al menos una letra y un número.")

    @field_validator("rut")
    @classmethod
    def _validar_rut(cls, valor: str) -> str:
        return normalizar_rut(valor)

    @field_validator("nombres", "apellido_paterno", "apellido_materno")
    @classmethod
    def _normalizar_nombres(cls, valor: str) -> str:
        return _normalizar_nombre(valor)

    @field_validator("email")
    @classmethod
    def _validar_formato_email(cls, valor: str) -> str:
        return _validar_email(valor)

    @field_validator("password")
    @classmethod
    def _validar_password(cls, valor: str) -> str:
        if not _PATRON_PASSWORD.match(valor):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, incluyendo al menos una "
                "letra y un número."
            )
        return valor


class DocenteUpdate(BaseModel):
    """Actualización parcial de datos del docente (no incluye la contraseña)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "telefono": "+56987654321",
                "email": "maria.perez.nueva@colegio.cl",
            }
        }
    )

    institucion_id: int | None = None
    nombres: str | None = Field(default=None, min_length=2, max_length=150)
    apellido_paterno: str | None = Field(default=None, min_length=2, max_length=100)
    apellido_materno: str | None = Field(default=None, min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=150)
    telefono: str | None = Field(default=None, max_length=20)

    @field_validator("nombres", "apellido_paterno", "apellido_materno")
    @classmethod
    def _normalizar_nombres(cls, valor: str | None) -> str | None:
        return _normalizar_nombre(valor) if valor is not None else None

    @field_validator("email")
    @classmethod
    def _validar_formato_email(cls, valor: str | None) -> str | None:
        return _validar_email(valor) if valor is not None else None


class DocenteEstadoUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"estado": "INACTIVO"}})

    estado: EstadoDocente = Field(..., description="Nuevo estado del docente.")


class DocenteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institucion_id: int
    rut: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str
    email: str
    telefono: str | None
    estado: EstadoDocente
    fecha_creacion: datetime
    fecha_actualizacion: datetime


class PaginaDocentes(BaseModel):
    items: list[DocenteOut]
    total: int = Field(description="Cantidad total de docentes que cumplen el filtro.")
    page: int
    size: int
    pages: int = Field(description="Cantidad total de páginas.")
