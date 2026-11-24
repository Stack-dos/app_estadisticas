from dataclasses import dataclass, field


@dataclass
class JugadorDTO:  # Sale en RegistrarJugadorUseCase.execute()
    nombre_completo: str
    id: int
    anioNacimiento: int | None
    nombre: str = field(default="", compare=False)
    apellido: str = field(default="", compare=False)


@dataclass
class CrearJugadorDTO:  # Entra en RegistrasJugadorUseCase.execute
    nombre: str
    apellido: str
    anioNacimiento: int | None = None


@dataclass
class EditarJugadorDTO:
    """Entra en EditarJugadorUseCase.ejecutar()."""

    idJugador: int
    nombre: str
    apellido: str
    anioNacimiento: int | None = None
