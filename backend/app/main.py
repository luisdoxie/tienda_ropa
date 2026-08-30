import logging

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

# Carga .env al entorno real del proceso (no solo a Settings): lo necesita
# GOOGLE_APPLICATION_CREDENTIALS, que las Application Default Credentials
# de Google leen directo de os.environ, no de la app.
load_dotenv()

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import registrar_handlers
from app.abastecimiento.router import routers as abastecimiento_routers
from app.catalogo.router import routers as catalogo_routers
from app.core.router import routers as core_routers
from app.inventario.router import routers as inventario_routers
from app.organizacion.router import routers as organizacion_routers
from app.pagos.router import routers as pagos_routers
from app.probador.router import routers as probador_routers
from app.reservas.router import routers as reservas_routers
from app.seguridad.router import routers as seguridad_routers
from app.ventas.router import routers as ventas_routers

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="FashionStore API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_handlers(app)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: no se pudo conectar a la base de datos")
        return JSONResponse(status_code=503, content={"status": "error", "detalle": "base de datos no disponible"})
    return JSONResponse(status_code=200, content={"status": "ok"})


# Los routers de cada paquete de negocio se registran acá a medida que existen.
for router in (
    core_routers
    + seguridad_routers
    + organizacion_routers
    + catalogo_routers
    + probador_routers
    + inventario_routers
    + abastecimiento_routers
    + reservas_routers
    + ventas_routers
    + pagos_routers
):
    app.include_router(router)
