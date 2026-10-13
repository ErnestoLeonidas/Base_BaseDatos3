"""Endpoints de solo lectura de Institución."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.institucion_repository import InstitucionRepository
from app.schemas.institucion import InstitucionOut

router = APIRouter(prefix="/instituciones", tags=["Instituciones"])


@router.get(
    "",
    response_model=list[InstitucionOut],
    summary="Listar instituciones activas",
    description=(
        "Devuelve las instituciones activas, para poder elegir una al registrar un "
        "docente. Es un endpoint de solo lectura (las instituciones no se crean ni "
        "modifican en esta etapa)."
    ),
)
def listar_instituciones(db: Session = Depends(get_db)) -> list[InstitucionOut]:
    repositorio = InstitucionRepository(db)
    return [InstitucionOut.model_validate(i) for i in repositorio.listar_activas()]
