from fastapi.testclient import TestClient


def test_lista_instituciones_activas(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/instituciones")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert isinstance(cuerpo, list)
    assert len(cuerpo) >= 2
    assert all(institucion["activa"] is True for institucion in cuerpo)
    assert all({"id", "nombre", "rbd", "comuna"} <= institucion.keys() for institucion in cuerpo)
