from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoError
from app.organizacion.models import HorarioSucursal
from app.organizacion.repository import EmpleadoRepository, HorarioRepository, SucursalRepository
from app.organizacion.schemas import EmpleadoActualizar, EmpleadoCrear, HorarioActualizar, HorarioCrear
from app.seguridad import service as seguridad_service

sucursal_repo = SucursalRepository()
horario_repo = HorarioRepository()
empleado_repo = EmpleadoRepository()


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
