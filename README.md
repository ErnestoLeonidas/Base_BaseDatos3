# EvalAI — API Colegio

API base para EvalAI, la plataforma que permite a docentes de colegios chilenos generar,
aplicar y corregir evaluaciones alineadas a Objetivos de Aprendizaje (OA).

El sistema se construye **por módulos y etapas**. Hasta ahora están construidas:

- **Etapa 0** — base del proyecto: estructura en capas, conexión a Oracle, migraciones
  Alembic y manejo de errores uniforme.
- **Etapa 1** — registro de docentes: tablas `INSTITUCION`/`DOCENTE`, endpoints de
  registro/listado/actualización y activación-desactivación.

Las etapas futuras (autenticación, base curricular, cursos, evaluaciones, etc.) se
agregan sobre esta base sin necesidad de rehacerla.

> 📘 Si vas a replicar este proyecto paso a paso (por ejemplo, como estudiante del
> taller), usa [`docs/guia-paso-a-paso.md`](docs/guia-paso-a-paso.md): explica cada
> comando, el porqué de cada decisión de diseño, y los problemas más comunes al
> levantarlo desde cero.

## Stack

- Python 3.12 · FastAPI · Uvicorn
- Oracle Database 23ai Free (Docker, imagen `gvenzl/oracle-free`)
- `python-oracledb` (modo thin) + SQLAlchemy 2.0 + Alembic
- Pydantic v2 + pydantic-settings
- Argon2 (`argon2-cffi`) para hash de contraseñas
- pytest + httpx

## Estructura del proyecto

```
app/
  core/          # configuración, seguridad (hash de contraseñas), manejo de errores
  db/            # engine, sesión, Base declarativa
  models/        # modelos SQLAlchemy (se completan en cada etapa)
  schemas/       # modelos Pydantic de request/response
  repositories/  # acceso a datos
  services/      # reglas de negocio
  api/v1/        # routers versionados por módulo
  main.py
alembic/         # migraciones versionadas
tests/
docs/
```

Cada etapa futura solo necesita agregar: su router en `app/api/v1/`, sus modelos y
schemas, su service y su migración Alembic. No es necesario modificar `app/core`,
`app/db` ni el manejo de errores ya definidos.

## Requisitos previos

- Docker y Docker Compose.
- No se requiere tener Python ni Oracle instalados en el equipo: todo corre en
  contenedores, usando exactamente Python 3.12 dentro de ellos.

## Levantar el proyecto desde cero

1. Copiar el archivo de variables de entorno de ejemplo y ajustarlo si se quiere:

   ```
   cp .env.example .env
   ```

   (En Windows PowerShell: `Copy-Item .env.example .env`)

2. Construir y levantar los servicios (Oracle + API):

   ```
   docker compose up -d --build
   ```

   La primera vez, Oracle puede tardar 1-2 minutos en inicializarse (crea la base,
   el PDB `FREEPDB1` y el usuario de aplicación). Se puede seguir el progreso con:

   ```
   docker compose logs -f oracle
   ```

   El servicio `api` espera automáticamente a que Oracle esté saludable
   (`depends_on: condition: service_healthy`) antes de arrancar.

3. Aplicar las migraciones de base de datos (crea las tablas y siembra 2 instituciones
   de ejemplo):

   ```
   docker compose exec api alembic upgrade head
   ```

4. Verificar que todo funciona:

   - Estado del servicio y de la conexión a la base de datos:
     `GET http://localhost:8000/health`
   - Instituciones sembradas: `GET http://localhost:8000/api/v1/instituciones`
   - Documentación interactiva (Swagger UI): `http://localhost:8000/docs`
   - Documentación alternativa (ReDoc): `http://localhost:8000/redoc`

## Ejecutar las pruebas

Las pruebas corren contra la base Oracle del propio `docker-compose.yml` (no se usa
SQLite, para no divergir del dialecto real). Cada test queda envuelto en una
transacción que se revierte al final (`tests/conftest.py`), así que no deja datos
residuales en la base aunque se ejecute muchas veces:

```
docker compose exec api pytest
```

## Variables de entorno (`.env`)

| Variable         | Descripción                                                              |
| ---------------- | ------------------------------------------------------------------------- |
| `ORACLE_USER`     | Usuario de aplicación en Oracle (se crea automáticamente al levantar el contenedor). |
| `ORACLE_PASSWORD` | Contraseña de ese usuario (y de SYS/SYSTEM, solo en desarrollo local).    |
| `ORACLE_DSN`      | Cadena de conexión `host:puerto/servicio`. Dentro de Docker Compose: `oracle:1521/FREEPDB1`. |
| `APP_ENV`         | Entorno de ejecución: `desarrollo` \| `pruebas` \| `produccion`.          |

No se incluyen credenciales reales en el repositorio; `.env` está excluido en
`.gitignore`.

## Manejo de errores

Todas las respuestas de error siguen el mismo formato:

```json
{ "error": "<codigo>", "mensaje": "<texto en español>", "detalle": null }
```

Las excepciones de dominio (`RecursoNoEncontradoError`, `ConflictoError`,
`ValidacionNegocioError`, definidas en `app/core/errors.py`) se traducen automáticamente
a este formato. Las etapas futuras deben lanzar estas excepciones en sus `services` en
lugar de construir respuestas HTTP manualmente.

## Acceso a datos: paquetes PL/SQL

El acceso a datos de Institución/Docente **no usa el ORM para leer ni escribir**: la
API llama a paquetes PL/SQL (`PKG_INSTITUCION`, `PKG_DOCENTE`, creados en la migración
`0003`), que son los que además concentran las validaciones de negocio (RUT/email
único, institución activa, existencia del docente), reportadas con
`RAISE_APPLICATION_ERROR` y códigos `-20001`..`-20005`. `app/db/oracle_calls.py` traduce
esos códigos a las excepciones de dominio de la API. El detalle completo está en
[`docs/modelo-datos.md`](docs/modelo-datos.md).

El hash de la contraseña (Argon2) se sigue calculando en Python, ya que PL/SQL no tiene
una implementación nativa.

## Migraciones (Alembic)

- Crear una nueva migración (a partir de los modelos en `app/models/`):

  ```
  docker compose exec api alembic revision --autogenerate -m "descripcion"
  ```

- Aplicar migraciones pendientes:

  ```
  docker compose exec api alembic upgrade head
  ```

## Modelo de datos

Ver [`docs/modelo-datos.md`](docs/modelo-datos.md): diagrama entidad-relación (Mermaid)
y tabla de trazabilidad endpoint ↔ requisito.

## Estado actual

- **Etapa 0 — Base del proyecto:** completa.
- **Etapa 1 — Registro de docentes:** completa (tablas `INSTITUCION`/`DOCENTE`,
  endpoints de registro, listado, obtención, actualización y activación/desactivación).
- Etapas 2 en adelante (autenticación, base curricular, cursos, evaluaciones,
  corrección por fotografía, reportería): no implementadas, solo referenciadas en el
  diseño.
