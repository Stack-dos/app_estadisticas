from aplicacion.dtos.competencia_dto import CompetenciaDTO
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido


class ListarCompetenciasUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Funcion que permite inicializar el caso de uso de listar las competencias
        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias, categorias e inscripciones
        """
        self.repo = repo

    def ejecutar(self) -> list[CompetenciaDTO]:
        """
        Funcion que permite listar todas las competencias existentes

        Returns:
            list[CompetenciaDTO]: Lista de competencias. Lista vacia si todavia no hay ninguna.
        """
        return [
            CompetenciaDTO(
                idCompetencia=id_persistido(c.idCompetencia, "Competencia"),
                nombre=c.nombre,
                anio=c.anio,
                tipo=c.tipo,
            )
            for c in self.repo.obtener_todas_competencias()
        ]
