import datetime as dt
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    crear_access_token,
    crear_refresh_token,
    crear_reset_token,
    decodificar_token,
    permisos_de_usuario,
    verificar_password,
)
from app.seguridad.models import Cliente, Usuario
from app.seguridad.repository import ClienteRepository, UsuarioRepository
from app.seguridad.schemas import (
    ClientePerfilActualizar,
    LoginRequest,
    RegistroRequest,
    TokenRespuesta,
    UsuarioCrear,
)

logger = logging.getLogger(__name__)

usuario_repo = UsuarioRepository()
cliente_repo = ClienteRepository()

ROL_CLIENTE = "cliente"


def registrar_cliente(db: Session, datos: RegistroRequest) -> Usuario:
    usuario = usuario_repo.crear(
        db,
        UsuarioCrear(
            nombre=datos.nombre,
            apellido=datos.apellido,
            email=datos.email,
            telefono=datos.telefono,
            password=datos.password,
        ),
    )
    usuario_repo.asignar_roles(db, usuario, [ROL_CLIENTE])

    cliente = Cliente(usuario_id=usuario.id, ci_nit=datos.ci_nit)
    db.add(cliente)
    db.commit()
    db.refresh(usuario)
    return usuario


def _generar_tokens(usuario_id: int, roles: list[str], permisos: list[str]) -> TokenRespuesta:
    return TokenRespuesta(
        access_token=crear_access_token(usuario_id, roles, permisos),
        refresh_token=crear_refresh_token(usuario_id),
    )


def login(db: Session, datos: LoginRequest) -> TokenRespuesta:
    usuario = usuario_repo.obtener_por_email(db, datos.email)
    credenciales_invalidas = (
        usuario is None
        or not usuario.activo
        or not verificar_password(datos.password, usuario.password_hash)
    )
    if credenciales_invalidas:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    usuario.ultimo_acceso = dt.datetime.now(dt.timezone.utc)
    db.commit()

    roles = [r.nombre for r in usuario.roles]
    permisos = permisos_de_usuario(db, usuario.id)
    return _generar_tokens(usuario.id, roles, permisos)


def refrescar_token(db: Session, refresh_token: str) -> TokenRespuesta:
    payload = decodificar_token(refresh_token)
    if payload.get("tipo") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    roles = [r.nombre for r in usuario.roles]
    permisos = permisos_de_usuario(db, usuario.id)
    return _generar_tokens(usuario.id, roles, permisos)


def solicitar_recuperacion(db: Session, email: str) -> None:
    """Genera un token de recuperación si el email existe.

    Todavía no hay un servicio de correo en el proyecto, así que el token se
    deja en el log para pruebas manuales. La respuesta al cliente es siempre
    genérica (ver router) para no revelar si el email está registrado.
    """
    usuario = usuario_repo.obtener_por_email(db, email)
    if usuario is not None and usuario.activo:
        token = crear_reset_token(usuario.id)
        logger.info("Token de recuperación para %s: %s", email, token)


def obtener_usuario(db: Session, usuario_id: int) -> Usuario:
    """Punto de entrada para que otros paquetes (p. ej. organizacion, al crear
    un empleado) validen un usuario sin consultar la tabla directamente."""
    return usuario_repo.obtener(db, usuario_id)


def obtener_perfil_cliente(db: Session, usuario_id: int) -> Cliente:
    return cliente_repo.obtener_por_usuario(db, usuario_id)


def obtener_cliente(db: Session, cliente_id: int) -> Cliente:
    """Para que otros paquetes (p. ej. `reservas`, para notificar al dueño
    de una reserva) resuelvan el usuario_id de un cliente sin consultar
    la tabla `cliente` directamente."""
    return cliente_repo.obtener(db, cliente_id)


def actualizar_perfil_cliente(
    db: Session, usuario_id: int, datos: ClientePerfilActualizar
) -> Cliente:
    return cliente_repo.actualizar_perfil(db, usuario_id, datos)
