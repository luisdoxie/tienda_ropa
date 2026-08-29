"""Hash de contraseñas, JWT y dependencias de autenticación/autorización.

Vive en `core` (así lo pide el plan de desarrollo), pero para verificar
permisos necesita consultar las tablas del paquete `seguridad`. Los modelos
se importan de forma diferida dentro de las funciones para dejar explícita
esa dependencia hacia arriba, que es la única excepción a la regla de
paquetes de CLAUDE.md.
"""

from __future__ import annotations

import datetime as dt

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import PermisoDenegadoError

settings = get_settings()

_bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _crear_token(usuario_id: int, tipo: str, expira: dt.timedelta, extra: dict | None = None) -> str:
    ahora = dt.datetime.now(dt.timezone.utc)
    payload: dict = {"sub": str(usuario_id), "tipo": tipo, "iat": ahora, "exp": ahora + expira}
    payload.update(extra or {})
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def crear_access_token(usuario_id: int, roles: list[str], permisos: list[str]) -> str:
    """El payload lleva usuario_id, roles y permisos, nunca la contraseña."""
    return _crear_token(
        usuario_id,
        tipo="access",
        expira=dt.timedelta(minutes=settings.jwt_access_token_expire_minutes),
        extra={"roles": roles, "permisos": permisos},
    )


def crear_refresh_token(usuario_id: int) -> str:
    return _crear_token(
        usuario_id,
        tipo="refresh",
        expira=dt.timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def crear_reset_token(usuario_id: int) -> str:
    return _crear_token(usuario_id, tipo="reset", expira=dt.timedelta(minutes=30))


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado"
        ) from exc


def permisos_de_usuario(db: Session, usuario_id: int) -> list[str]:
    """Códigos de permiso reales del usuario, vía sus roles activos."""
    from app.seguridad.models import Permiso, Rol, rol_permiso, usuario_rol

    filas = db.execute(
        select(Permiso.codigo)
        .join(rol_permiso, rol_permiso.c.permiso_id == Permiso.id)
        .join(Rol, Rol.id == rol_permiso.c.rol_id)
        .join(usuario_rol, usuario_rol.c.rol_id == Rol.id)
        .where(usuario_rol.c.usuario_id == usuario_id, Rol.activo.is_(True))
        .distinct()
    ).scalars()
    return list(filas)


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
):
    from app.seguridad.models import Usuario

    if credenciales is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    payload = decodificar_token(credenciales.credentials)
    if payload.get("tipo") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")
    return usuario


def require_permission(codigo: str):
    """Dependencia que exige el permiso `codigo`.

    Consulta rol_permiso/usuario_rol en cada request: el permiso vivo en la
    base es la fuente de verdad, no una lista fija ni lo que venga en el JWT.
    """

    def verificador(usuario=Depends(get_current_user), db: Session = Depends(get_db)):
        if codigo not in permisos_de_usuario(db, usuario.id):
            raise PermisoDenegadoError(f"Falta el permiso '{codigo}'")
        return usuario

    return verificador


def require_service_token(x_service_token: str | None = Header(default=None)) -> None:
    """Protege endpoints de tareas de sistema (cron/scheduler), que no
    tienen un usuario logueado detrás. No es un JWT: es un secreto fijo
    compartido, configurado por variable de entorno (TAREAS_TOKEN). Si no
    está configurado, la tarea queda inhabilitada (nunca compara contra
    una cadena vacía)."""
    if not settings.tareas_token or x_service_token != settings.tareas_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de servicio inválido")
