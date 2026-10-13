"""crea paquetes PL/SQL PKG_INSTITUCION y PKG_DOCENTE

El acceso a datos de Institucion/Docente se hace desde la API a traves de estos
paquetes (no con SQL generado por el ORM). Las validaciones de negocio (RUT/email
unico, institucion activa, existencia del docente) viven aqui y se reportan con
RAISE_APPLICATION_ERROR usando codigos -20001..-20005, que la API traduce a
404/409/422 (ver app/db/oracle_calls.py).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-12 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _verificar_compilacion(nombre: str, tipo: str) -> None:
    """Lanza un error si CREATE OR REPLACE dejo el objeto PL/SQL en estado INVALID.

    Oracle no falla la sentencia DDL por errores de compilacion: el objeto queda
    INVALID y el detalle se consulta aparte en USER_ERRORS.
    """
    conn = op.get_bind()
    errores = conn.execute(
        sa.text(
            "SELECT LINE, POSITION, TEXT FROM USER_ERRORS "
            "WHERE NAME = :nombre AND TYPE = :tipo ORDER BY SEQUENCE"
        ),
        {"nombre": nombre, "tipo": tipo},
    ).fetchall()
    if errores:
        detalle = "\n".join(f"  L{fila[0]}:{fila[1]} {fila[2]}" for fila in errores)
        raise RuntimeError(f"Errores de compilación en {tipo} {nombre}:\n{detalle}")


_PKG_INSTITUCION_SPEC = """
CREATE OR REPLACE PACKAGE PKG_INSTITUCION AS
    PROCEDURE listar_activas(p_cursor OUT SYS_REFCURSOR);
    FUNCTION esta_activa(p_id IN NUMBER) RETURN NUMBER;
END PKG_INSTITUCION;
"""

_PKG_INSTITUCION_BODY = """
CREATE OR REPLACE PACKAGE BODY PKG_INSTITUCION AS

    PROCEDURE listar_activas(p_cursor OUT SYS_REFCURSOR) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT ID, NOMBRE, RBD, COMUNA, ACTIVA, FECHA_CREACION
            FROM INSTITUCION
            WHERE ACTIVA = 1
            ORDER BY NOMBRE;
    END listar_activas;

    -- Devuelve 1/0 segun ACTIVA, o -1 si el id no existe.
    FUNCTION esta_activa(p_id IN NUMBER) RETURN NUMBER IS
        v_activa NUMBER;
    BEGIN
        SELECT ACTIVA INTO v_activa FROM INSTITUCION WHERE ID = p_id;
        RETURN v_activa;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN -1;
    END esta_activa;

END PKG_INSTITUCION;
"""

_PKG_DOCENTE_SPEC = """
CREATE OR REPLACE PACKAGE PKG_DOCENTE AS

    PROCEDURE insertar(
        p_institucion_id   IN  NUMBER,
        p_rut              IN  VARCHAR2,
        p_nombres          IN  VARCHAR2,
        p_apellido_paterno IN  VARCHAR2,
        p_apellido_materno IN  VARCHAR2,
        p_email            IN  VARCHAR2,
        p_telefono         IN  VARCHAR2,
        p_password_hash    IN  VARCHAR2,
        p_id               OUT NUMBER
    );

    -- Los parametros NULL significan "no cambiar ese campo" (actualizacion parcial).
    PROCEDURE actualizar(
        p_id               IN NUMBER,
        p_institucion_id   IN NUMBER,
        p_nombres          IN VARCHAR2,
        p_apellido_paterno IN VARCHAR2,
        p_apellido_materno IN VARCHAR2,
        p_email            IN VARCHAR2,
        p_telefono         IN VARCHAR2
    );

    PROCEDURE cambiar_estado(p_id IN NUMBER, p_estado IN VARCHAR2);

    PROCEDURE obtener(p_id IN NUMBER, p_cursor OUT SYS_REFCURSOR);

    PROCEDURE listar(
        p_institucion_id IN NUMBER,
        p_estado         IN VARCHAR2,
        p_busqueda       IN VARCHAR2,
        p_page           IN NUMBER,
        p_size           IN NUMBER,
        p_cursor         OUT SYS_REFCURSOR,
        p_total          OUT NUMBER
    );

END PKG_DOCENTE;
"""

_PKG_DOCENTE_BODY = """
CREATE OR REPLACE PACKAGE BODY PKG_DOCENTE AS

    PROCEDURE insertar(
        p_institucion_id   IN  NUMBER,
        p_rut              IN  VARCHAR2,
        p_nombres          IN  VARCHAR2,
        p_apellido_paterno IN  VARCHAR2,
        p_apellido_materno IN  VARCHAR2,
        p_email            IN  VARCHAR2,
        p_telefono         IN  VARCHAR2,
        p_password_hash    IN  VARCHAR2,
        p_id               OUT NUMBER
    ) IS
        v_existe NUMBER;
        v_activa NUMBER;
    BEGIN
        v_activa := PKG_INSTITUCION.esta_activa(p_institucion_id);
        IF v_activa = -1 THEN
            RAISE_APPLICATION_ERROR(-20001, 'No existe una institucion con id ' || p_institucion_id || '.');
        ELSIF v_activa = 0 THEN
            RAISE_APPLICATION_ERROR(-20002, 'La institucion seleccionada no esta activa.');
        END IF;

        SELECT COUNT(*) INTO v_existe FROM DOCENTE WHERE RUT = p_rut;
        IF v_existe > 0 THEN
            RAISE_APPLICATION_ERROR(-20003, 'Ya existe un docente registrado con el RUT ' || p_rut || '.');
        END IF;

        SELECT COUNT(*) INTO v_existe FROM DOCENTE WHERE EMAIL = p_email;
        IF v_existe > 0 THEN
            RAISE_APPLICATION_ERROR(-20004, 'Ya existe un docente registrado con el correo ' || p_email || '.');
        END IF;

        INSERT INTO DOCENTE (
            INSTITUCION_ID, RUT, NOMBRES, APELLIDO_PATERNO, APELLIDO_MATERNO,
            EMAIL, TELEFONO, PASSWORD_HASH, ESTADO, FECHA_CREACION, FECHA_ACTUALIZACION
        ) VALUES (
            p_institucion_id, p_rut, p_nombres, p_apellido_paterno, p_apellido_materno,
            p_email, p_telefono, p_password_hash, 'ACTIVO', SYSTIMESTAMP, SYSTIMESTAMP
        )
        RETURNING ID INTO p_id;
    END insertar;


    PROCEDURE actualizar(
        p_id               IN NUMBER,
        p_institucion_id   IN NUMBER,
        p_nombres          IN VARCHAR2,
        p_apellido_paterno IN VARCHAR2,
        p_apellido_materno IN VARCHAR2,
        p_email            IN VARCHAR2,
        p_telefono         IN VARCHAR2
    ) IS
        v_existe NUMBER;
        v_activa NUMBER;
        v_actual DOCENTE%ROWTYPE;
    BEGIN
        SELECT * INTO v_actual FROM DOCENTE WHERE ID = p_id;

        IF p_institucion_id IS NOT NULL AND p_institucion_id != v_actual.INSTITUCION_ID THEN
            v_activa := PKG_INSTITUCION.esta_activa(p_institucion_id);
            IF v_activa = -1 THEN
                RAISE_APPLICATION_ERROR(-20001, 'No existe una institucion con id ' || p_institucion_id || '.');
            ELSIF v_activa = 0 THEN
                RAISE_APPLICATION_ERROR(-20002, 'La institucion seleccionada no esta activa.');
            END IF;
        END IF;

        IF p_email IS NOT NULL AND p_email != v_actual.EMAIL THEN
            SELECT COUNT(*) INTO v_existe FROM DOCENTE WHERE EMAIL = p_email AND ID != p_id;
            IF v_existe > 0 THEN
                RAISE_APPLICATION_ERROR(-20004, 'Ya existe un docente registrado con el correo ' || p_email || '.');
            END IF;
        END IF;

        UPDATE DOCENTE
        SET INSTITUCION_ID      = COALESCE(p_institucion_id, INSTITUCION_ID),
            NOMBRES             = COALESCE(p_nombres, NOMBRES),
            APELLIDO_PATERNO    = COALESCE(p_apellido_paterno, APELLIDO_PATERNO),
            APELLIDO_MATERNO    = COALESCE(p_apellido_materno, APELLIDO_MATERNO),
            EMAIL               = COALESCE(p_email, EMAIL),
            TELEFONO            = COALESCE(p_telefono, TELEFONO),
            FECHA_ACTUALIZACION = SYSTIMESTAMP
        WHERE ID = p_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20005, 'No existe un docente con id ' || p_id || '.');
    END actualizar;


    PROCEDURE cambiar_estado(p_id IN NUMBER, p_estado IN VARCHAR2) IS
    BEGIN
        UPDATE DOCENTE
        SET ESTADO = p_estado,
            FECHA_ACTUALIZACION = SYSTIMESTAMP
        WHERE ID = p_id;

        IF SQL%ROWCOUNT = 0 THEN
            RAISE_APPLICATION_ERROR(-20005, 'No existe un docente con id ' || p_id || '.');
        END IF;
    END cambiar_estado;


    PROCEDURE obtener(p_id IN NUMBER, p_cursor OUT SYS_REFCURSOR) IS
        v_existe NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_existe FROM DOCENTE WHERE ID = p_id;
        IF v_existe = 0 THEN
            RAISE_APPLICATION_ERROR(-20005, 'No existe un docente con id ' || p_id || '.');
        END IF;

        OPEN p_cursor FOR
            SELECT ID, INSTITUCION_ID, RUT, NOMBRES, APELLIDO_PATERNO, APELLIDO_MATERNO,
                   EMAIL, TELEFONO, ESTADO, FECHA_CREACION, FECHA_ACTUALIZACION
            FROM DOCENTE
            WHERE ID = p_id;
    END obtener;


    PROCEDURE listar(
        p_institucion_id IN NUMBER,
        p_estado         IN VARCHAR2,
        p_busqueda       IN VARCHAR2,
        p_page           IN NUMBER,
        p_size           IN NUMBER,
        p_cursor         OUT SYS_REFCURSOR,
        p_total          OUT NUMBER
    ) IS
        v_patron VARCHAR2(202);
    BEGIN
        v_patron := '%' || UPPER(p_busqueda) || '%';

        SELECT COUNT(*)
        INTO p_total
        FROM DOCENTE
        WHERE (p_institucion_id IS NULL OR INSTITUCION_ID = p_institucion_id)
          AND (p_estado IS NULL OR ESTADO = p_estado)
          AND (p_busqueda IS NULL
               OR UPPER(NOMBRES) LIKE v_patron
               OR UPPER(APELLIDO_PATERNO) LIKE v_patron
               OR UPPER(APELLIDO_MATERNO) LIKE v_patron
               OR UPPER(RUT) LIKE v_patron);

        OPEN p_cursor FOR
            SELECT ID, INSTITUCION_ID, RUT, NOMBRES, APELLIDO_PATERNO, APELLIDO_MATERNO,
                   EMAIL, TELEFONO, ESTADO, FECHA_CREACION, FECHA_ACTUALIZACION
            FROM DOCENTE
            WHERE (p_institucion_id IS NULL OR INSTITUCION_ID = p_institucion_id)
              AND (p_estado IS NULL OR ESTADO = p_estado)
              AND (p_busqueda IS NULL
                   OR UPPER(NOMBRES) LIKE v_patron
                   OR UPPER(APELLIDO_PATERNO) LIKE v_patron
                   OR UPPER(APELLIDO_MATERNO) LIKE v_patron
                   OR UPPER(RUT) LIKE v_patron)
            ORDER BY ID
            OFFSET (p_page - 1) * p_size ROWS FETCH NEXT p_size ROWS ONLY;
    END listar;

END PKG_DOCENTE;
"""


def upgrade() -> None:
    op.execute(_PKG_INSTITUCION_SPEC)
    _verificar_compilacion("PKG_INSTITUCION", "PACKAGE")
    op.execute(_PKG_INSTITUCION_BODY)
    _verificar_compilacion("PKG_INSTITUCION", "PACKAGE BODY")

    op.execute(_PKG_DOCENTE_SPEC)
    _verificar_compilacion("PKG_DOCENTE", "PACKAGE")
    op.execute(_PKG_DOCENTE_BODY)
    _verificar_compilacion("PKG_DOCENTE", "PACKAGE BODY")


def downgrade() -> None:
    op.execute("DROP PACKAGE PKG_DOCENTE")
    op.execute("DROP PACKAGE PKG_INSTITUCION")
