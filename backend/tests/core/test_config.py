from app.core.config import Settings


def _settings(database_url: str) -> Settings:
    return Settings(database_url=database_url, jwt_secret_key="clave-de-pruebas")


def test_normaliza_postgres_a_psycopg():
    assert _settings("postgres://user:pass@host:5432/db").database_url == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_normaliza_postgresql_a_psycopg():
    assert _settings("postgresql://user:pass@host:5432/db").database_url == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_no_toca_una_url_que_ya_es_psycopg():
    url = "postgresql+psycopg://user:pass@host:5432/db"
    assert _settings(url).database_url == url


def test_no_toca_urls_de_otros_motores():
    url = "sqlite:///:memory:"
    assert _settings(url).database_url == url
