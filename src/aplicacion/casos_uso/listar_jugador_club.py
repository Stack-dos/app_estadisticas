from aplicacion.dtos.jugador_dto import JugadorDTO
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido


class ListarJugadoresClubUseCase:
    def __init__(self, repo: JugadorRepositorio):
        self.repo = repo

    def ejecutar(self, idClub: int) -> list[JugadorDTO]:
        """
        Funcion que permite listar los jugadores de un club

        Args:
            idClub (int): ID del club del cual se quieren listar los jugadores

        Returns:
            list[JugadorDTO]: Lista de jugadores del club. Lista vacia si el club no tiene jugadores.
        """
        # La interfaz del repositorio admite None; sin este "or []" el for de abajo se rompería.
        lista_jugadores = self.repo.buscar_por_club(idClub=idClub) or []
        return [
            JugadorDTO(
                nombre_completo=j.nombre_completo,
                id=id_persistido(j.idJugador, "Jugador"),
                anioNacimiento=j.anioNacimiento,
                nombre=j.nombre,
                apellido=j.apellido,
            )
            for j in lista_jugadores
        ]
