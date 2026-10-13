"""Punto de entrada de la API de EvalAI."""

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.errors import registrar_manejadores_de_errores

app = FastAPI(
    title="EvalAI — API Colegio",
    description=(
        "API para EvalAI, la plataforma que permite a docentes de colegios chilenos "
        "generar, aplicar y corregir evaluaciones alineadas a Objetivos de Aprendizaje "
        "(OA), con preguntas generadas por IA, corrección por fotografía y reportes de "
        "logro por indicador."
    ),
    version="0.1.0",
    # Se mantiene debug=False (por defecto) para que los errores no controlados
    # siempre respondan con el envelope JSON uniforme, incluso en desarrollo.
    contact={"name": "Equipo EvalAI"},
)

registrar_manejadores_de_errores(app)

app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
