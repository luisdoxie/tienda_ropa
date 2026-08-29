from app.core.database import get_db
from app.main import app


def test_health_ok_cuando_la_base_responde(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_health_503_cuando_la_base_no_responde(client):
    class _SesionRota:
        def execute(self, *args, **kwargs):
            raise RuntimeError("sin conexión")

    def get_db_roto():
        yield _SesionRota()

    app.dependency_overrides[get_db] = get_db_roto
    try:
        respuesta = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert respuesta.status_code == 503
    assert respuesta.json()["status"] == "error"
