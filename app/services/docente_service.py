"""Orquestación del registro de docentes.

Las reglas de negocio (RUT/email único, institución activa, existencia) viven en el
paquete PL/SQL `PKG_DOCENTE` (ver `app/repositories/docente_repository.py`); este
service solo se encarga de lo que no puede vivir en la base de datos (el hash de la
contraseña con Argon2) y de armar las respuestas.
"""

import math

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.docente_repository import DocenteRepository
from app.schemas.docente import (
    DocenteCreate,
    DocenteOut,
    DocenteUpdate,
    EstadoDocente,
    PaginaDocentes,
)


class DocenteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.docentes = DocenteRepository(db)

    def registrar(self, datos: DocenteCreate) -> DocenteOut:
        nuevo_id = self.docentes.insertar(
            institucion_id=datos.institucion_id,
            rut=datos.rut,
            nombres=datos.nombres,
            apellido_paterno=datos.apellido_paterno,
            apellido_materno=datos.apellido_materno,
            email=datos.email,
            telefono=datos.telefono,
            password_hash=hash_password(datos.password),
        )
        self.db.commit()
        return DocenteOut.model_validate(self.docentes.obtener_por_id(nuevo_id))

    def obtener(self, docente_id: int) -> DocenteOut:
        return DocenteOut.model_validate(self.docentes.obtener_por_id(docente_id))

    def listar(
        self,
        *,
        institucion_id: int | None,
        estado: EstadoDocente | None,
        busqueda: str | None,
        page: int,
        size: int,
    ) -> PaginaDocentes:
        filas, total = self.docentes.listar(
            institucion_id=institucion_id,
            estado=estado.value if estado else None,
            busqueda=busqueda,
            page=page,
            size=size,
        )
        total_paginas = math.ceil(total / size) if total else 0
        return PaginaDocentes(
            items=[DocenteOut.model_validate(fila) for fila in filas],
            total=total,
            page=page,
            size=size,
            pages=total_paginas,
        )

    def actualizar(self, docente_id: int, datos: DocenteUpdate) -> DocenteOut:
        self.docentes.actualizar(
            docente_id,
            institucion_id=datos.institucion_id,
            nombres=datos.nombres,
            apellido_paterno=datos.apellido_paterno,
            apellido_materno=datos.apellido_materno,
            email=datos.email,
            telefono=datos.telefono,
        )
        self.db.commit()
        return DocenteOut.model_validate(self.docentes.obtener_por_id(docente_id))

    def cambiar_estado(self, docente_id: int, estado: EstadoDocente) -> DocenteOut:
        self.docentes.cambiar_estado(docente_id, estado.value)
        self.db.commit()
        return DocenteOut.model_validate(self.docentes.obtener_por_id(docente_id))
