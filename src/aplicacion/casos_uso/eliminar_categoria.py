from dominio.exceptions import CategoriaEnUsoError, CategoriaNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


class EliminarCategoriaUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Inicializa el caso de uso para eliminar una categoria del catalogo.

        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias y categorias.
        """
        self.repo = repo

    def ejecutar(self, idCategoria: int) -> bool:
        """
        Elimina una categoria siempre que no este habilitada en ninguna competencia ni tenga inscripciones.

        Args:
            idCategoria (int): ID de la categoria a eliminar.

        Raises:
            CategoriaNoEncontradaError: Si la categoria no existe.
            CategoriaEnUsoError: Si la categoria esta habilitada en alguna competencia o tiene inscripciones.

        Returns:
            bool: True si se elimino correctamente, False si fallo al borrar en el repositorio.
        """
        if not any(c.idCategoria == idCategoria for c in self.repo.obtener_categorias()):
            raise CategoriaNoEncontradaError(f"No existe una categoria con idCategoria={idCategoria}")

        if self.repo.categoria_en_uso(idCategoria):
            raise CategoriaEnUsoError(
                f"No se puede eliminar la categoria (idCategoria={idCategoria}) porque esta en uso en una competencia"
            )

        return self.repo.eliminar_categoria(idCategoria)
