from aplicacion.casos_uso.agregar_jugador_lista import AgregarJugadorAListaBuenaFeUseCase
from aplicacion.dtos.lista_buena_fe_dto import (
    AgregarJugadoresListaDTO,
    AgregarJugadorListaDTO,
    JugadorRechazadoDTO,
    ResultadoAgregarJugadoresDTO,
)
from dominio.exceptions import DatoInvalidoError, ErrorDeDominio


class AgregarJugadoresAListaBuenaFeUseCase:
    """Habilita varios jugadores a la vez en una lista de buena fe (US-113).

    Decision (2026-11-27): NO es "todo o nada". Se agregan los jugadores validos y se informa cuales no
    entraron y por que: al armar una lista, un jugador que ya estaba no tiene por que frenar al resto.
    Cada jugador pasa por las mismas reglas que el alta individual (`AgregarJugadorAListaBuenaFeUseCase`).
    """

    def __init__(self, agregar_uno: AgregarJugadorAListaBuenaFeUseCase):
        """
        Args:
            agregar_uno (AgregarJugadorAListaBuenaFeUseCase): El alta individual, que tiene las reglas.
        """
        self.agregar_uno = agregar_uno

    def ejecutar(self, dto: AgregarJugadoresListaDTO) -> ResultadoAgregarJugadoresDTO:
        """
        Intenta habilitar a cada jugador y junta el resultado.

        Args:
            dto (AgregarJugadoresListaDTO): La inscripcion y los ids de los jugadores a habilitar.

        Raises:
            DatoInvalidoError: Si no se eligio ningun jugador.

        Returns:
            ResultadoAgregarJugadoresDTO: Ids agregados y jugadores rechazados con el motivo.
        """
        ids = list(dict.fromkeys(dto.idJugadores))  # sin repetidos, en el orden elegido
        if not ids:
            raise DatoInvalidoError("Elegí al menos un jugador para agregar a la lista.")

        resultado = ResultadoAgregarJugadoresDTO()
        for id_jugador in ids:
            try:
                agregado = self.agregar_uno.ejecutar(
                    AgregarJugadorListaDTO(idInscripcion=dto.idInscripcion, idJugador=id_jugador)
                )
            except ErrorDeDominio as e:
                resultado.rechazados.append(JugadorRechazadoDTO(idJugador=id_jugador, motivo=str(e)))
                continue
            if agregado is None:
                resultado.rechazados.append(
                    JugadorRechazadoDTO(idJugador=id_jugador, motivo="No se pudo guardar en la base.")
                )
            else:
                resultado.agregados.append(id_jugador)
        return resultado
