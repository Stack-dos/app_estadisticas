from aplicacion.dtos.competencia_dto import InscripcionDTO
from dominio.exceptions import ListaBuenaFeNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido


class ListarInscripcionesClubUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Funcion que permite inicializar el caso de uso de listar las inscripciones de un club
        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias, categorias e inscripciones
        """
        self.repo = repo

    def ejecutar(self, idClub: int) -> list[InscripcionDTO]:
        """
        Funcion que permite listar las inscripciones de un club, junto con el id de la lista de buena fe
        de cada una (es el dato que hace falta para administrar esa lista).

        Args:
            idClub (int): ID del club del cual se quieren listar las inscripciones

        Raises:
            ListaBuenaFeNoEncontradaError: Si una inscripcion no tiene lista de buena fe (no deberia pasar:
                la relacion es 1:1 y se crean juntas).

        Returns:
            list[InscripcionDTO]: Lista de inscripciones. Lista vacia si el club no tiene ninguna.
        """
        resultado = []
        for inscripcion in self.repo.obtener_inscripciones_por_club(idClub):
            id_inscripcion = id_persistido(inscripcion.idInscripcion, "Inscripcion")
            lista = self.repo.obtener_lista_por_inscripcion(id_inscripcion)
            if lista is None:
                raise ListaBuenaFeNoEncontradaError(
                    f"La inscripcion (idInscripcion={id_inscripcion}) no tiene lista de buena fe"
                )
            resultado.append(
                InscripcionDTO(
                    idInscripcion=id_inscripcion,
                    idClub=inscripcion.idClub,
                    idCategoria=inscripcion.idCategoria,
                    idCompetencia=inscripcion.idCompetencia,
                    idListaBuenaFe=id_persistido(lista.idListaBuenaFe, "ListaBuenaFe"),
                )
            )
        return resultado
