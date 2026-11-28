from aplicacion.dtos.categoria_dto import CategoriaDTO
from dominio.exceptions import CompetenciaNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido


class ListarCategoriasDeCompetenciaUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Inicializa el caso de uso para listar las categorias habilitadas en una competencia.

        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias y categorias.
        """
        self.repo = repo

    def ejecutar(self, idCompetencia: int) -> list[CategoriaDTO]:
        """
        Devuelve las categorias habilitadas para una competencia.

        Args:
            idCompetencia (int): ID de la competencia a consultar.

        Raises:
            CompetenciaNoEncontradaError: Si la competencia no existe.

        Returns:
            list[CategoriaDTO]: Categorias habilitadas (lista vacia si aun no tiene ninguna).
        """
        if self.repo.buscar_competencia_por_id(idCompetencia) is None:
            raise CompetenciaNoEncontradaError(f"No existe una competencia con idCompetencia={idCompetencia}")

        return [
            CategoriaDTO(idCategoria=id_persistido(c.idCategoria, "Categoria"), nombre=c.nombre)
            for c in self.repo.obtener_categorias_de_competencia(idCompetencia)
        ]
