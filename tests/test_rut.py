import pytest

from app.core.rut import calcular_digito_verificador, normalizar_rut


def test_normaliza_rut_con_puntos_y_guion() -> None:
    assert normalizar_rut("12.345.678-5") == "12345678-5"


def test_normaliza_rut_sin_puntos() -> None:
    assert normalizar_rut("12345678-5") == "12345678-5"


def test_normaliza_rut_con_dv_k_en_minuscula() -> None:
    cuerpo = 15500001
    dv = calcular_digito_verificador(cuerpo)
    assert normalizar_rut(f"{cuerpo}-{dv.lower()}") == f"{cuerpo}-{dv}"


def test_rechaza_rut_con_digito_verificador_incorrecto() -> None:
    with pytest.raises(ValueError):
        normalizar_rut("11111111-2")


def test_rechaza_rut_con_formato_invalido() -> None:
    with pytest.raises(ValueError):
        normalizar_rut("no-es-un-rut")
