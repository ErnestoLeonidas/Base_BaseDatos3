"""Modelo ORM de la tabla INSTITUCION."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Institucion(Base):
    __tablename__ = "INSTITUCION"

    id: Mapped[int] = mapped_column("ID", sa.Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column("NOMBRE", sa.String(200), nullable=False)
    rbd: Mapped[str] = mapped_column("RBD", sa.String(20), nullable=False, unique=True)
    comuna: Mapped[str] = mapped_column("COMUNA", sa.String(100), nullable=False)
    activa: Mapped[bool] = mapped_column("ACTIVA", sa.Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        "FECHA_CREACION", sa.TIMESTAMP(timezone=True), nullable=False
    )
