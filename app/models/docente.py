"""Modelo ORM de la tabla DOCENTE."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.institucion import Institucion


class Docente(Base):
    __tablename__ = "DOCENTE"

    id: Mapped[int] = mapped_column("ID", sa.Integer, primary_key=True)
    institucion_id: Mapped[int] = mapped_column(
        "INSTITUCION_ID",
        sa.Integer,
        sa.ForeignKey("INSTITUCION.ID", name="FK_DOCENTE_INSTITUCION"),
        nullable=False,
    )
    rut: Mapped[str] = mapped_column("RUT", sa.String(12), nullable=False, unique=True)
    nombres: Mapped[str] = mapped_column("NOMBRES", sa.String(150), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column("APELLIDO_PATERNO", sa.String(100), nullable=False)
    apellido_materno: Mapped[str] = mapped_column("APELLIDO_MATERNO", sa.String(100), nullable=False)
    email: Mapped[str] = mapped_column("EMAIL", sa.String(150), nullable=False, unique=True)
    telefono: Mapped[str | None] = mapped_column("TELEFONO", sa.String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column("PASSWORD_HASH", sa.String(255), nullable=False)
    estado: Mapped[str] = mapped_column("ESTADO", sa.String(10), nullable=False, default="ACTIVO")
    fecha_creacion: Mapped[datetime] = mapped_column(
        "FECHA_CREACION", sa.TIMESTAMP(timezone=True), nullable=False
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        "FECHA_ACTUALIZACION", sa.TIMESTAMP(timezone=True), nullable=False
    )

    institucion: Mapped[Institucion] = relationship()
