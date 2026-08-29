from dataclasses import dataclass

from fastapi import Query


@dataclass
class ParametrosPaginacion:
    pagina: int
    tamanio: int

    @property
    def offset(self) -> int:
        return (self.pagina - 1) * self.tamanio


def parametros_paginacion(
    pagina: int = Query(default=1, ge=1),
    tamanio: int = Query(default=20, ge=1, le=100),
) -> ParametrosPaginacion:
    return ParametrosPaginacion(pagina=pagina, tamanio=tamanio)
