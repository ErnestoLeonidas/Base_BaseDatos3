"""Schemas de Institución (solo lectura en esta etapa)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InstitucionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    nombre: str = Field(examples=["Liceo Demo Uno"])
    rbd: str = Field(examples=["00001-1"])
    comuna: str = Field(examples=["Santiago"])
    activa: bool = Field(examples=[True])
    fecha_creacion: datetime
