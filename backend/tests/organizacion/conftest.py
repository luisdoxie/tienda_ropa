import pytest

from app.seguridad.repository import UsuarioRepository
from app.seguridad.schemas import UsuarioCrear


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
def cliente_headers(client, db_session):
    usuario_repo = UsuarioRepository()
    usuario = usuario_repo.crear(
        db_session,
        UsuarioCrear(nombre="Cli", apellido="Ente", email="cliente@example.com", password="claveSegura123"),
    )
    usuario_repo.asignar_roles(db_session, usuario, ["cliente"])

    token = _login(client, "cliente@example.com", "claveSegura123")
    return {"Authorization": f"Bearer {token}"}
