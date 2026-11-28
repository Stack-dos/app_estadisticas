from aplicacion.dtos.categoria_dto import CategoriaDTO
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido


class ListarCategoriasUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Funcion que permite inicializar el caso de uso de listar las categorias
        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias, categorias e inscripciones
        """
        self.repo = repo

    def ejecutar(self) -> list[CategoriaDTO]:
        """
        Funcion que permite listar todas las categorias existentes

        Returns:
            list[CategoriaDTO]: Lista de categorias. Lista vacia si todavia no hay ninguna.
        """
        return [
            CategoriaDTO(idCategoria=id_persistido(c.idCategoria, "Categoria"), nombre=c.nombre)
            for c in self.repo.obtener_categorias()
        ]
