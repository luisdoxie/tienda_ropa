from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Error de regla de negocio. No expone detalles de implementación."""

    def __init__(self, mensaje: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.mensaje = mensaje
        self.status_code = status_code
        super().__init__(mensaje)


class NoEncontradoError(DomainError):
    def __init__(self, mensaje: str = "Recurso no encontrado") -> None:
        super().__init__(mensaje, status_code=status.HTTP_404_NOT_FOUND)


class ConflictoError(DomainError):
    def __init__(self, mensaje: str = "Conflicto con el estado actual del recurso") -> None:
        super().__init__(mensaje, status_code=status.HTTP_409_CONFLICT)


class PermisoDenegadoError(DomainError):
    def __init__(self, mensaje: str = "No tiene permiso para realizar esta acción") -> None:
        super().__init__(mensaje, status_code=status.HTTP_403_FORBIDDEN)


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensaje})
