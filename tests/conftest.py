from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.rut import calcular_digito_verificador
from app.db.session import engine, get_db
from app.main import app
from app.models.institucion import Institucion


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Sesión envuelta en una transacción externa que se revierte al final del test.

    Así cada test puede insertar datos (docentes, etc.) usando el Oracle real de
    Docker Compose sin dejar residuos entre ejecuciones de la suite.
    """
    connection = engine.connect()
    transaccion_externa = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _reiniciar_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaccion_externa.rollback()
        connection.close()


@pytest.fixture()
def cliente(db_session: Session) -> Generator[TestClient, None, None]:
    def _get_db_de_prueba() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _get_db_de_prueba
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def generar_rut():
    """Genera RUTs válidos (dígito verificador correcto) y distintos entre sí."""
    contador = {"valor": 20_000_000}

    def _generar() -> str:
        contador["valor"] += 1
        cuerpo = contador["valor"]
        verificador = calcular_digito_verificador(cuerpo)
        return f"{cuerpo}-{verificador}"

    return _generar


@pytest.fixture()
def institucion_activa_id(db_session: Session) -> int:
    """Id de una institución activa ya sembrada (seed de la migración 0002)."""
    institucion = db_session.scalars(
        select(Institucion).where(Institucion.activa == True)  # noqa: E712
    ).first()
    assert institucion is not None, "No hay instituciones activas sembradas."
    return institucion.id
