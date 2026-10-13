from fastapi.testclient import TestClient


def _payload(rut: str, email: str, institucion_id: int, **overrides) -> dict:
    datos = {
        "institucion_id": institucion_id,
        "rut": rut,
        "nombres": "Ana",
        "apellido_paterno": "Torres",
        "apellido_materno": "Lira",
        "email": email,
        "telefono": "+56911111111",
        "password": "Clave1234",
    }
    datos.update(overrides)
    return datos


def _email_para(rut: str) -> str:
    return f"docente{rut.replace('-', '')}@colegio.cl"


# --- Caso feliz ------------------------------------------------------------


def test_registrar_docente_caso_feliz(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    rut = generar_rut()
    respuesta = cliente.post(
        "/api/v1/docentes",
        json=_payload(rut, _email_para(rut), institucion_activa_id, nombres="  maría   josé  "),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["rut"] == rut
    assert cuerpo["nombres"] == "María José"
    assert cuerpo["email"] == _email_para(rut)
    assert cuerpo["estado"] == "ACTIVO"
    assert "password" not in cuerpo
    assert "password_hash" not in cuerpo
    assert "password" not in respuesta.text and "Clave1234" not in respuesta.text


# --- Errores de validación y de negocio ------------------------------------


def test_registrar_docente_rut_invalido(cliente: TestClient, institucion_activa_id) -> None:
    respuesta = cliente.post(
        "/api/v1/docentes",
        json=_payload("11111111-2", "correo-rut-invalido@colegio.cl", institucion_activa_id),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "validacion"


def test_registrar_docente_rut_duplicado(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    rut = generar_rut()
    primera = cliente.post("/api/v1/docentes", json=_payload(rut, _email_para(rut), institucion_activa_id))
    assert primera.status_code == 201

    segunda = cliente.post(
        "/api/v1/docentes", json=_payload(rut, "otro-correo@colegio.cl", institucion_activa_id)
    )
    assert segunda.status_code == 409
    assert "RUT" in segunda.json()["mensaje"]


def test_registrar_docente_email_duplicado(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    email_repetido = "repetido@colegio.cl"
    primera = cliente.post(
        "/api/v1/docentes", json=_payload(generar_rut(), email_repetido, institucion_activa_id)
    )
    assert primera.status_code == 201

    segunda = cliente.post(
        "/api/v1/docentes", json=_payload(generar_rut(), email_repetido, institucion_activa_id)
    )
    assert segunda.status_code == 409
    assert "correo" in segunda.json()["mensaje"]


def test_registrar_docente_institucion_inexistente(cliente: TestClient, generar_rut) -> None:
    rut = generar_rut()
    respuesta = cliente.post("/api/v1/docentes", json=_payload(rut, _email_para(rut), 999_999))

    assert respuesta.status_code == 404


def test_registrar_docente_password_debil(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    rut = generar_rut()
    respuesta = cliente.post(
        "/api/v1/docentes",
        json=_payload(rut, _email_para(rut), institucion_activa_id, password="abc"),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "validacion"


# --- Obtener / listar --------------------------------------------------------


def test_obtener_docente_no_existe(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/v1/docentes/999999")

    assert respuesta.status_code == 404


def test_obtener_docente_existente(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    rut = generar_rut()
    creado = cliente.post("/api/v1/docentes", json=_payload(rut, _email_para(rut), institucion_activa_id))
    docente_id = creado.json()["id"]

    respuesta = cliente.get(f"/api/v1/docentes/{docente_id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["rut"] == rut
    assert "password" not in respuesta.text


def test_listar_docentes_con_paginacion_y_filtro_institucion(
    cliente: TestClient, generar_rut, institucion_activa_id
) -> None:
    for _ in range(3):
        rut = generar_rut()
        cliente.post("/api/v1/docentes", json=_payload(rut, _email_para(rut), institucion_activa_id))

    respuesta = cliente.get(
        f"/api/v1/docentes?institucion_id={institucion_activa_id}&page=1&size=2"
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["page"] == 1
    assert cuerpo["size"] == 2
    assert len(cuerpo["items"]) == 2
    assert cuerpo["total"] >= 3
    assert cuerpo["pages"] >= 2
    assert "password" not in respuesta.text


def test_listar_docentes_busqueda_por_rut(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    rut = generar_rut()
    cliente.post("/api/v1/docentes", json=_payload(rut, _email_para(rut), institucion_activa_id))

    respuesta = cliente.get(f"/api/v1/docentes?busqueda={rut[:5]}")

    assert respuesta.status_code == 200
    ruts_encontrados = [item["rut"] for item in respuesta.json()["items"]]
    assert rut in ruts_encontrados


# --- Actualizar --------------------------------------------------------------


def test_actualizar_docente(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    rut = generar_rut()
    creado = cliente.post("/api/v1/docentes", json=_payload(rut, _email_para(rut), institucion_activa_id))
    docente_id = creado.json()["id"]

    respuesta = cliente.patch(
        f"/api/v1/docentes/{docente_id}",
        json={"telefono": "+56922223333", "apellido_materno": "  lira  gonzalez "},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["telefono"] == "+56922223333"
    assert cuerpo["apellido_materno"] == "Lira Gonzalez"
    assert cuerpo["rut"] == rut  # el RUT no cambia


def test_actualizar_docente_no_existe(cliente: TestClient) -> None:
    respuesta = cliente.patch("/api/v1/docentes/999999", json={"telefono": "+56900000000"})

    assert respuesta.status_code == 404


def test_actualizar_docente_email_duplicado(
    cliente: TestClient, generar_rut, institucion_activa_id
) -> None:
    rut_a = generar_rut()
    rut_b = generar_rut()
    cliente.post("/api/v1/docentes", json=_payload(rut_a, _email_para(rut_a), institucion_activa_id))
    creado_b = cliente.post(
        "/api/v1/docentes", json=_payload(rut_b, _email_para(rut_b), institucion_activa_id)
    )
    docente_b_id = creado_b.json()["id"]

    respuesta = cliente.patch(
        f"/api/v1/docentes/{docente_b_id}", json={"email": _email_para(rut_a)}
    )

    assert respuesta.status_code == 409


# --- Cambiar estado ------------------------------------------------------------


def test_cambiar_estado_docente(cliente: TestClient, generar_rut, institucion_activa_id) -> None:
    rut = generar_rut()
    creado = cliente.post("/api/v1/docentes", json=_payload(rut, _email_para(rut), institucion_activa_id))
    docente_id = creado.json()["id"]

    respuesta = cliente.patch(f"/api/v1/docentes/{docente_id}/estado", json={"estado": "INACTIVO"})

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "INACTIVO"


def test_cambiar_estado_docente_no_existe(cliente: TestClient) -> None:
    respuesta = cliente.patch("/api/v1/docentes/999999/estado", json={"estado": "INACTIVO"})

    assert respuesta.status_code == 404
