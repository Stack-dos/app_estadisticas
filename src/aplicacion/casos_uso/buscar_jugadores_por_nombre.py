from aplicacion.dtos.jugador_dto import JugadorDTO
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido


class BuscarJugadoresPorNombreUseCase:
    """Busca jugadores por nombre o apellido en toda la base (sin filtrar por club)."""

    def __init__(self, repo: JugadorRepositorio):
        """Inicializa el caso de uso con el repositorio de jugadores.

        Args:
            repo (JugadorRepositorio): Repositorio de jugadores.
        """
        self.repo = repo

    def ejecutar(self, texto: str) -> list[JugadorDTO]:
        """Devuelve los jugadores cuyo nombre o apellido coincida con `texto`.

        Args:
            texto (str): Texto a buscar (si esta vacio o son solo espacios, devuelve lista vacia).

        Returns:
            list[JugadorDTO]: Jugadores coincidentes listos para mostrar en pantalla.
        """
        consulta = texto.strip()
        if not consulta:
            return []

        return [
            JugadorDTO(
                nombre_completo=j.nombre_completo,
                id=id_persistido(j.idJugador, "Jugador"),
                anioNacimiento=j.anioNacimiento,
                nombre=j.nombre,
                apellido=j.apellido,
            )
            for j in self.repo.buscar_por_nombre(consulta)
        ]
