"""Tests de integracion de punta a punta de los casos de uso, con repositorios reales y una base en archivo.

Reemplazan a `test_cli_e2e.py` (borrado con la CLI en la US-105): prueban lo mismo pero sin interfaz,
llamando a los casos de uso como lo hacen las pantallas. Es lo unico que no cubren los otros tests: los
unitarios de casos de uso usan repositorios falsos, y los de repositorios no pasan por los casos de uso.

Cada `abrir()` simula un arranque de la app: conexion nueva + `inicializar_schema()` sobre el mismo archivo.
"""

import sqlite3
from collections.abc import Callable
from types import SimpleNamespace

import pytest

import config.rutas as r
from aplicacion.casos_uso.agregar_jugador_lista import AgregarJugadorAListaBuenaFeUseCase
from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_categoria import CrearCategoriaUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.crear_competencia import CrearCompetenciaUseCase
from aplicacion.casos_uso.desvincular_jugador_club import DesvincularJugadorDeClubUseCase
from aplicacion.casos_uso.inscribir_club_competencia import InscribirClubEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.casos_uso.quitar_jugador_lista import QuitarJugadorDeListaBuenaFeUseCase
from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.casos_uso.vincular_jugador_club import VincularJugadorAClubUseCase
from aplicacion.dtos.categoria_dto import CrearCategoriaDTO
from aplicacion.dtos.club_dto import CrearClubDTO, DesvincularJugadorDTO, VincularJugadorClubDTO
from aplicacion.dtos.competencia_dto import CrearCompetenciaDTO, InscribirClubDTO
from aplicacion.dtos.jugador_dto import CrearJugadorDTO
from aplicacion.dtos.lista_buena_fe_dto import AgregarJugadorListaDTO, QuitarJugadorListaDTO
from dominio.exceptions import ErrorDeDominio
from infraestructura.persistencia.database_manager import SQLiteManager
from infraestructura.repositorios.sqlite_club_repositorio import SqliteClubRepositorio
from infraestructura.repositorios.sqlite_competencia_repositorio import SqliteCompetenciaRepositorio
from infraestructura.repositorios.sqlite_jugador_repositorio import SqliteJugadorRepositorio
from infraestructura.repositorios.sqlite_partido_repositorio import SqlitePartidoRepositorio

ID_DT = 1  # el entrenador que crea los clubes (CrearClubUseCase lo vincula en usuarioClub)


def _casos_de_uso(conexion: sqlite3.Connection) -> SimpleNamespace:
    """Arma los casos de uso sobre una conexion, igual que lo hara el composition root de la GUI."""
    # OR IGNORE: cada abrir() de un mismo archivo pasa por aca, y el usuario ya puede existir
    conexion.execute(
        "INSERT OR IGNORE INTO usuario (idUsuario, nombre, email, contrasenia) VALUES (?, 'DT', 'dt@test.com', 'x')",
        (ID_DT,),
    )
    conexion.commit()
    club = SqliteClubRepositorio(conexion)
    jugador = SqliteJugadorRepositorio(conexion)
    competencia = SqliteCompetenciaRepositorio(conexion)
    return SimpleNamespace(
        crear_club=CrearClubUseCase(club),
        listar_clubes=ListarClubesUsuarioUseCase(club),
        cambiar_club_activo=CambiarClubActivoUseCase(club),
        registrar_jugador=RegistrarJugadorUseCase(jugador),
        vincular=VincularJugadorAClubUseCase(jugador, club),
        desvincular=DesvincularJugadorDeClubUseCase(jugador),
        listar_jugadores=ListarJugadoresClubUseCase(jugador),
        crear_competencia=CrearCompetenciaUseCase(competencia),
        crear_categoria=CrearCategoriaUseCase(competencia),
        listar_categorias=ListarCategoriasUseCase(competencia),
        listar_competencias=ListarCompetenciasUseCase(competencia),
        inscribir=InscribirClubEnCompetenciaUseCase(competencia, club),
        listar_inscripciones=ListarInscripcionesClubUseCase(competencia),
        agregar_a_lista=AgregarJugadorAListaBuenaFeUseCase(competencia, jugador),
        listar_lista=ListarListaBuenaFeUseCase(competencia, jugador),
        quitar_de_lista=QuitarJugadorDeListaBuenaFeUseCase(competencia),
        listar_partidos=ListarPartidosPorClubUseCase(SqlitePartidoRepositorio(conexion)),
    )


@pytest.fixture
def abrir(tmp_path):
    """Devuelve `abrir() -> casos de uso` sobre un archivo temporal (no toca estadisticas.db)."""
    db_path = str(tmp_path / "flujo.db")
    managers: list[SQLiteManager] = []

    def _abrir() -> SimpleNamespace:
        manager = SQLiteManager(db_path, r.SCHEMA_SQL, r.VISTA_SQL)
        conexion = manager.connect()
        manager.inicializar_schema()
        managers.append(manager)
        return _casos_de_uso(conexion)

    _abrir.db_path = db_path  # type: ignore[attr-defined]
    yield _abrir
    for manager in managers:
        manager.close_connection()


@pytest.fixture
def uc(abrir):
    return abrir()


def _inscribir_club_1(uc: SimpleNamespace) -> None:
    uc.crear_club.ejecutar(CrearClubDTO(nombre="Atenas"), ID_DT)
    uc.registrar_jugador.ejecutar(CrearJugadorDTO(nombre="A", apellido="B", anioNacimiento=1990))
    uc.crear_competencia.ejecutar(CrearCompetenciaDTO(nombre="Liga", anio=2026))
    uc.crear_categoria.ejecutar(CrearCategoriaDTO(nombre="U21"))
    uc.inscribir.ejecutar(InscribirClubDTO(idClub=1, idCategoria=1, idCompetencia=1, fechaPresentacion="2026-03-01"))


def test_los_datos_persisten_entre_arranques(abrir):
    """Regresion: schema.sql empezaba con DROP TABLE y cada arranque borraba todos los datos."""
    assert abrir().crear_club.ejecutar(CrearClubDTO(nombre="Atenas"), ID_DT).idClub == 1

    club = abrir().crear_club.ejecutar(CrearClubDTO(nombre="Instituto"), ID_DT)

    assert club.idClub == 2  # si la base se hubiera borrado, el id volveria a ser 1


def test_un_club_creado_aparece_en_mis_clubes_y_se_puede_activar(uc):
    """Regresion (fix US-106): CrearClubUseCase no vinculaba al usuario y el club nunca aparecia en su lista."""
    club = uc.crear_club.ejecutar(CrearClubDTO(nombre="Atenas"), ID_DT)

    assert uc.listar_clubes.ejecutar(ID_DT) == [club]
    assert uc.cambiar_club_activo.ejecutar(ID_DT, club.idClub) == club


def test_flujo_completo_de_punta_a_punta(uc):
    assert uc.crear_club.ejecutar(CrearClubDTO(nombre="Atenas"), ID_DT).idClub == 1
    jugador = uc.registrar_jugador.ejecutar(CrearJugadorDTO(nombre="Manu", apellido="Ginobili", anioNacimiento=1977))
    assert (jugador.id, jugador.nombre_completo) == (1, "Manu Ginobili")

    vinculo = uc.vincular.ejecutar(VincularJugadorClubDTO(idJugador=1, idClub=1, fechaDesde="2026-01-05"))
    assert (vinculo.idJugador, vinculo.idClub, vinculo.fechaDesde) == (1, 1, "2026-01-05")
    assert [j.nombre_completo for j in uc.listar_jugadores.ejecutar(1)] == ["Manu Ginobili"]

    competencia = uc.crear_competencia.ejecutar(CrearCompetenciaDTO(nombre="Liga", anio=2026, tipo="PROVINCIAL"))
    assert (competencia.idCompetencia, competencia.nombre, competencia.anio) == (1, "Liga", 2026)
    assert uc.crear_categoria.ejecutar(CrearCategoriaDTO(nombre="U21")).idCategoria == 1
    assert [c.nombre for c in uc.listar_categorias.ejecutar()] == ["U21"]
    assert [c.nombre for c in uc.listar_competencias.ejecutar()] == ["Liga"]

    inscripcion = uc.inscribir.ejecutar(
        InscribirClubDTO(idClub=1, idCategoria=1, idCompetencia=1, fechaPresentacion="2026-03-01")
    )
    assert (inscripcion.idInscripcion, inscripcion.idListaBuenaFe) == (1, 1)
    assert len(uc.listar_inscripciones.ejecutar(1)) == 1

    # la lista de buena fe arranca vacia, se habilita al jugador (que juega en el club) y aparece en la lista
    assert uc.listar_lista.ejecutar(1) == []
    habilitado = uc.agregar_a_lista.ejecutar(AgregarJugadorListaDTO(idInscripcion=1, idJugador=1))
    assert (habilitado.idJugador, habilitado.idListaBuenaFe, habilitado.idInscripcion) == (1, 1, 1)
    assert [j.nombre_completo for j in uc.listar_lista.ejecutar(1)] == ["Manu Ginobili"]

    # se deshace la habilitacion y la lista vuelve a quedar vacia
    uc.quitar_de_lista.ejecutar(QuitarJugadorListaDTO(idInscripcion=1, idJugador=1))
    assert uc.listar_lista.ejecutar(1) == []

    assert uc.listar_partidos.ejecutar(1) == []


def test_un_jugador_puede_cambiar_de_club_sin_pisar_el_periodo_anterior(uc):
    uc.crear_club.ejecutar(CrearClubDTO(nombre="Atenas"), ID_DT)
    uc.crear_club.ejecutar(CrearClubDTO(nombre="Instituto"), ID_DT)
    uc.registrar_jugador.ejecutar(CrearJugadorDTO(nombre="Manu", apellido="Ginobili", anioNacimiento=1977))
    uc.vincular.ejecutar(VincularJugadorClubDTO(idJugador=1, idClub=1, fechaDesde="2026-01-01"))

    # se lo da de baja: deja de figurar en el club 1
    vinculo = uc.desvincular.ejecutar(DesvincularJugadorDTO(idJugador=1, fechaHasta="2026-06-30"))
    assert (vinculo.idClub, vinculo.fechaDesde, vinculo.fechaHasta) == (1, "2026-01-01", "2026-06-30")
    assert uc.listar_jugadores.ejecutar(1) == []

    # el vinculo nuevo no puede empezar antes de que termine el anterior...
    with pytest.raises(ErrorDeDominio, match="antes de que termine el anterior"):
        uc.vincular.ejecutar(VincularJugadorClubDTO(idJugador=1, idClub=2, fechaDesde="2026-06-01"))

    # ...pero si despues, y entonces pasa a figurar en el club 2
    uc.vincular.ejecutar(VincularJugadorClubDTO(idJugador=1, idClub=2, fechaDesde="2026-07-01"))
    assert [j.nombre_completo for j in uc.listar_jugadores.ejecutar(2)] == ["Manu Ginobili"]


def test_listar_partidos_trae_los_nombres_de_los_clubes_y_de_la_competencia(abrir):
    uc = abrir()
    uc.crear_club.ejecutar(CrearClubDTO(nombre="Atenas"), ID_DT)
    uc.crear_club.ejecutar(CrearClubDTO(nombre="Instituto"), ID_DT)
    uc.crear_competencia.ejecutar(CrearCompetenciaDTO(nombre="Liga Provincial", anio=2026))
    # todavia no hay un caso de uso para cargar partidos (US-108): se inserta directo en la base
    conexion = sqlite3.connect(abrir.db_path)
    conexion.execute(
        "INSERT INTO partido (fecha, estadio, idCompetencia, idClubLocal, idClubVisitante) VALUES (?, ?, ?, ?, ?)",
        ("2026-05-21", "Cancha Atenas", 1, 1, 2),
    )
    conexion.commit()
    conexion.close()

    [partido] = uc.listar_partidos.ejecutar(2)  # el club 2 jugo de visitante

    assert (partido.clubLocal, partido.clubVisitante) == ("Atenas", "Instituto")
    assert (partido.competencia, partido.anioCompetencia) == ("Liga Provincial", 2026)
    assert (partido.estadio, partido.fecha) == ("Cancha Atenas", "2026-05-21")


def _club_atenas_e_instituto_con_jugador_en_atenas(uc: SimpleNamespace) -> None:
    uc.crear_club.ejecutar(CrearClubDTO(nombre="Atenas"), ID_DT)
    uc.crear_club.ejecutar(CrearClubDTO(nombre="Instituto"), ID_DT)
    uc.registrar_jugador.ejecutar(CrearJugadorDTO(nombre="A", apellido="B", anioNacimiento=1990))
    uc.vincular.ejecutar(VincularJugadorClubDTO(idJugador=1, idClub=1, fechaDesde="2026-01-01"))


def _sin_preparacion(uc: SimpleNamespace) -> None:
    pass


@pytest.mark.parametrize(
    "preparacion, accion, mensaje",
    [
        pytest.param(
            _sin_preparacion,
            lambda uc: uc.vincular.ejecutar(VincularJugadorClubDTO(idJugador=99, idClub=1, fechaDesde="2026-01-01")),
            "No existe un jugador con idJugador=99",
            id="jugador inexistente",
        ),
        pytest.param(
            _club_atenas_e_instituto_con_jugador_en_atenas,
            lambda uc: uc.vincular.ejecutar(VincularJugadorClubDTO(idJugador=1, idClub=2, fechaDesde="2026-02-01")),
            "tiene un club activo",
            id="jugador que ya tiene club activo",
        ),
        pytest.param(
            lambda uc: uc.crear_categoria.ejecutar(CrearCategoriaDTO(nombre="U21")),
            lambda uc: uc.crear_categoria.ejecutar(CrearCategoriaDTO(nombre=" u21")),
            "Ya existe una categoria",
            id="categoria repetida",
        ),
        pytest.param(
            _sin_preparacion,
            lambda uc: uc.agregar_a_lista.ejecutar(AgregarJugadorListaDTO(idInscripcion=7, idJugador=1)),
            "No existe una inscripcion con idInscripcion=7",
            id="lista de una inscripcion inexistente",
        ),
        pytest.param(
            _inscribir_club_1,
            lambda uc: uc.agregar_a_lista.ejecutar(AgregarJugadorListaDTO(idInscripcion=1, idJugador=1)),
            "no tiene un vinculo vigente con el club",
            id="jugador que no juega en el club de la inscripcion",
        ),
        pytest.param(
            _sin_preparacion,
            lambda uc: uc.crear_competencia.ejecutar(CrearCompetenciaDTO(nombre="Vieja", anio=1900)),
            "Año debe ser mayor que 1900",
            id="anio de competencia invalido",
        ),
        pytest.param(
            _sin_preparacion,
            lambda uc: uc.crear_club.ejecutar(CrearClubDTO(nombre=""), ID_DT),
            "El nombre del club no puede estar vacio",
            id="club sin nombre",
        ),
        pytest.param(
            _sin_preparacion,
            lambda uc: uc.registrar_jugador.ejecutar(CrearJugadorDTO(nombre="A", apellido="B", anioNacimiento=3000)),
            "El año de nacimiento debe estar entre",
            id="anio de nacimiento imposible",
        ),
        pytest.param(
            lambda uc: uc.registrar_jugador.ejecutar(CrearJugadorDTO(nombre="A", apellido="B", anioNacimiento=1990)),
            lambda uc: uc.desvincular.ejecutar(DesvincularJugadorDTO(idJugador=1, fechaHasta="2026-06-30")),
            "no tiene un club activo",
            id="desvincular a un jugador sin club",
        ),
        pytest.param(
            _inscribir_club_1,
            lambda uc: uc.quitar_de_lista.ejecutar(QuitarJugadorListaDTO(idInscripcion=1, idJugador=1)),
            "no esta en la lista de buena fe",
            id="quitar de la lista a quien no esta",
        ),
    ],
)
def test_los_errores_de_negocio_llegan_como_error_de_dominio(
    uc, preparacion: Callable[[SimpleNamespace], object], accion: Callable[[SimpleNamespace], object], mensaje: str
):
    """Con repositorios reales, cada regla rota llega como `ErrorDeDominio`: es lo que la GUI muestra al usuario."""
    preparacion(uc)

    with pytest.raises(ErrorDeDominio, match=mensaje):
        accion(uc)
