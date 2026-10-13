"""Endpoints de registro y gestión de Docentes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.docente import (
    DocenteCreate,
    DocenteEstadoUpdate,
    DocenteOut,
    DocenteUpdate,
    EstadoDocente,
    PaginaDocentes,
)
from app.services.docente_service import DocenteService

router = APIRouter(prefix="/docentes", tags=["Docentes"])


@router.post(
    "",
    response_model=DocenteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un docente",
    description=(
        "Crea un nuevo docente. El RUT se valida (dígito verificador módulo 11) y se "
        "normaliza al formato `12345678-5`; el correo se guarda en minúsculas; la "
        "contraseña se almacena únicamente como hash (Argon2) y nunca se devuelve en "
        "ninguna respuesta."
    ),
    responses={
        404: {"description": "La institución indicada no existe."},
        409: {"description": "El RUT o el correo ya están registrados."},
        422: {"description": "RUT inválido, correo con formato inválido o contraseña débil."},
    },
)
def registrar_docente(datos: DocenteCreate, db: Session = Depends(get_db)) -> DocenteOut:
    servicio = DocenteService(db)
    return servicio.registrar(datos)


@router.get(
    "",
    response_model=PaginaDocentes,
    summary="Listar docentes",
    description=(
        "Lista paginada de docentes, con filtros opcionales por institución, estado y "
        "búsqueda por nombre, apellido o RUT."
    ),
)
def listar_docentes(
    institucion_id: int | None = Query(default=None, description="Filtra por id de institución."),
    estado: EstadoDocente | None = Query(default=None, description="Filtra por estado."),
    busqueda: str | None = Query(
        default=None, description="Busca por nombre, apellido o RUT (coincidencia parcial)."
    ),
    page: int = Query(default=1, ge=1, description="Número de página, comienza en 1."),
    size: int = Query(default=20, ge=1, le=100, description="Resultados por página (máximo 100)."),
    db: Session = Depends(get_db),
) -> PaginaDocentes:
    servicio = DocenteService(db)
    return servicio.listar(
        institucion_id=institucion_id,
        estado=estado,
        busqueda=busqueda,
        page=page,
        size=size,
    )


@router.get(
    "/{docente_id}",
    response_model=DocenteOut,
    summary="Obtener un docente",
    description="Obtiene los datos de un docente por su id.",
    responses={404: {"description": "El docente no existe."}},
)
def obtener_docente(docente_id: int, db: Session = Depends(get_db)) -> DocenteOut:
    servicio = DocenteService(db)
    return servicio.obtener(docente_id)


@router.patch(
    "/{docente_id}",
    response_model=DocenteOut,
    summary="Actualizar datos de un docente",
    description=(
        "Actualiza los datos de un docente (nombres, apellidos, correo, teléfono o "
        "institución). No permite cambiar la contraseña ni el RUT."
    ),
    responses={
        404: {"description": "El docente, o la institución indicada, no existe."},
        409: {"description": "El correo ya está registrado por otro docente."},
    },
)
def actualizar_docente(
    docente_id: int, datos: DocenteUpdate, db: Session = Depends(get_db)
) -> DocenteOut:
    servicio = DocenteService(db)
    return servicio.actualizar(docente_id, datos)


@router.patch(
    "/{docente_id}/estado",
    response_model=DocenteOut,
    summary="Activar o desactivar un docente",
    description=(
        "Cambia el estado del docente entre ACTIVO e INACTIVO. Es una eliminación "
        "lógica: el registro nunca se borra físicamente."
    ),
    responses={404: {"description": "El docente no existe."}},
)
def cambiar_estado_docente(
    docente_id: int, datos: DocenteEstadoUpdate, db: Session = Depends(get_db)
) -> DocenteOut:
    servicio = DocenteService(db)
    return servicio.cambiar_estado(docente_id, datos.estado)
