"""Excepciones de dominio para la aplicacion de estadisticas."""


class ErrorDeDominio(Exception):
    """Clase base para todas las excepciones de dominio."""

    pass


class ClubNoEncontradoError(ErrorDeDominio):
    """Se lanza cuando se quiere trabajar con un club inexistente"""

    pass


class JugadorNoEncontradoError(ErrorDeDominio):
    """Se lanza cuando se quiere trabajar con un jugador inexistente"""

    pass


class CompetenciaNoEncontradaError(ErrorDeDominio):
    """Se lanza cuando se quiere trabajar con una competencia inexistente"""

    pass


class CategoriaNoEncontradaError(ErrorDeDominio):
    """Se lanza cuando se quiere trabajar con una categoria inexistente"""

    pass


class InscripcionDuplicadaError(ErrorDeDominio):
    """Se lanza cuando un club ya esta inscripto en la misma competencia y categoria."""

    pass


class CategoriaDuplicadaError(ErrorDeDominio):
    """Se lanza cuando se intenta crear una categoria con un nombre que ya existe."""

    pass


class InscripcionNoEncontradaError(ErrorDeDominio):
    """Se lanza cuando se quiere trabajar con una inscripcion inexistente."""

    pass


class ListaBuenaFeNoEncontradaError(ErrorDeDominio):
    """Se lanza cuando una inscripcion no tiene su lista de buena fe (deberia haber siempre una, relacion 1:1)."""

    pass


class JugadorYaEnListaError(ErrorDeDominio):
    """Se lanza cuando se intenta agregar a una lista de buena fe un jugador que ya esta en ella."""

    pass


class JugadorNoPerteneceAlClubError(ErrorDeDominio):
    """Se lanza cuando se intenta habilitar en una lista un jugador que no tiene vinculo vigente con el club."""

    pass


class JugadorNoEstaEnListaError(ErrorDeDominio):
    """Se lanza cuando se intenta quitar de una lista de buena fe a un jugador que no esta en ella."""

    pass


class JugadorSinVinculoActivoError(ErrorDeDominio):
    """Se lanza cuando se intenta desvincular de su club a un jugador que no tiene un vinculo vigente."""

    pass


class VinculoSuperpuestoError(ErrorDeDominio):
    """Se lanza cuando un vinculo nuevo empieza antes de que termine uno anterior del mismo jugador."""

    pass


class DatoInvalidoError(ErrorDeDominio, ValueError):
    """Se lanza cuando un dato tiene un valor invalido (vacio, fuera de rango, incoherente con otro).

    Hereda tambien de `ValueError`: el codigo que ya capturaba `ValueError` sigue funcionando, y al ser
    una `ErrorDeDominio` la CLI la muestra como un mensaje amigable, sin traceback.
    """

    pass


class UsuarioNoEncontradoError(ErrorDeDominio):
    """Se lanza cuando se intenta usar un usuario inexistente"""

    pass


class CredencialesInvalidasError(ErrorDeDominio):
    """Se lanza cuando se intenta acceder con contraseña incorrecta"""

    pass


class EmailYaRegistradoError(ErrorDeDominio):
    """Se lanza cuando se intenta registrar un usuario con un email que ya esta en uso."""

    pass


class ClubYaExisteError(ErrorDeDominio):
    """Se lanza cuando se intenta crear un club con un nombre que ya existe (sin distinguir mayusculas)."""

    pass


class VinculoActivoExistenteError(ErrorDeDominio):
    """Se lanza cuando se intenta registrar un jugador en un club nuevo cuando todavia tiene un club."""

    pass


class CategoriaNoHabilitadaError(ErrorDeDominio):
    """Se lanza cuando se inscribe a un club en una categoria que la competencia no juega (US-107)."""

    pass


class CategoriaYaHabilitadaError(ErrorDeDominio):
    """Se lanza cuando se habilita en una competencia una categoria que ya juega (US-107)."""

    pass


class CategoriaConInscripcionesError(ErrorDeDominio):
    """Se lanza cuando se quita de una competencia una categoria que tiene clubes inscriptos (US-107)."""

    pass


class CompetenciaEnUsoError(ErrorDeDominio):
    """Se lanza cuando se intenta eliminar una competencia que tiene inscripciones o partidos (US-107)."""

    pass


class CategoriaEnUsoError(ErrorDeDominio):
    """Se lanza cuando se intenta eliminar una categoria que esta habilitada o en uso (US-107)."""

    pass


class InscripcionEnUsoError(ErrorDeDominio):
    """Se lanza cuando se intenta dar de baja una inscripcion de un club con partidos cargados (US-107)."""

    pass


class JugadorEnUsoError(ErrorDeDominio):
    """Se lanza cuando se intenta eliminar un jugador con partidos cargados o en listas de buena fe (US-112)."""

    pass
