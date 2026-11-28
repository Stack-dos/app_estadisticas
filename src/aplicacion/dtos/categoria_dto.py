from dataclasses import dataclass


@dataclass
class CrearCategoriaDTO:
    """Entra a CrearCategoriaUseCase.ejecutar()"""

    nombre: str


@dataclass
class CategoriaDTO:
    """Sale de CrearCategoriaUseCase / ListarCategoriasUseCase"""

    idCategoria: int
    nombre: str
