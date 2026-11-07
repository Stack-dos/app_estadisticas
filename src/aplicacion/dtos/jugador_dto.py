from dataclasses import dataclass


@dataclass
class JugadorDTO:  # Sale en RegistrarJugadorUseCase.execute()
    nombre_completo: str
    id: int
    anioNacimiento: int | None


@dataclass
class CrearJugadorDTO:  # Entra en RegistrasJugadorUseCase.execute
    nombre: str
    apellido: str
    anioNacimiento: int | None = None
