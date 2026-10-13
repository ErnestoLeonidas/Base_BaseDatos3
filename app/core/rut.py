"""Validación y normalización de RUT chileno (dígito verificador módulo 11).

Utilidad genérica (no específica de docentes) para que otras etapas que también
manejen RUT (p. ej. estudiantes) puedan reutilizarla.
"""

import re

_CARACTERES_VALIDOS = re.compile(r"[^0-9kK]")


def calcular_digito_verificador(cuerpo: int) -> str:
    """Calcula el dígito verificador (módulo 11) para el cuerpo numérico de un RUT."""
    suma = 0
    multiplicador = 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def normalizar_rut(rut_crudo: str) -> str:
    """Valida un RUT (con o sin puntos/guion) y lo normaliza a formato "12345678-9".

    Lanza ValueError con un mensaje en español si el RUT no es válido.
    """
    limpio = _CARACTERES_VALIDOS.sub("", rut_crudo).upper()
    if len(limpio) < 2:
        raise ValueError("El RUT ingresado no es válido.")

    cuerpo, verificador = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit():
        raise ValueError("El RUT ingresado no es válido.")

    cuerpo_int = int(cuerpo)
    if calcular_digito_verificador(cuerpo_int) != verificador:
        raise ValueError("El RUT ingresado no es válido (el dígito verificador no corresponde).")

    return f"{cuerpo_int}-{verificador}"
