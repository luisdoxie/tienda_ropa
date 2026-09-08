from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ParametrosPeriodo, periodo_reportes
from app.core.security import require_permission
from app.reportes import service
from app.reportes.schemas import DashboardRespuesta, ReporteInventarioRespuesta, ReporteReservasRespuesta, ReporteVentasRespuesta

PERMISO_VER = "reportes.ver"
ver_requerido = Depends(require_permission(PERMISO_VER))

router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"], dependencies=[ver_requerido])


@router.get("/ventas", response_model=ReporteVentasRespuesta)
def reporte_ventas(
    periodo: ParametrosPeriodo = Depends(periodo_reportes),
    sucursal_id: int | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    canal: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ReporteVentasRespuesta:
    return service.reporte_ventas(db, periodo, sucursal_id, categoria_id, canal)


@router.get("/inventario", response_model=ReporteInventarioRespuesta)
def reporte_inventario(
    sucursal_id: int | None = Query(default=None), db: Session = Depends(get_db)
) -> ReporteInventarioRespuesta:
    return service.reporte_inventario(db, sucursal_id)


@router.get("/reservas", response_model=ReporteReservasRespuesta)
def reporte_reservas(
    periodo: ParametrosPeriodo = Depends(periodo_reportes),
    sucursal_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ReporteReservasRespuesta:
    return service.reporte_reservas(db, periodo, sucursal_id)


@router.get("/dashboard", response_model=DashboardRespuesta)
def reporte_dashboard(
    periodo: ParametrosPeriodo = Depends(periodo_reportes),
    sucursal_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DashboardRespuesta:
    return service.reporte_dashboard(db, periodo, sucursal_id)


routers = [router]
