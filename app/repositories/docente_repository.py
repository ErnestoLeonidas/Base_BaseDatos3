"""Acceso a datos de Docente: todas las operaciones llaman a PKG_DOCENTE.

Las validaciones de negocio (RUT/email único, institución activa, existencia del
docente) viven en el paquete PL/SQL; este repositorio solo arma los parámetros,
invoca el procedimiento/función correspondiente y traduce el resultado a dicts.
"""

from typing import Any

import oracledb
from sqlalchemy.orm import Session

from app.db.oracle_calls import ejecutar, fila_como_dict, filas_como_dicts, obtener_cursor, var_number, var_str


class DocenteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def insertar(
        self,
        *,
        institucion_id: int,
        rut: str,
        nombres: str,
        apellido_paterno: str,
        apellido_materno: str,
        email: str,
        telefono: str | None,
        password_hash: str,
    ) -> int:
        def _llamar() -> int:
            cursor = obtener_cursor(self.db)
            p_id = cursor.var(oracledb.NUMBER)
            cursor.callproc(
                "PKG_DOCENTE.insertar",
                [
                    institucion_id,
                    rut,
                    nombres,
                    apellido_paterno,
                    apellido_materno,
                    email,
                    var_str(cursor, telefono, 20),
                    password_hash,
                    p_id,
                ],
            )
            return int(p_id.getvalue())

        return ejecutar(_llamar)

    def actualizar(
        self,
        docente_id: int,
        *,
        institucion_id: int | None,
        nombres: str | None,
        apellido_paterno: str | None,
        apellido_materno: str | None,
        email: str | None,
        telefono: str | None,
    ) -> None:
        def _llamar() -> None:
            cursor = obtener_cursor(self.db)
            cursor.callproc(
                "PKG_DOCENTE.actualizar",
                [
                    docente_id,
                    var_number(cursor, institucion_id),
                    var_str(cursor, nombres, 150),
                    var_str(cursor, apellido_paterno, 100),
                    var_str(cursor, apellido_materno, 100),
                    var_str(cursor, email, 150),
                    var_str(cursor, telefono, 20),
                ],
            )

        ejecutar(_llamar)

    def cambiar_estado(self, docente_id: int, estado: str) -> None:
        def _llamar() -> None:
            cursor = obtener_cursor(self.db)
            cursor.callproc("PKG_DOCENTE.cambiar_estado", [docente_id, estado])

        ejecutar(_llamar)

    def obtener_por_id(self, docente_id: int) -> dict[str, Any]:
        def _llamar() -> dict[str, Any]:
            cursor = obtener_cursor(self.db)
            out_cursor = cursor.var(oracledb.DB_TYPE_CURSOR)
            cursor.callproc("PKG_DOCENTE.obtener", [docente_id, out_cursor])
            return fila_como_dict(out_cursor.getvalue())

        return ejecutar(_llamar)

    def listar(
        self,
        *,
        institucion_id: int | None,
        estado: str | None,
        busqueda: str | None,
        page: int,
        size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        def _llamar() -> tuple[list[dict[str, Any]], int]:
            cursor = obtener_cursor(self.db)
            out_cursor = cursor.var(oracledb.DB_TYPE_CURSOR)
            p_total = cursor.var(oracledb.NUMBER)
            cursor.callproc(
                "PKG_DOCENTE.listar",
                [
                    var_number(cursor, institucion_id),
                    var_str(cursor, estado, 10),
                    var_str(cursor, busqueda, 200),
                    page,
                    size,
                    out_cursor,
                    p_total,
                ],
            )
            filas = filas_como_dicts(out_cursor.getvalue())
            return filas, int(p_total.getvalue())

        return ejecutar(_llamar)
