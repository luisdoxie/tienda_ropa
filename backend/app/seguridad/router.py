from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ParametrosPaginacion, parametros_paginacion
from app.core.security import get_current_user, permisos_de_usuario, require_permission
from app.seguridad import service
from app.seguridad.repository import RolRepository, UsuarioRepository
from app.seguridad.schemas import (
    AsignarPermisosRequest,
    AsignarRolesRequest,
    ClientePerfilActualizar,
    ClientePerfilRespuesta,
    LoginRequest,
    RecuperarRequest,
    RefreshRequest,
    RegistroRequest,
    RolActualizar,
    RolCrear,
    RolRespuesta,
    TokenRespuesta,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioRespuesta,
    UsuarioYoRespuesta,
)

rol_repo = RolRepository()
usuario_repo = UsuarioRepository()

PERMISO_ROLES = "roles.gestionar"
PERMISO_USUARIOS = "usuarios.gestionar"

# ---- /api/v1/auth -----------------------------------------------------------

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@auth_router.post("/registro", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def registro(datos: RegistroRequest, db: Session = Depends(get_db)) -> UsuarioRespuesta:
    usuario = service.registrar_cliente(db, datos)
    return UsuarioRespuesta.from_modelo(usuario)


@auth_router.post("/login", response_model=TokenRespuesta)
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> TokenRespuesta:
    return service.login(db, datos)


@auth_router.post("/refresh", response_model=TokenRespuesta)
def refresh(datos: RefreshRequest, db: Session = Depends(get_db)) -> TokenRespuesta:
    return service.refrescar_token(db, datos.refresh_token)


@auth_router.get("/yo", response_model=UsuarioYoRespuesta)
def yo(usuario=Depends(get_current_user), db: Session = Depends(get_db)) -> UsuarioYoRespuesta:
    base = UsuarioRespuesta.from_modelo(usuario)
    return UsuarioYoRespuesta(**base.model_dump(), permisos=permisos_de_usuario(db, usuario.id))


@auth_router.post("/recuperar", status_code=status.HTTP_202_ACCEPTED)
def recuperar(datos: RecuperarRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    service.solicitar_recuperacion(db, datos.email)
    return {"detail": "Si el correo está registrado, se enviarán instrucciones de recuperación."}


# ---- /api/v1/roles -----------------------------------------------------------

roles_router = APIRouter(prefix="/api/v1/roles", tags=["roles"])


@roles_router.get("", response_model=list[RolRespuesta], dependencies=[Depends(require_permission(PERMISO_ROLES))])
def listar_roles(
    db: Session = Depends(get_db),
    paginacion: ParametrosPaginacion = Depends(parametros_paginacion),
) -> list[RolRespuesta]:
    return list(rol_repo.listar(db, paginacion))


@roles_router.get("/{rol_id}", response_model=RolRespuesta, dependencies=[Depends(require_permission(PERMISO_ROLES))])
def obtener_rol(rol_id: int, db: Session = Depends(get_db)) -> RolRespuesta:
    return rol_repo.obtener(db, rol_id)


@roles_router.post(
    "", response_model=RolRespuesta, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PERMISO_ROLES))],
)
def crear_rol(datos: RolCrear, db: Session = Depends(get_db)) -> RolRespuesta:
    return rol_repo.crear(db, datos)


@roles_router.put("/{rol_id}", response_model=RolRespuesta, dependencies=[Depends(require_permission(PERMISO_ROLES))])
def actualizar_rol(rol_id: int, datos: RolActualizar, db: Session = Depends(get_db)) -> RolRespuesta:
    return rol_repo.actualizar(db, rol_id, datos)


@roles_router.delete(
    "/{rol_id}", status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(PERMISO_ROLES))],
)
def desactivar_rol(rol_id: int, db: Session = Depends(get_db)) -> None:
    rol_repo.desactivar(db, rol_id)


@roles_router.put(
    "/{rol_id}/permisos", response_model=RolRespuesta,
    dependencies=[Depends(require_permission(PERMISO_ROLES))],
)
def asignar_permisos(
    rol_id: int, datos: AsignarPermisosRequest, db: Session = Depends(get_db)
) -> RolRespuesta:
    rol = rol_repo.obtener(db, rol_id)
    return rol_repo.asignar_permisos(db, rol, datos.codigos_permiso)


# ---- /api/v1/usuarios --------------------------------------------------------

usuarios_router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])


@usuarios_router.get(
    "", response_model=list[UsuarioRespuesta],
    dependencies=[Depends(require_permission(PERMISO_USUARIOS))],
)
def listar_usuarios(
    db: Session = Depends(get_db),
    paginacion: ParametrosPaginacion = Depends(parametros_paginacion),
) -> list[UsuarioRespuesta]:
    usuarios = usuario_repo.listar(db, paginacion)
    return [UsuarioRespuesta.from_modelo(u) for u in usuarios]


@usuarios_router.get(
    "/{usuario_id}", response_model=UsuarioRespuesta,
    dependencies=[Depends(require_permission(PERMISO_USUARIOS))],
)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)) -> UsuarioRespuesta:
    return UsuarioRespuesta.from_modelo(usuario_repo.obtener(db, usuario_id))


@usuarios_router.post(
    "", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PERMISO_USUARIOS))],
)
def crear_usuario(datos: UsuarioCrear, db: Session = Depends(get_db)) -> UsuarioRespuesta:
    return UsuarioRespuesta.from_modelo(usuario_repo.crear(db, datos))


@usuarios_router.put(
    "/{usuario_id}", response_model=UsuarioRespuesta,
    dependencies=[Depends(require_permission(PERMISO_USUARIOS))],
)
def actualizar_usuario(
    usuario_id: int, datos: UsuarioActualizar, db: Session = Depends(get_db)
) -> UsuarioRespuesta:
    return UsuarioRespuesta.from_modelo(usuario_repo.actualizar(db, usuario_id, datos))


@usuarios_router.delete(
    "/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(PERMISO_USUARIOS))],
)
def desactivar_usuario(usuario_id: int, db: Session = Depends(get_db)) -> None:
    usuario_repo.desactivar(db, usuario_id)


@usuarios_router.put(
    "/{usuario_id}/roles", response_model=UsuarioRespuesta,
    dependencies=[Depends(require_permission(PERMISO_USUARIOS))],
)
def asignar_roles(
    usuario_id: int, datos: AsignarRolesRequest, db: Session = Depends(get_db)
) -> UsuarioRespuesta:
    usuario = usuario_repo.obtener(db, usuario_id)
    return UsuarioRespuesta.from_modelo(usuario_repo.asignar_roles(db, usuario, datos.nombres_rol))


# ---- /api/v1/clientes/perfil --------------------------------------------------

clientes_router = APIRouter(prefix="/api/v1/clientes", tags=["clientes"])


@clientes_router.get("/perfil", response_model=ClientePerfilRespuesta)
def obtener_perfil(usuario=Depends(get_current_user), db: Session = Depends(get_db)) -> ClientePerfilRespuesta:
    cliente = service.obtener_perfil_cliente(db, usuario.id)
    return ClientePerfilRespuesta.from_modelo(cliente)


@clientes_router.put("/perfil", response_model=ClientePerfilRespuesta)
def actualizar_perfil(
    datos: ClientePerfilActualizar, usuario=Depends(get_current_user), db: Session = Depends(get_db)
) -> ClientePerfilRespuesta:
    cliente = service.actualizar_perfil_cliente(db, usuario.id, datos)
    return ClientePerfilRespuesta.from_modelo(cliente)


routers = [auth_router, roles_router, usuarios_router, clientes_router]
