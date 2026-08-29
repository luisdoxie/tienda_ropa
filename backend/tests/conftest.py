import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "clave-de-pruebas")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.catalogo import models as _catalogo_models  # noqa: F401  (registra las tablas)
from app.organizacion import models as _organizacion_models  # noqa: F401  (registra las tablas)
from app.probador import models as _probador_models  # noqa: F401  (registra las tablas)
from app.seguridad import models as _seguridad_models  # noqa: F401  (registra las tablas)
from app.seguridad.repository import UsuarioRepository
from app.seguridad.schemas import UsuarioCrear
from scripts.seed_seguridad import seed as seed_seguridad


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    seed_seguridad(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(client, email, password):
    respuesta = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return respuesta.json()["access_token"]


@pytest.fixture()
def admin_headers(client, db_session):
    usuario_repo = UsuarioRepository()
    usuario = usuario_repo.crear(
        db_session,
        UsuarioCrear(nombre="Admin", apellido="Root", email="admin@example.com", password="claveSegura123"),
    )
    usuario_repo.asignar_roles(db_session, usuario, ["administrador"])

    token = _login(client, "admin@example.com", "claveSegura123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def cliente_headers(client):
    # Vía /auth/registro (no usuario_repo.crear a mano): así el usuario
    # también tiene su fila en `cliente`, igual que en producción. Varios
    # endpoints (favoritos, perfil) la necesitan.
    client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Cli",
            "apellido": "Ente",
            "email": "cliente@example.com",
            "password": "claveSegura123",
        },
    )
    token = _login(client, "cliente@example.com", "claveSegura123")
    return {"Authorization": f"Bearer {token}"}
