"""Utilidades para invocar paquetes PL/SQL desde una sesión de SQLAlchemy.

Las operaciones de Docente/Institución no se hacen con el ORM: se delegan a paquetes
PL/SQL (`PKG_INSTITUCION`, `PKG_DOCENTE`) que viven en la base de datos y que incluyen
ahí las validaciones de negocio (RUT/email único, institución activa, etc.), lanzando
`RAISE_APPLICATION_ERROR` con códigos `-200xx`. Este módulo traduce esos códigos a las
excepciones de dominio de `app.core.errors`.
"""

from collections.abc import Callable
from typing import Any, TypeVar

import oracledb
from sqlalchemy.orm import Session

from app.core.errors import (
    ConflictoError,
    ErrorDeAplicacion,
    RecursoNoEncontradoError,
    ValidacionNegocioError,
)

T = TypeVar("T")

# Mapa de código de error de aplicación Oracle (sin el signo) -> excepción de dominio.
_ERRORES_DE_NEGOCIO: dict[int, type[ErrorDeAplicacion]] = {
    20001: RecursoNoEncontradoError,  # institución no existe
    20002: ValidacionNegocioError,  # institución inactiva
    20003: ConflictoError,  # RUT duplicado
    20004: ConflictoError,  # email duplicado
    20005: RecursoNoEncontradoError,  # docente no existe
}


def obtener_cursor(db: Session) -> oracledb.Cursor:
    """Cursor oracledb nativo sobre la misma conexión/transacción que usa `db`.

    Así las llamadas a los paquetes participan de la misma transacción que el resto
    de la sesión (se confirman o revierten junto con `db.commit()` / `db.rollback()`).
    """
    return db.connection().connection.cursor()


def var_number(cursor: oracledb.Cursor, valor: int | None) -> oracledb.Var:
    """Variable de bind NUMBER, explícita para que un valor None no cambie el tipo."""
    variable = cursor.var(oracledb.NUMBER)
    variable.setvalue(0, valor)
    return variable


def var_str(cursor: oracledb.Cursor, valor: str | None, tamano: int = 4000) -> oracledb.Var:
    """Variable de bind VARCHAR2, explícita para que un valor None no cambie el tipo."""
    variable = cursor.var(oracledb.STRING, tamano)
    variable.setvalue(0, valor)
    return variable


def filas_como_dicts(cursor_resultado: oracledb.Cursor) -> list[dict[str, Any]]:
    """Convierte un SYS_REFCURSOR ya abierto en una lista de dicts con claves en minúscula."""
    columnas = [columna[0].lower() for columna in cursor_resultado.description]
    return [dict(zip(columnas, fila)) for fila in cursor_resultado]


def fila_como_dict(cursor_resultado: oracledb.Cursor) -> dict[str, Any] | None:
    """Convierte la primera fila de un SYS_REFCURSOR ya abierto en un dict, o None si está vacío."""
    columnas = [columna[0].lower() for columna in cursor_resultado.description]
    fila = cursor_resultado.fetchone()
    return dict(zip(columnas, fila)) if fila is not None else None


def ejecutar(funcion: Callable[[], T]) -> T:
    """Ejecuta `funcion` traduciendo los ORA-20xxx de los paquetes a excepciones de dominio.

    Cualquier otro error de Oracle (uno no esperado por la aplicación) se vuelve a
    lanzar tal cual, para que termine como un 500 genérico.
    """
    try:
        return funcion()
    except oracledb.DatabaseError as exc:
        oracle_error = exc.args[0]
        codigo = getattr(oracle_error, "code", None)
        clase_error = _ERRORES_DE_NEGOCIO.get(codigo)
        if clase_error is None:
            raise
        # El mensaje llega como "ORA-20003: Ya existe un docente...\nORA-06512: ...".
        mensaje = oracle_error.message.split("\n", 1)[0].split(": ", 1)[-1]
        raise clase_error(mensaje) from exc
