from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import registrar_handlers
from app.organizacion.router import routers as organizacion_routers
from app.seguridad.router import routers as seguridad_routers

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
def health() -> dict[str, str]:
    return {"status": "ok"}


# Los routers de cada paquete de negocio se registran acá a medida que existen.
for router in seguridad_routers + organizacion_routers:
    app.include_router(router)
