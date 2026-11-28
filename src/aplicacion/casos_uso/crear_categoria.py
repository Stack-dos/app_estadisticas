import logging

from aplicacion.dtos.categoria_dto import CategoriaDTO, CrearCategoriaDTO
from dominio.entidades.competencia import Categoria
from dominio.exceptions import CategoriaDuplicadaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido

# logging de la biblioteca estandar: el correlation_id lo agrega el handler (US-110).
logger = logging.getLogger(__name__)


class CrearCategoriaUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Funcion que permite inicializar el caso de uso de crear una categoria
        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias, categorias e inscripciones
        """
        self.repo = repo

    def ejecutar(self, dto: CrearCategoriaDTO) -> CategoriaDTO | None:
        """
        Funcion que permite crear una categoria (ej. "U21"). No se permiten nombres repetidos, sin importar
        mayusculas/minusculas ni espacios de los extremos ("u21 " es la misma categoria que "U21").

        Args:
            dto (CrearCategoriaDTO): DTO con el nombre de la categoria a crear

        Raises:
            TypeError: Si el nombre no es un texto (lo lanza la entidad).
            CategoriaDuplicadaError: Si ya existe una categoria con ese nombre.

        Returns:
            CategoriaDTO | None: DTO con la categoria creada, o None si no se pudo guardar
        """
        categoria = Categoria(nombre=dto.nombre)

        nombre_normalizado = categoria.nombre.strip().lower()
        if any(c.nombre.strip().lower() == nombre_normalizado for c in self.repo.obtener_categorias()):
            raise CategoriaDuplicadaError(f"Ya existe una categoria con el nombre '{categoria.nombre.strip()}'")

        resultado = self.repo.guardar_categoria(cat=categoria)
        if resultado is None:
            return None
        logger.info("Categoria creada", extra={"evento": "categoria_creada", "id_categoria": resultado.idCategoria})
        return CategoriaDTO(idCategoria=id_persistido(resultado.idCategoria, "Categoria"), nombre=resultado.nombre)
