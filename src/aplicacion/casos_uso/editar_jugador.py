import logging

from aplicacion.dtos.jugador_dto import EditarJugadorDTO, JugadorDTO
from dominio.entidades.jugador import Jugador
from dominio.exceptions import JugadorNoEncontradoError
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido

# logging de la biblioteca estandar: el correlation_id lo agrega el handler (US-110).
logger = logging.getLogger(__name__)


class EditarJugadorUseCase:
    """Actualiza los datos basicos (nombre, apellido y año de nacimiento) de un jugador."""

    def __init__(self, repo: JugadorRepositorio):
        """Inicializa el caso de uso con el repositorio de jugadores.

        Args:
            repo (JugadorRepositorio): Repositorio de jugadores.
        """
        self.repo = repo

    def ejecutar(self, datos: EditarJugadorDTO) -> JugadorDTO | None:
        """Valida y persiste los nuevos datos de un jugador existente.

        Args:
            datos (EditarJugadorDTO): ID del jugador y nuevos valores.

        Raises:
            JugadorNoEncontradoError: Si no existe un jugador con ese ID.
            DatoInvalidoError: Si el nombre/apellido quedan vacios o el año esta fuera de rango.

        Returns:
            JugadorDTO | None: El jugador actualizado, o None si fallo al guardar en la base.
        """
        if self.repo.buscar_por_id(datos.idJugador) is None:
            raise JugadorNoEncontradoError(f"No existe un jugador con idJugador={datos.idJugador}")

        jugador = Jugador(
            nombre=datos.nombre,
            apellido=datos.apellido,
            anioNacimiento=datos.anioNacimiento,
            idJugador=datos.idJugador,
        )
        actualizado = self.repo.actualizar(jugador)
        if actualizado is None:
            return None
        logger.info("Jugador editado", extra={"evento": "jugador_actualizado", "id_jugador": actualizado.idJugador})
        return JugadorDTO(
            nombre_completo=actualizado.nombre_completo,
            id=id_persistido(actualizado.idJugador, "Jugador"),
            anioNacimiento=actualizado.anioNacimiento,
            nombre=actualizado.nombre,
            apellido=actualizado.apellido,
        )
