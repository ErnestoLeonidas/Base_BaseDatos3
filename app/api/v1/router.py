"""Router agregador de todos los endpoints versionados bajo `/api/v1`.

Cada etapa futura agrega su propio router y lo incluye aquí.
"""

from fastapi import APIRouter

from app.api.v1 import docentes, instituciones

api_router = APIRouter()
api_router.include_router(instituciones.router)
api_router.include_router(docentes.router)
