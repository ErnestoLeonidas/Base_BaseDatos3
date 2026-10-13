"""Manejo de errores uniforme: excepciones de dominio y su traducción a JSON.

Toda respuesta de error de la API sigue el mismo sobre (envelope):

    { "error": <codigo>, "mensaje": <texto>, "detalle": <opcional> }

Las etapas futuras (docentes, cursos, evaluaciones, etc.) deben lanzar las
excepciones de dominio definidas aquí (o subclases de `ErrorDeAplicacion`) en
lugar de construir respuestas HTTP a mano.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class ErrorDeAplicacion(Exception):
    """Excepción base para errores de negocio controlados de EvalAI."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    codigo: str = "error_aplicacion"

    def __init__(self, mensaje: str, detalle: Any = None) -> None:
        self.mensaje = mensaje
        self.detalle = detalle
        super().__init__(mensaje)


class RecursoNoEncontradoError(ErrorDeAplicacion):
    """El recurso solicitado no existe. Se traduce a HTTP 404."""

    status_code = status.HTTP_404_NOT_FOUND
    codigo = "recurso_no_encontrado"


class ConflictoError(ErrorDeAplicacion):
    """El recurso ya existe o entra en conflicto con el estado actual. Se traduce a HTTP 409."""

    status_code = status.HTTP_409_CONFLICT
    codigo = "conflicto"


class ValidacionNegocioError(ErrorDeAplicacion):
    """Una regla de negocio (no de forma) no se cumple. Se traduce a HTTP 422."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    codigo = "validacion"


def _envelope(codigo: Any, mensaje: str, detalle: Any = None) -> dict[str, Any]:
    return {"error": codigo, "mensaje": mensaje, "detalle": detalle}


# Traducción al español de los tipos de error más comunes que genera Pydantic v2.
_MENSAJES_POR_TIPO: dict[str, str] = {
    "missing": "Este campo es obligatorio.",
    "string_too_short": "El valor ingresado es demasiado corto.",
    "string_too_long": "El valor ingresado es demasiado largo.",
    "string_type": "Debe ser un texto.",
    "value_error": "El valor ingresado no es válido.",
    "int_parsing": "Debe ser un número entero.",
    "int_type": "Debe ser un número entero.",
    "float_parsing": "Debe ser un número.",
    "bool_parsing": "Debe ser un valor booleano (verdadero/falso).",
    "greater_than_equal": "El valor debe ser mayor o igual al mínimo permitido.",
    "less_than_equal": "El valor debe ser menor o igual al máximo permitido.",
    "enum": "El valor no está entre las opciones permitidas.",
    "extra_forbidden": "No se permiten campos adicionales.",
    "json_invalid": "El cuerpo de la solicitud no es un JSON válido.",
}


def _traducir_errores_validacion(errores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    traducidos = []
    for err in errores:
        tipo = err.get("type", "")
        msg_original = err.get("msg", "Valor inválido.")
        if tipo == "value_error" and msg_original.startswith("Value error, "):
            # Mensaje de un validador propio (ya en español): se usa tal cual, sin
            # el prefijo en inglés que agrega Pydantic.
            mensaje = msg_original.removeprefix("Value error, ")
        else:
            mensaje = _MENSAJES_POR_TIPO.get(tipo, msg_original)
        campo = ".".join(str(parte) for parte in err.get("loc", []) if parte != "body")
        traducidos.append({"campo": campo, "mensaje": mensaje})
    return traducidos


def registrar_manejadores_de_errores(app: FastAPI) -> None:
    """Registra en `app` los manejadores que producen el envelope uniforme de error."""

    @app.exception_handler(ErrorDeAplicacion)
    async def _manejar_error_aplicacion(request: Request, exc: ErrorDeAplicacion) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.codigo, exc.mensaje, exc.detalle),
        )

    @app.exception_handler(RequestValidationError)
    async def _manejar_error_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
        detalle = _traducir_errores_validacion(jsonable_encoder(exc.errors()))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("validacion", "Los datos enviados no son válidos.", detalle),
        )

    # Se registra sobre la HTTPException de Starlette (no la de FastAPI): rutas no
    # encontradas o métodos no permitidos las levanta el framework usando esa clase base.
    @app.exception_handler(HTTPException)
    async def _manejar_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.status_code, str(exc.detail), None),
        )

    @app.exception_handler(Exception)
    async def _manejar_error_inesperado(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Ocurrió un error interno inesperado.",
                None,
            ),
        )
