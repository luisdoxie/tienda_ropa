def registrar(client, email="cliente1@example.com", password="unaClaveSegura123"):
    return client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "email": email,
            "password": password,
            "telefono": "70000000",
        },
    )


def test_registro_crea_usuario_con_rol_cliente(client):
    respuesta = registrar(client)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "cliente1@example.com"
    assert cuerpo["roles"] == ["cliente"]
    assert "password" not in cuerpo
    assert "password_hash" not in cuerpo


def test_registro_no_persiste_la_contrasena_en_texto_plano(client, db_session):
    registrar(client, email="cliente2@example.com", password="unaClaveSegura123")

    from app.seguridad.models import Usuario

    usuario = db_session.query(Usuario).filter(Usuario.email == "cliente2@example.com").one()
    assert usuario.password_hash != "unaClaveSegura123"
    assert usuario.password_hash.startswith("$2b$")


def test_login_correcto_devuelve_tokens(client):
    registrar(client, email="cliente3@example.com", password="unaClaveSegura123")

    respuesta = client.post(
        "/api/v1/auth/login",
        json={"email": "cliente3@example.com", "password": "unaClaveSegura123"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["access_token"]
    assert cuerpo["refresh_token"]


def test_login_con_contrasena_incorrecta_falla(client):
    registrar(client, email="cliente4@example.com", password="unaClaveSegura123")

    respuesta = client.post(
        "/api/v1/auth/login",
        json={"email": "cliente4@example.com", "password": "otra-clave"},
    )

    assert respuesta.status_code == 401


def test_endpoint_protegido_sin_token_es_rechazado(client):
    respuesta = client.get("/api/v1/roles")

    assert respuesta.status_code == 401


def test_endpoint_protegido_con_rol_insuficiente_es_rechazado(client):
    registrar(client, email="cliente5@example.com", password="unaClaveSegura123")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "cliente5@example.com", "password": "unaClaveSegura123"},
    )
    access_token = login.json()["access_token"]

    respuesta = client.get(
        "/api/v1/roles", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert respuesta.status_code == 403


def test_require_permission_revisa_la_tabla_en_vivo_no_el_token(client, db_session):
    """El token de acceso guarda los permisos al momento del login, pero
    require_permission debe volver a consultar rol_permiso en cada request.
    Si el admin le quita el permiso al rol después de emitido el token, el
    mismo token debe dejar de servir para esa acción."""
    from app.seguridad.models import Rol
    from app.seguridad.repository import UsuarioRepository

    registrar(client, email="admin1@example.com", password="unaClaveSegura123")

    usuario_repo = UsuarioRepository()
    usuario = usuario_repo.obtener_por_email(db_session, "admin1@example.com")
    usuario_repo.asignar_roles(db_session, usuario, ["administrador"])

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin1@example.com", "password": "unaClaveSegura123"},
    )
    access_token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    assert client.get("/api/v1/roles", headers=headers).status_code == 200

    rol_admin = db_session.query(Rol).filter(Rol.nombre == "administrador").one()
    rol_admin.permisos = [p for p in rol_admin.permisos if p.codigo != "roles.gestionar"]
    db_session.commit()

    respuesta = client.get("/api/v1/roles", headers=headers)
    assert respuesta.status_code == 403


def test_yo_devuelve_roles_y_permisos_del_usuario(client):
    registrar(client, email="cliente6@example.com", password="unaClaveSegura123")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "cliente6@example.com", "password": "unaClaveSegura123"},
    )
    access_token = login.json()["access_token"]

    respuesta = client.get("/api/v1/auth/yo", headers={"Authorization": f"Bearer {access_token}"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["roles"] == ["cliente"]
    assert "reservas.crear" in cuerpo["permisos"]
