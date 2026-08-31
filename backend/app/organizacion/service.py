from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoError, NoEncontradoError
from app.organizacion.models import Empleado, HorarioSucursal, Sucursal
from app.organizacion.repository import EmpleadoRepository, HorarioRepository, SucursalRepository
from app.organizacion.schemas import EmpleadoActualizar, EmpleadoCrear, HorarioActualizar, HorarioCrear
from app.seguridad import service as seguridad_service

sucursal_repo = SucursalRepository()
horario_repo = HorarioRepository()
empleado_repo = EmpleadoRepository()


def obtener_sucursal(db: Session, sucursal_id: int) -> Sucursal:
    """Para que otros paquetes (p. ej. `inventario`) validen una sucursal
    sin consultar la tabla `sucursal` directamente."""
    return sucursal_repo.obtener(db, sucursal_id)


def obtener_horario_dia(db: Session, sucursal_id: int, dia_semana: int) -> HorarioSucursal | None:
    """Para que `reservas` valide que una franja horaria cae dentro del
    horario de atención de la sucursal, sin consultar horario_sucursal
    directamente."""
    return horario_repo.obtener_por_dia(db, sucursal_id, dia_semana)


def listar_empleados_sucursal(db: Session, sucursal_id: int) -> list[Empleado]:
    """Para que `reservas` notifique a los empleados de una sucursal sin
    consultar la tabla `empleado` directamente."""
    return empleado_repo.listar_por_sucursal(db, sucursal_id)


def obtener_empleado_por_usuario(db: Session, usuario_id: int) -> Empleado | None:
    """Para que `ventas` resuelva el cajero (empleado) a partir del usuario
    logueado al registrar una venta presencial, sin consultar `empleado`
    directamente."""
    return empleado_repo.obtener_por_usuario(db, usuario_id)


def obtener_mi_empleado(db: Session, usuario_id: int) -> Empleado:
    """GET /empleados/yo: para que la caja (Angular) sepa en qué sucursal
    trabaja el cajero logueado, sin necesitar el permiso de administración
    de organizacion.gestionar (ver empleados_router)."""
    empleado = empleado_repo.obtener_por_usuario(db, usuario_id)
    if empleado is None:
        raise NoEncontradoError("Este usuario no tiene un registro de empleado")
    return empleado


def crear_horario(db: Session, sucursal_id: int, datos: HorarioCrear) -> HorarioSucursal:
    sucursal_repo.obtener(db, sucursal_id)  # 404 si no existe / está inactiva

    if horario_repo.obtener_por_dia(db, sucursal_id, datos.dia_semana) is not None:
        raise ConflictoError("Ya existe un horario para ese día en esta sucursal")

    horario = HorarioSucursal(
        sucursal_id=sucursal_id,
        dia_semana=datos.dia_semana,
        hora_apertura=datos.hora_apertura,
        hora_cierre=datos.hora_cierre,
    )
    return horario_repo.crear(db, sucursal_id, horario)


def actualizar_horario(
    db: Session, sucursal_id: int, horario_id: int, datos: HorarioActualizar
) -> HorarioSucursal:
    horario = horario_repo.obtener(db, sucursal_id, horario_id)
    return horario_repo.actualizar(db, horario, datos.hora_apertura, datos.hora_cierre)


def eliminar_horario(db: Session, sucursal_id: int, horario_id: int) -> None:
    horario = horario_repo.obtener(db, sucursal_id, horario_id)
    horario_repo.eliminar(db, horario)


def crear_empleado(db: Session, datos: EmpleadoCrear):
    seguridad_service.obtener_usuario(db, datos.usuario_id)  # valida que el usuario exista

    if empleado_repo.obtener_por_usuario(db, datos.usuario_id) is not None:
        raise ConflictoError("Ese usuario ya es empleado")

    if datos.sucursal_id is not None:
        sucursal_repo.obtener(db, datos.sucursal_id)  # 404 si no existe / está inactiva

    return empleado_repo.crear(db, datos)


def actualizar_empleado(db: Session, empleado_id: int, datos: EmpleadoActualizar):
    if datos.sucursal_id is not None:
        sucursal_repo.obtener(db, datos.sucursal_id)  # 404 si no existe / está inactiva
    return empleado_repo.actualizar(db, empleado_id, datos)
