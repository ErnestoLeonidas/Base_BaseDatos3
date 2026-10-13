"""crea INSTITUCION y DOCENTE, con seed de 2 instituciones de ejemplo

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-12 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "INSTITUCION",
        sa.Column("ID", sa.Integer, sa.Identity(always=True), nullable=False),
        sa.Column("NOMBRE", sa.String(200), nullable=False),
        sa.Column("RBD", sa.String(20), nullable=False),
        sa.Column("COMUNA", sa.String(100), nullable=False),
        sa.Column("ACTIVA", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "FECHA_CREACION",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("SYSTIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("ID", name="PK_INSTITUCION"),
        sa.UniqueConstraint("RBD", name="UK_INSTITUCION_RBD"),
        sa.CheckConstraint("ACTIVA IN (0,1)", name="CK_INSTITUCION_ACTIVA"),
    )

    op.create_table(
        "DOCENTE",
        sa.Column("ID", sa.Integer, sa.Identity(always=True), nullable=False),
        sa.Column("INSTITUCION_ID", sa.Integer, nullable=False),
        sa.Column("RUT", sa.String(12), nullable=False),
        sa.Column("NOMBRES", sa.String(150), nullable=False),
        sa.Column("APELLIDO_PATERNO", sa.String(100), nullable=False),
        sa.Column("APELLIDO_MATERNO", sa.String(100), nullable=False),
        sa.Column("EMAIL", sa.String(150), nullable=False),
        sa.Column("TELEFONO", sa.String(20), nullable=True),
        sa.Column("PASSWORD_HASH", sa.String(255), nullable=False),
        sa.Column("ESTADO", sa.String(10), nullable=False, server_default="ACTIVO"),
        sa.Column(
            "FECHA_CREACION",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("SYSTIMESTAMP"),
        ),
        sa.Column(
            "FECHA_ACTUALIZACION",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("SYSTIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("ID", name="PK_DOCENTE"),
        sa.UniqueConstraint("RUT", name="UK_DOCENTE_RUT"),
        sa.UniqueConstraint("EMAIL", name="UK_DOCENTE_EMAIL"),
        sa.ForeignKeyConstraint(
            ["INSTITUCION_ID"], ["INSTITUCION.ID"], name="FK_DOCENTE_INSTITUCION"
        ),
        sa.CheckConstraint("ESTADO IN ('ACTIVO','INACTIVO')", name="CK_DOCENTE_ESTADO"),
    )
    op.create_index("IX_DOCENTE_INSTITUCION_ID", "DOCENTE", ["INSTITUCION_ID"])

    instituciones = sa.table(
        "INSTITUCION",
        sa.column("NOMBRE", sa.String),
        sa.column("RBD", sa.String),
        sa.column("COMUNA", sa.String),
        sa.column("ACTIVA", sa.Integer),
    )
    op.bulk_insert(
        instituciones,
        [
            {
                "NOMBRE": "Liceo Demo Uno",
                "RBD": "00001-1",
                "COMUNA": "Santiago",
                "ACTIVA": 1,
            },
            {
                "NOMBRE": "Colegio Demo Dos",
                "RBD": "00002-2",
                "COMUNA": "Valparaíso",
                "ACTIVA": 1,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("IX_DOCENTE_INSTITUCION_ID", table_name="DOCENTE")
    op.drop_table("DOCENTE")
    op.drop_table("INSTITUCION")
