"""Endpoint de salud del servicio (fuera del versionado `/api/v1`)."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["Salud"])


@router.get(
    "/health",
    summary="Verificar el estado del servicio",
    description=(
        "Comprueba que la API está en ejecución y que la conexión con la base de datos "
        "Oracle responde correctamente (`SELECT 1 FROM DUAL`)."
    ),
    responses={
        200: {
            "description": "El servicio y la base de datos están operativos.",
            "content": {
                "application/json": {"example": {"estado": "ok", "base_datos": "conectada"}}
            },
        },
        503: {
            "description": "El servicio está en ejecución pero no logra conectarse a la base de datos.",
            "content": {
                "application/json": {
                    "example": {
                        "error": 503,
                        "mensaje": "No fue posible conectar con la base de datos.",
                        "detalle": None,
                    }
                }
            },
        },
    },
)
def verificar_salud(db: Session = Depends(get_db)) -> JSONResponse:
    try:
        db.execute(text("SELECT 1 FROM DUAL"))
    except Exception:
        # Cualquier falla al intentar la consulta (error de Oracle, timeout de red,
        # resolución de host, etc.) se traduce como "base de datos no disponible".
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": status.HTTP_503_SERVICE_UNAVAILABLE,
                "mensaje": "No fue posible conectar con la base de datos.",
                "detalle": None,
            },
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"estado": "ok", "base_datos": "conectada"},
    )
