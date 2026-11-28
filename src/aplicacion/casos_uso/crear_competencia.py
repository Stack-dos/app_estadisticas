import logging

from aplicacion.dtos.competencia_dto import CompetenciaDTO, CrearCompetenciaDTO
from dominio.entidades.competencia import Competencia
from dominio.exceptions import CategoriaNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido

# logging de la biblioteca estandar: el correlation_id lo agrega el handler (US-110).
logger = logging.getLogger(__name__)


class CrearCompetenciaUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Funcion que permite inicializar el caso de uso de crear una competencia
        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias
        """
        self.repo = repo

    def ejecutar(self, dto: CrearCompetenciaDTO) -> CompetenciaDTO | None:
        """
        Funcion que permite crear una competencia en la base de datos junto con sus categorias
        habilitadas en una unica transaccion atomica.

        Args:
            dto (CrearCompetenciaDTO): DTO que contiene la informacion de la competencia a crear y
                las categorias que juega (puede ser una lista vacia).

        Raises:
            TypeError: Si algun dato de la competencia tiene un tipo incorrecto (lo lanza la entidad).
            DatoInvalidoError: Si el nombre esta vacio o el año de la competencia no es valido.
            CategoriaNoEncontradaError: Si alguna de las categorias indicadas no existe.

        Returns:
            CompetenciaDTO | None: DTO con la competencia creada, o None si no se pudo guardar
        """
        competencia = Competencia(nombre=dto.nombre, anio=dto.anio, tipo=dto.tipo)
        id_categorias = list(dict.fromkeys(dto.idCategorias))
        if id_categorias:
            existentes = {c.idCategoria for c in self.repo.obtener_categorias()}
            for id_categoria in id_categorias:
                if id_categoria not in existentes:
                    raise CategoriaNoEncontradaError(f"No existe una categoria con idCategoria={id_categoria}")

        resultado = self.repo.guardar_competencia_con_categorias(compe=competencia, idCategorias=id_categorias)
        if resultado is None:
            return None
        logger.info(
            "Competencia creada", extra={"evento": "competencia_creada", "id_competencia": resultado.idCompetencia}
        )
        return CompetenciaDTO(
            idCompetencia=id_persistido(resultado.idCompetencia, "Competencia"),
            nombre=resultado.nombre,
            anio=resultado.anio,
            tipo=resultado.tipo,
        )
