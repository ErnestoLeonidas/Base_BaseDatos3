"""baseline: inicializa la cadena de migraciones (sin cambios de esquema)

Revision ID: 0001
Revises:
Create Date: 2026-10-12 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migración inicial vacía: solo deja la cadena de Alembic lista sobre Oracle."""
    pass


def downgrade() -> None:
    """Migración inicial vacía: no hay nada que revertir."""
    pass
