# Guía paso a paso — EvalAI API Colegio

Esta guía explica, paso a paso, cómo levantar el proyecto desde cero y cómo está
construido, para que cualquier estudiante del taller pueda **replicarlo** en su propio
equipo y entender las decisiones de diseño. Cubre lo que existe hoy: **Etapa 0** (base
del proyecto) y **Etapa 1** (registro de docentes).

No reemplaza al [`README.md`](../README.md) (más breve, "cómo arrancar rápido") ni a
[`modelo-datos.md`](modelo-datos.md) (diagrama ER y trazabilidad): esta guía es el
recorrido completo, con el porqué de cada decisión.

## Índice

1. [Requisitos previos](#1-requisitos-previos)
2. [Obtener el proyecto y configurarlo](#2-obtener-el-proyecto-y-configurarlo)
3. [Levantar Oracle y la API con Docker Compose](#3-levantar-oracle-y-la-api-con-docker-compose)
4. [Aplicar las migraciones](#4-aplicar-las-migraciones)
5. [Verificar que todo funciona](#5-verificar-que-todo-funciona)
6. [Cómo está organizado el código (arquitectura en capas)](#6-cómo-está-organizado-el-código-arquitectura-en-capas)
7. [El modelo de datos](#7-el-modelo-de-datos)
8. [Por qué el acceso a datos pasa por paquetes PL/SQL](#8-por-qué-el-acceso-a-datos-pasa-por-paquetes-plsql)
9. [Las reglas de negocio del registro de docentes](#9-las-reglas-de-negocio-del-registro-de-docentes)
10. [Probar los endpoints](#10-probar-los-endpoints)
11. [Poblar datos de prueba](#11-poblar-datos-de-prueba)
12. [Ejecutar las pruebas automatizadas](#12-ejecutar-las-pruebas-automatizadas)
13. [Manejo de errores](#13-manejo-de-errores)
14. [Problemas comunes al replicar esto (y por qué pasan)](#14-problemas-comunes-al-replicar-esto-y-por-qué-pasan)
15. [Cómo seguir construyendo (etapas futuras)](#15-cómo-seguir-construyendo-etapas-futuras)
16. [Chuleta de comandos](#16-chuleta-de-comandos)

---

## 1. Requisitos previos

- **Docker** y **Docker Compose** instalados y funcionando (`docker --version`,
  `docker compose version`).
- **No necesitas** tener Python ni Oracle instalados en tu equipo: la API corre con
  Python 3.12 dentro de un contenedor, y Oracle corre en otro contenedor
  (`gvenzl/oracle-free`). Esto es deliberado: así todos en el curso corren exactamente
  la misma versión, sin depender de lo que cada uno tenga instalado localmente.
- Un cliente HTTP para probar (`curl`, o el navegador para Swagger UI).

## 2. Obtener el proyecto y configurarlo

1. Clona o copia la carpeta del proyecto.
2. Copia el archivo de variables de entorno de ejemplo:

   ```bash
   cp .env.example .env
   ```

   En Windows PowerShell: `Copy-Item .env.example .env`.

3. Abre `.env` y revisa las 4 variables (puedes dejar los valores de ejemplo tal
   cual para desarrollo local):

   | Variable | Para qué sirve |
   | --- | --- |
   | `ORACLE_USER` | Usuario de aplicación dentro de Oracle. La imagen de Docker lo crea automáticamente la primera vez que levanta el contenedor. |
   | `ORACLE_PASSWORD` | Contraseña de ese usuario (y, solo en este entorno de desarrollo, también la de `SYS`/`SYSTEM`). |
   | `ORACLE_DSN` | Cadena de conexión `host:puerto/servicio`. Dentro de la red de Docker Compose el host se llama `oracle` y el servicio es `FREEPDB1` (el PDB que trae por defecto la imagen `gvenzl/oracle-free`). |
   | `APP_ENV` | `desarrollo` \| `pruebas` \| `produccion`. Hoy no cambia nada automáticamente, pero las etapas futuras pueden usarla. |

   **Nunca** subas un `.env` con credenciales reales a un repositorio — por eso está
   en `.gitignore` y solo se versiona `.env.example` con valores de ejemplo.

## 3. Levantar Oracle y la API con Docker Compose

```bash
docker compose up -d --build
```

Esto hace dos cosas (ver `docker-compose.yml`):

- Levanta el servicio **`oracle`** (imagen `gvenzl/oracle-free`). La **primera vez**
  tarda 1-2 minutos: crea la base, el PDB `FREEPDB1`, y el usuario de aplicación
  (`APP_USER`/`APP_USER_PASSWORD`, tomados de tu `.env`). Los datos quedan en un
  volumen de Docker (`oracle_data`) para que no se pierdan si solo detienes el
  contenedor (`docker compose down`, sin `-v`).
- Construye y levanta el servicio **`api`** (tu código, con `uvicorn --reload`). Este
  servicio **espera automáticamente** a que Oracle esté "healthy"
  (`depends_on: condition: service_healthy`) antes de arrancar — no necesitas
  calcular tiempos de espera a mano.

Para ver el progreso de la inicialización de Oracle:

```bash
docker compose logs -f oracle
```

Cuando veas `DATABASE IS READY TO USE!` ya puedes seguir al siguiente paso. Para
confirmar el estado de los dos contenedores:

```bash
docker compose ps
```

Ambos deberían aparecer `Up`, y `evalai-oracle` además como `(healthy)`.

## 4. Aplicar las migraciones

La base de datos arranca **vacía** (sin tablas ni paquetes): todo lo crea Alembic,
nunca `Base.metadata.create_all()`. Aplica todas las migraciones pendientes con:

```bash
docker compose exec api alembic upgrade head
```

Esto corre, en orden, cada migración que hay en `alembic/versions/`:

| Migración | Qué hace |
| --- | --- |
| `0001_baseline` | No cambia el esquema; solo deja inicializada la tabla de control de Alembic (`alembic_version`) sobre una base limpia. |
| `0002_docentes_instituciones` | Crea las tablas `INSTITUCION` y `DOCENTE` (con sus constraints, índice, etc.) y siembra 2 instituciones de ejemplo. |
| `0003_paquetes_plsql` | Crea los paquetes `PKG_INSTITUCION` y `PKG_DOCENTE` (ver [sección 8](#8-por-qué-el-acceso-a-datos-pasa-por-paquetes-plsql)). |

Para ver en qué migración está la base, o el historial completo:

```bash
docker compose exec api alembic current
docker compose exec api alembic history
```

Si alguna vez quieres dejar la base limpia y repetir todo desde cero (por ejemplo,
para practicar el proceso completo), puedes borrar el volumen de Oracle y repetir
desde el paso 3:

```bash
docker compose down -v   # -v también borra los datos de Oracle
docker compose up -d --build
docker compose exec api alembic upgrade head
```

## 5. Verificar que todo funciona

- **Salud del servicio y de la conexión a la base**:
  `curl http://localhost:8000/health` → `{"estado":"ok","base_datos":"conectada"}`.
- **Documentación interactiva (Swagger UI)**: abre
  `http://localhost:8000/docs` en el navegador. Ahí puedes probar cada endpoint sin
  necesidad de `curl`.
- **ReDoc** (documentación de solo lectura, más pulida para leer): `/redoc`.
- **Instituciones sembradas**: `curl http://localhost:8000/api/v1/instituciones`.

## 6. Cómo está organizado el código (arquitectura en capas)

```mermaid
flowchart LR
    subgraph HTTP
        A["app/api/v1/*.py<br/>routers (FastAPI)"]
    end
    subgraph Negocio
        B["app/services/*.py<br/>orquesta, hashea password"]
    end
    subgraph Datos
        C["app/repositories/*.py<br/>arma parámetros, llama paquetes"]
    end
    subgraph "Base de datos"
        D["PKG_INSTITUCION / PKG_DOCENTE<br/>(PL/SQL: valida + hace el DML)"]
    end
    A --> B --> C --> D
```

Cada capa tiene una responsabilidad y solo conoce a la capa inmediatamente inferior:

- **`app/api/v1/`** (routers): define las rutas HTTP, valida la forma del request con
  Pydantic (`app/schemas/`), y traduce la respuesta del service a JSON. No tiene
  lógica de negocio.
- **`app/services/`**: orquesta. En esta etapa, `DocenteService` solo calcula el hash
  Argon2 de la contraseña (lo único que **no puede** vivir en la base de datos) y le
  pide al repositorio que inserte/actualice/liste.
- **`app/repositories/`**: la única capa que sabe cómo hablar con Oracle. No contiene
  reglas de negocio — solo arma los parámetros y llama al procedimiento/función del
  paquete PL/SQL correspondiente.
- **`app/core/`**: infraestructura transversal (configuración, hash de contraseñas,
  manejo uniforme de errores, validación de RUT) — reutilizable por cualquier etapa
  futura.
- **`app/db/`**: el engine de SQLAlchemy, la sesión por request (`get_db`), y
  `oracle_calls.py` (el puente entre la sesión de SQLAlchemy y los paquetes PL/SQL).

## 7. El modelo de datos

El detalle completo (diagrama entidad-relación en Mermaid, convenciones de nombres,
tabla de trazabilidad endpoint↔requisito) está en
[`modelo-datos.md`](modelo-datos.md). En resumen:

- **`INSTITUCION`**: `ID`, `NOMBRE`, `RBD` (único), `COMUNA`, `ACTIVA`,
  `FECHA_CREACION`.
- **`DOCENTE`**: `ID`, `INSTITUCION_ID` (FK), `RUT` (único, normalizado),
  `NOMBRES`, `APELLIDO_PATERNO`, `APELLIDO_MATERNO`, `EMAIL` (único, en minúsculas),
  `TELEFONO` (opcional), `PASSWORD_HASH`, `ESTADO`, `FECHA_CREACION`,
  `FECHA_ACTUALIZACION`.

Convenciones que vale la pena internalizar para el resto del taller: nombres de
tablas/columnas en MAYÚSCULAS, `VARCHAR2` con largo explícito, `ID` como
`GENERATED ALWAYS AS IDENTITY`, fechas como `TIMESTAMP WITH TIME ZONE`, booleanos
como `NUMBER(1)` con `CHECK (col IN (0,1))` (por compatibilidad con Oracle 19c, que no
tiene tipo `BOOLEAN` nativo en tablas), y **todas** las constraints con nombre
explícito (`PK_`, `FK_`, `UK_`, `CK_`) — nunca dejar que Oracle les ponga un nombre
autogenerado tipo `SYS_C00123456`, porque hace ilegible cualquier mensaje de error
futuro.

## 8. Por qué el acceso a datos pasa por paquetes PL/SQL

En la primera versión de la Etapa 1, la API leía y escribía `INSTITUCION`/`DOCENTE`
con SQLAlchemy (ORM). Se migró a que **toda** esa lógica viva en paquetes PL/SQL
(`PKG_INSTITUCION`, `PKG_DOCENTE`, creados en la migración `0003`). Esto es un patrón
clásico de un taller de bases de datos: la lógica de acceso y las reglas de
integridad no viven solo en la aplicación, sino también en la base de datos, donde
cualquier otro cliente que se conecte (otro sistema, un script, SQL*Plus) las
respeta igual.

**`PKG_INSTITUCION`**
- `listar_activas(p_cursor OUT SYS_REFCURSOR)`: instituciones con `ACTIVA = 1`.
- `esta_activa(p_id) RETURN NUMBER`: `1` si está activa, `0` si existe pero está
  inactiva, `-1` si el id no existe. La usa `PKG_DOCENTE` para no repetir la validación.

**`PKG_DOCENTE`**
- `insertar(...)`: valida que la institución exista y esté activa, que el RUT y el
  email no estén repetidos, inserta la fila y devuelve el `ID` nuevo por parámetro
  `OUT`.
- `actualizar(...)`: los parámetros que llegan en `NULL` significan "no cambiar ese
  campo" (actualización parcial, equivalente a un `PATCH`). Si cambia la institución
  o el email, revalida esas reglas.
- `cambiar_estado(p_id, p_estado)`: solo actualiza `ESTADO` y `FECHA_ACTUALIZACION`
  (eliminación lógica — nunca hay un `DELETE` físico).
- `obtener(p_id, p_cursor OUT SYS_REFCURSOR)` / `listar(..., p_cursor OUT
  SYS_REFCURSOR, p_total OUT NUMBER)`: lecturas, con paginación hecha en el propio
  PL/SQL (`OFFSET ... FETCH NEXT ... ROWS ONLY`) y búsqueda con `LIKE`.

Las validaciones de negocio se reportan con `RAISE_APPLICATION_ERROR(-200xx, mensaje)`
— es la forma estándar en PL/SQL de lanzar un "error de aplicación" con un código
propio (Oracle reserva el rango `-20000` a `-20999` exactamente para esto). Python
nunca parsea texto libre: lee el **código** del error con `oracledb` y lo traduce a
la excepción de dominio correcta en `app/db/oracle_calls.py`:

| Código Oracle | Significado | Excepción de dominio | HTTP |
| --- | --- | --- | --- |
| `-20001` | La institución indicada no existe | `RecursoNoEncontradoError` | `404` |
| `-20002` | La institución indicada no está activa | `ValidacionNegocioError` | `422` |
| `-20003` | El RUT ya está registrado | `ConflictoError` | `409` |
| `-20004` | El correo ya está registrado | `ConflictoError` | `409` |
| `-20005` | El docente no existe | `RecursoNoEncontradoError` | `404` |

Cómo se llama a un paquete desde Python (sin SQLAlchemy ORM) — la pieza clave está en
`app/db/oracle_calls.py::obtener_cursor()`: se toma el cursor nativo de `oracledb`
**de la misma conexión** que usa la `Session` de SQLAlchemy, así el `INSERT`/`UPDATE`
que hace el paquete participa de la misma transacción (se confirma con
`db.commit()`, se revierte con `db.rollback()`, igual que si fuera SQL del ORM).

## 9. Las reglas de negocio del registro de docentes

- **RUT chileno**: se valida el dígito verificador (módulo 11) y se normaliza al
  formato `12345678-5` (sin puntos, con guion). Se acepta con o sin puntos al
  ingresarlo. La función vive en `app/core/rut.py` (reutilizable por otras entidades
  con RUT en etapas futuras, p. ej. estudiantes).
- **Email**: formato válido (regex simple) y se guarda siempre en minúsculas.
- **Contraseña**: mínimo 8 caracteres, con al menos una letra y un número. Se guarda
  solo el **hash** (Argon2, vía `argon2-cffi`) — nunca el texto plano, y nunca se
  devuelve en ninguna respuesta de la API (ni siquiera el hash).
- **Nombres**: se les quita espacios repetidos y se capitalizan (`"maría  josé"` →
  `"María José"`). Es una heurística simple (`str.title()`), no reconoce partículas
  como "de la"/"del" en apellidos compuestos.
- **Institución**: debe existir y estar `ACTIVA` (lo valida `PKG_DOCENTE`, no Python).

## 10. Probar los endpoints

| Método y ruta | Qué hace | Tag en Swagger |
| --- | --- | --- |
| `POST /api/v1/docentes` | Registrar un docente | Docentes |
| `GET /api/v1/docentes` | Listar, con paginación (`page`, `size`) y filtros (`institucion_id`, `estado`, `busqueda`) | Docentes |
| `GET /api/v1/docentes/{id}` | Obtener un docente | Docentes |
| `PATCH /api/v1/docentes/{id}` | Actualizar datos (no cambia la contraseña ni el RUT) | Docentes |
| `PATCH /api/v1/docentes/{id}/estado` | Activar/desactivar (baja lógica) | Docentes |
| `GET /api/v1/instituciones` | Listar instituciones activas, para elegir una al registrar | Instituciones |

Ejemplo de registro feliz (ajusta el RUT si ya existe en tu base):

```bash
curl -X POST http://localhost:8000/api/v1/docentes \
  -H "Content-Type: application/json" \
  -d '{
        "institucion_id": 1,
        "rut": "12.345.678-5",
        "nombres": "María José",
        "apellido_paterno": "Pérez",
        "apellido_materno": "Soto",
        "email": "maria.perez@colegio.cl",
        "telefono": "+56912345678",
        "password": "Clave1234"
      }'
```

Casos de error que vale la pena probar (todos documentados con ejemplos en Swagger):
RUT con dígito verificador incorrecto (`422`), RUT o email ya registrados (`409`),
`institucion_id` que no existe (`404`), institución que existe pero está inactiva
(`422`), contraseña débil (`422`), docente que no existe en `GET`/`PATCH` (`404`).

## 11. Poblar datos de prueba

La forma correcta de poblar `DOCENTE` es **a través de la API** (nunca con `INSERT`
manual) — así pasan por las mismas validaciones que cualquier usuario real. Un
ejemplo con `httpx` corrido dentro del propio contenedor (usa
`app/core/rut.calcular_digito_verificador` para no tener que inventar RUTs válidos a
mano):

```bash
docker compose exec -T api python - <<'PYEOF'
import httpx
from app.core.rut import calcular_digito_verificador

base = "http://localhost:8000/api/v1/docentes"
with httpx.Client() as client:
    cuerpo = 10_000_001
    dv = calcular_digito_verificador(cuerpo)
    r = client.post(base, json={
        "institucion_id": 1,
        "rut": f"{cuerpo}-{dv}",
        "nombres": "Francisca Javiera",
        "apellido_paterno": "Vergara",
        "apellido_materno": "Castillo",
        "email": "vergara.francisca@liceo1.cl",
        "telefono": "+56911111111",
        "password": "ClaveDemo123",
    })
    print(r.status_code, r.json())
PYEOF
```

Para ver qué hay cargado en las tablas en un momento dado (solo para inspección, no
para modificar datos):

```bash
docker compose exec api python -c "
from app.db.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()
for fila in db.execute(text('SELECT ID, NOMBRES, RUT, ESTADO FROM DOCENTE ORDER BY ID')):
    print(fila)
db.close()
"
```

## 12. Ejecutar las pruebas automatizadas

```bash
docker compose exec api pytest -v
```

Las pruebas corren contra el **Oracle real** de Docker Compose (no SQLite, porque el
dialecto SQL no es el mismo — una prueba que pasa en SQLite puede fallar en Oracle, y
viceversa). Para que repetir la suite muchas veces no vaya llenando la base de datos
de prueba de basura, `tests/conftest.py` envuelve cada test en una transacción con
`SAVEPOINT` que se revierte al final (`db_session` + `after_transaction_end`): la
sesión de pytest ve los datos creados durante el test, y al terminar, desaparecen —
tus datos "reales" (los que poblaste en la sección 11) quedan intactos.

## 13. Manejo de errores

Toda respuesta de error de la API (sin excepción, incluidos errores no controlados)
usa el mismo formato:

```json
{ "error": "<codigo>", "mensaje": "<texto en español>", "detalle": null }
```

`<codigo>` es un slug (`"conflicto"`, `"recurso_no_encontrado"`, `"validacion"`) para
los errores de negocio, o el código HTTP mismo para errores genéricos (`404`, `405`,
`500`). El detalle completo del mapeo vive en `app/core/errors.py`.

## 14. Problemas comunes al replicar esto (y por qué pasan)

Si estás siguiendo esta guía desde cero y te encuentras con alguno de estos errores,
son justamente los que aparecieron construyendo este mismo proyecto — vale la pena
entender la causa, no solo copiar el arreglo:

- **`pip install python-oracledb` falla ("No matching distribution")**: el paquete
  de PyPI se llama `oracledb` (el proyecto se llama "python-oracledb", pero el nombre
  que usa `pip install` es distinto). Revisa `requirements.txt`.
- **`DPY-6003: SID "FREEPDB1" is not registered with the listener`**: al construir la
  URL de SQLAlchemy a mano (`oracle+oracledb://user:pass@host:port/FREEPDB1`), lo que
  va después del último `/` se interpreta como **SID**, no como *service name*.
  `FREEPDB1` es un nombre de servicio (de un PDB), no un SID — hay que pasarlo como
  parámetro de consulta `?service_name=FREEPDB1` (ver `app/core/config.py`).
- **Un `404`/`405` no usa el formato de error uniforme**: si registras un
  `@app.exception_handler(HTTPException)` importando `HTTPException` desde
  `fastapi`, no capturas los 404/405 que genera el propio framework internamente
  (esos usan `starlette.exceptions.HTTPException`, la clase **base**, no la subclase
  de FastAPI). Hay que registrar el handler sobre la clase de Starlette.
- **`WHERE ACTIVA IS 1` → `ORA-00908`**: en SQLAlchemy, comparar una columna
  `Boolean` con `.is_(True)` genera la sintaxis `IS 1`, que no es válida en Oracle
  (`IS` solo se usa con `NULL`/`NOT NULL` o, en Oracle 23ai+, con literales
  `TRUE`/`FALSE`, no con `1`). Hay que comparar con `== True` (`col == True`), que
  genera `= 1`.
- **Una migración que crea un paquete PL/SQL "no falla", pero el paquete no
  funciona**: `CREATE OR REPLACE PACKAGE BODY` con un error de sintaxis **no hace
  fallar la sentencia DDL** — Oracle deja el objeto en estado `INVALID` y el detalle
  queda en la vista `USER_ERRORS`. Si no revisas esa vista después de crear el
  paquete, `alembic upgrade head` puede terminar "exitosamente" con un paquete roto
  (ver `_verificar_compilacion()` en `alembic/versions/0003_paquetes_plsql.py`).
- **Oracle tarda "una eternidad" la primera vez**: es esperado — está inicializando
  la base de datos completa dentro del contenedor. Las veces siguientes (mientras no
  borres el volumen con `down -v`) es prácticamente instantáneo.

## 15. Cómo seguir construyendo (etapas futuras)

El diseño está pensado para que cada etapa futura (autenticación y roles, base
curricular, cursos y estudiantes, evaluaciones con IA, etc.) agregue, sin modificar
lo que ya existe:

- su **router** en `app/api/v1/`,
- sus **modelos** (si usa ORM) o sus **paquetes PL/SQL** (si sigue este mismo patrón)
  y sus **schemas** Pydantic,
- su **service**,
- su **migración** Alembic (una nueva, nunca editando `0001`/`0002`/`0003`).

`app/core` (configuración, seguridad, manejo de errores) y `app/db` (engine, sesión,
helpers para llamar paquetes) ya están listos para ser reutilizados tal cual.

## 16. Chuleta de comandos

```bash
# Levantar todo
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head

# Verificar
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/instituciones
# Swagger: http://localhost:8000/docs

# Pruebas
docker compose exec api pytest -v

# Ver logs
docker compose logs -f api
docker compose logs -f oracle

# Estado de las migraciones
docker compose exec api alembic current
docker compose exec api alembic history

# Reiniciar todo desde cero (borra los datos de Oracle)
docker compose down -v
docker compose up -d --build
docker compose exec api alembic upgrade head

# Apagar sin borrar datos
docker compose down
```
