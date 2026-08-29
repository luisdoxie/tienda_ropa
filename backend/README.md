# FashionStore — Backend

FastAPI + SQLAlchemy 2.0 + Alembic. Ver `../CLAUDE.md` para la arquitectura completa.

## Desarrollo local

```bash
py -3.13 -m venv .venv
.venv/Scripts/activate            # Windows
pip install -r requirements-dev.txt
cp .env.example .env              # completar DATABASE_URL y JWT_SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

Requiere PostgreSQL local con la base `fashionstore_dev` ya creada a mano (ver "Entorno local" en `CLAUDE.md`).

## Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | Cadena de conexión a PostgreSQL. Acepta `postgresql+psycopg://...`, `postgresql://...` o `postgres://...` — las dos últimas se normalizan solas a `+psycopg` en `core/config.py`, porque Railway inyecta la variable en formato psycopg2 y el proyecto usa psycopg 3. |
| `JWT_SECRET_KEY` | Sí | Secreto para firmar los JWT. Un valor aleatorio largo, distinto en cada entorno. |
| `JWT_ALGORITHM` | No (`HS256`) | Algoritmo de firma. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No (`30`) | Vida del access token. |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No (`7`) | Vida del refresh token. |
| `CORS_ORIGINS` | No (`http://localhost:4200`) | Orígenes permitidos, separados por coma. En producción debe incluir el dominio de Vercel del front (ej. `https://fashionstore.vercel.app`). |
| `ENVIRONMENT` | No (`local`) | Etiqueta informativa (`local`, `production`, ...). |
| `PORT` | La define Railway | Puerto en el que escucha uvicorn. No se declara a mano: Railway la inyecta y `scripts/start.sh` la lee. |

## Despliegue en Railway (sin Docker)

1. **Crear el proyecto en Railway** con dos servicios: PostgreSQL (plugin) y este backend, apuntando al repositorio con `backend/` como root del servicio.
2. **Variables de entorno del servicio backend**: cargar `JWT_SECRET_KEY`, `CORS_ORIGINS` (con el dominio real de Vercel) y `ENVIRONMENT=production`. `DATABASE_URL` no se carga a mano: Railway la provee automáticamente al enlazar el plugin de PostgreSQL (queda referenciada como `${{Postgres.DATABASE_URL}}` o similar).
3. **Build**: Railway detecta Python vía Nixpacks a partir de `requirements.txt` y `.python-version` (fijado en `3.13`). Si el autodetector eligiera otra versión, fijarla explícitamente con la variable de entorno `NIXPACKS_PYTHON_VERSION=3.13` en el servicio.
4. **Arranque**: `railway.json` define `deploy.startCommand = bash scripts/start.sh`. Ese script corre `alembic upgrade head` una sola vez y recién después hace `exec uvicorn ... --port $PORT`. Las migraciones no se repiten por worker porque corren antes del `exec`, en un único proceso de arranque.
5. **Health check**: `railway.json` apunta `deploy.healthcheckPath` a `/health`. Railway no promueve el nuevo deploy a "en línea" hasta que ese endpoint responda 200. `/health` ejecuta `SELECT 1` contra la base real — si la base no responde, devuelve 503, no un falso "ok".
6. Verificar `/health` manualmente en el navegador (`https://<servicio>.up.railway.app/health`) antes de dar el despliegue por bueno.

### CORS con Vercel

El front en Angular se despliega en Vercel. Una vez que Vercel asigna el dominio (o el dominio propio si se configura uno), agregarlo a `CORS_ORIGINS` en las variables de entorno de Railway, separado por coma si conviven varios orígenes (ej. previews). No hace falta redeploy de código, solo reiniciar el servicio para que tome la variable nueva.

## Migraciones

```bash
alembic revision --autogenerate -m "descripcion"
# revisar a mano el archivo generado antes de aplicar
alembic upgrade head
```

Nunca a mano contra la base. Ver "Flujo de cambios de esquema" en `CLAUDE.md`.
