import logging

from aplicacion.dtos.jugador_dto import CrearJugadorDTO, JugadorDTO
from dominio.entidades.jugador import Jugador
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido

# logging de la biblioteca estandar: el correlation_id lo agrega el handler (US-110).
logger = logging.getLogger(__name__)


class RegistrarJugadorUseCase:
    def __init__(self, jugador_repo: JugadorRepositorio):
        self.repo = jugador_repo

    def ejecutar(self, datos: CrearJugadorDTO) -> JugadorDTO | None:
        """
        Funcion que permite registrar un jugador nuevo

        Args:
            datos (CrearJugadorDTO): DTO con los datos del jugador a registrar

        Returns:
            JugadorDTO | None: DTO con el jugador registrado, o None si no se pudo guardar
        """
        jug = Jugador(nombre=datos.nombre, apellido=datos.apellido, anioNacimiento=datos.anioNacimiento)

        resultado = self.repo.guardar(jugador=jug)
        if resultado is None:
            return None
        logger.info("Jugador creado", extra={"evento": "jugador_creado", "id_jugador": resultado.idJugador})
        return JugadorDTO(
            nombre_completo=resultado.nombre_completo,
            id=id_persistido(resultado.idJugador, "Jugador"),
            anioNacimiento=resultado.anioNacimiento,
            nombre=resultado.nombre,
            apellido=resultado.apellido,
        )
