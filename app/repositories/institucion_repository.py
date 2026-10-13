"""Acceso a datos de Institución: llama a PKG_INSTITUCION (solo lectura en esta etapa)."""

from typing import Any

import oracledb
from sqlalchemy.orm import Session

from app.db.oracle_calls import ejecutar, filas_como_dicts, obtener_cursor


class InstitucionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar_activas(self) -> list[dict[str, Any]]:
        def _llamar() -> list[dict[str, Any]]:
            cursor = obtener_cursor(self.db)
            out_cursor = cursor.var(oracledb.DB_TYPE_CURSOR)
            cursor.callproc("PKG_INSTITUCION.listar_activas", [out_cursor])
            return filas_como_dicts(out_cursor.getvalue())

        return ejecutar(_llamar)
