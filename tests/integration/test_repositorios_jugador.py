import pytest

from aplicacion.casos_uso.eliminar_jugador import EliminarJugadorUseCase
from dominio.entidades.jugador import Jugador, JugadorClub
from dominio.exceptions import JugadorEnUsoError, VinculoActivoExistenteError
from infraestructura.repositorios.sqlite_jugador_repositorio import SqliteJugadorRepositorio


def test_buscar_por_id(db_conexion):
    """Funcion que busca a un jugador por un determinado ID

    Args:
        db_conexion (_type_): conexion a la base de datos
    """
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador_encontrado = jugador_rep.buscar_por_id(1)
    assert jugador_encontrado.nombre == "pepe"
    assert jugador_encontrado.apellido == "argento"
    assert jugador_encontrado.anioNacimiento == 1980


def test_buscar_por_club(db_conexion):
    """Funcion que busca a un jugador por su club

    Args:
        db_conexion (_type_): conexion a la base de datos
    """
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    # creamos la persona Jugador para vincularla a un determinado club
    nombre = "Carlos"
    apellido = "Mona Jimenez"
    anioNacimiento = 1980

    jugador_aux = Jugador(nombre=nombre, apellido=apellido, anioNacimiento=anioNacimiento)

    jugador_guardado = jugador_rep.guardar(jugador_aux)

    id_club = 1
    jugador_club_aux = JugadorClub(
        fechaDesde="2023-01-01", fechaHasta=None, idJugador=jugador_guardado.idJugador, idClub=id_club
    )
    jugador_rep.link_to_club(jugador_club_aux)

    jugadores_encontrados = jugador_rep.buscar_por_club(id_club)

    assert jugadores_encontrados is not None
    assert len(jugadores_encontrados) >= 1
    assert jugadores_encontrados[0].nombre == "Carlos"
    assert jugadores_encontrados[0].apellido == "Mona Jimenez"
    # esto es para corregir, estuve probando de varias formas y no funciona, es para revisar


def test_guardar(db_conexion):
    """Funcion que guarda a un jugador en la base de datos
    Args:
        db_conexion (_type_): conexion a la base de datos
    """
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    nombre = "Carlos"
    apellido = "Mona Jimenez"
    anioNacimiento = 1951
    jugador_aux = Jugador(nombre=nombre, apellido=apellido, anioNacimiento=anioNacimiento)
    jugador_guardado = jugador_rep.guardar(jugador_aux)
    jugador_reg = jugador_rep.buscar_por_id(jugador_guardado.idJugador)
    assert jugador_reg.nombre == nombre
    assert jugador_reg.apellido == apellido
    assert jugador_reg.anioNacimiento == anioNacimiento


def test_link_to_club(db_conexion):
    """

    Args:
        db_conexion (_type_): _description_
    """
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador_aux = Jugador(nombre="Lionel", apellido="Messi", anioNacimiento=1987)
    jugador_guardado = jugador_rep.guardar(jugador_aux)

    id_club = 1
    jc = JugadorClub(fechaDesde="2021-08-10", fechaHasta=None, idJugador=jugador_guardado.idJugador, idClub=id_club)
    jugador_rep.link_to_club(jc)

    jugadores_en_club = jugador_rep.buscar_por_club(id_club)
    assert jugadores_en_club is not None
    encontrado = any(j.idJugador == jugador_guardado.idJugador for j in jugadores_en_club)
    assert encontrado is True


def test_club_activo(db_conexion):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador_aux = Jugador(nombre="Angel", apellido="Di Maria", anioNacimiento=1988)
    jugador_guardado = jugador_rep.guardar(jugador_aux)

    id_club = 1
    jc = JugadorClub(fechaDesde="2023-07-01", fechaHasta=None, idJugador=jugador_guardado.idJugador, idClub=id_club)
    jugador_rep.link_to_club(jc)

    club_activo = jugador_rep.club_activo(jugador_guardado.idJugador)
    assert club_activo is not None
    assert club_activo.idClub == id_club


def test_link_to_club_si_ya_tiene_vinculo_activo_lanza_error_de_dominio(db_conexion, crear_jugador):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador = jugador_rep.guardar(crear_jugador())
    jugador_rep.link_to_club(JugadorClub("2026-01-01", None, idJugador=jugador.idJugador, idClub=1))

    with pytest.raises(VinculoActivoExistenteError):
        jugador_rep.link_to_club(JugadorClub("2026-02-01", None, idJugador=jugador.idJugador, idClub=2))


def test_buscar_por_club_excluye_vinculos_cerrados(db_conexion):
    """buscar_por_club devuelve solo jugadores actuales: el que ya se fue (fechaHasta cargada) no aparece."""
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    id_club = 1
    actual = jugador_rep.guardar(Jugador(nombre="Actual", apellido="Vigente", anioNacimiento=1995))
    ex = jugador_rep.guardar(Jugador(nombre="Ex", apellido="Jugador", anioNacimiento=1994))
    jugador_rep.link_to_club(JugadorClub("2023-01-01", None, idJugador=actual.idJugador, idClub=id_club))
    jugador_rep.link_to_club(JugadorClub("2020-01-01", None, idJugador=ex.idJugador, idClub=id_club))
    # el repositorio todavia no tiene un metodo para cerrar un vinculo, se cierra directo en la BD
    db_conexion.execute(
        "UPDATE jugadorClub SET fechaHasta = ? WHERE idJugador = ? AND idClub = ?",
        ("2022-12-31", ex.idJugador, id_club),
    )
    db_conexion.commit()

    ids = [j.idJugador for j in jugador_rep.buscar_por_club(id_club)]

    assert actual.idJugador in ids
    assert ex.idJugador not in ids


def test_historial_vinculos_de_un_jugador_sin_clubes_es_una_lista_vacia(db_conexion, crear_jugador):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador = jugador_rep.guardar(crear_jugador())

    assert jugador_rep.historial_vinculos(jugador.idJugador) == []


def test_cerrar_vinculo_cierra_el_vigente_y_deja_al_jugador_sin_club_activo(db_conexion, crear_jugador):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador = jugador_rep.guardar(crear_jugador())
    jugador_rep.link_to_club(JugadorClub("2026-01-01", None, idJugador=jugador.idJugador, idClub=1))

    cerrado = jugador_rep.cerrar_vinculo(jugador.idJugador, "2026-06-30")

    assert cerrado == JugadorClub("2026-01-01", "2026-06-30", idJugador=jugador.idJugador, idClub=1)
    assert jugador_rep.club_activo(jugador.idJugador) is None
    assert jugador.idJugador not in [j.idJugador for j in jugador_rep.buscar_por_club(1)]


def test_un_jugador_que_se_fue_de_un_club_puede_vincularse_a_otro_y_queda_el_historial(db_conexion, crear_jugador):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador = jugador_rep.guardar(crear_jugador())
    jugador_rep.link_to_club(JugadorClub("2020-01-01", None, idJugador=jugador.idJugador, idClub=1))
    jugador_rep.cerrar_vinculo(jugador.idJugador, "2021-01-01")
    jugador_rep.link_to_club(JugadorClub("2021-02-01", None, idJugador=jugador.idJugador, idClub=2))

    historial = jugador_rep.historial_vinculos(jugador.idJugador)

    assert historial == [
        JugadorClub("2020-01-01", "2021-01-01", idJugador=jugador.idJugador, idClub=1),
        JugadorClub("2021-02-01", None, idJugador=jugador.idJugador, idClub=2),
    ]
    assert jugador_rep.club_activo(jugador.idJugador).idClub == 2


def test_cerrar_vinculo_de_un_jugador_sin_vinculo_vigente_devuelve_none(db_conexion, crear_jugador):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador = jugador_rep.guardar(crear_jugador())

    assert jugador_rep.cerrar_vinculo(jugador.idJugador, "2026-06-30") is None


def test_cerrar_vinculo_con_fecha_anterior_al_inicio_lo_rechaza_la_base_y_sigue_vigente(db_conexion, crear_jugador):
    """El CHECK (fechaHasta >= fechaDesde) del schema impide una baja anterior al inicio del vinculo."""
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    jugador = jugador_rep.guardar(crear_jugador())
    jugador_rep.link_to_club(JugadorClub("2026-01-01", None, idJugador=jugador.idJugador, idClub=1))

    assert jugador_rep.cerrar_vinculo(jugador.idJugador, "2025-12-31") is None
    assert jugador_rep.club_activo(jugador.idJugador).idClub == 1


def test_buscar_por_nombre_busca_en_todos_los_clubes_sin_distinguir_mayusculas_ni_tildes(db_conexion):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    sin_club = jugador_rep.guardar(Jugador(nombre="Martín", apellido="Pérez", anioNacimiento=2002))
    en_otro_club = jugador_rep.guardar(Jugador(nombre="Mateo", apellido="Perez", anioNacimiento=2001))
    jugador_rep.link_to_club(JugadorClub("2025-01-01", None, idJugador=en_otro_club.idJugador, idClub=2))

    # Busca sin tildes ni mayusculas y encuentra tanto al que tiene tildes como al vinculado en otro club
    ids_perez = [j.idJugador for j in jugador_rep.buscar_por_nombre("perez")]
    assert sin_club.idJugador in ids_perez
    assert en_otro_club.idJugador in ids_perez

    # Busca con tildes contra el guardado sin tildes y por nombre + apellido
    assert [j.idJugador for j in jugador_rep.buscar_por_nombre("MARTÍN")] == [sin_club.idJugador]
    assert [j.idJugador for j in jugador_rep.buscar_por_nombre("mateo pérez")] == [en_otro_club.idJugador]
    assert jugador_rep.buscar_por_nombre("   ") == []


def test_actualizar_jugador_modifica_los_datos_en_la_base(db_conexion):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    guardado = jugador_rep.guardar(Jugador(nombre="Mratin", apellido="Preez", anioNacimiento=2000))

    actualizado = jugador_rep.actualizar(
        Jugador(nombre="Martín", apellido="Pérez", anioNacimiento=2001, idJugador=guardado.idJugador)
    )

    assert actualizado == Jugador(nombre="Martín", apellido="Pérez", anioNacimiento=2001, idJugador=guardado.idJugador)
    desde_db = jugador_rep.buscar_por_id(guardado.idJugador)
    assert desde_db == actualizado


def test_eliminar_jugador_sin_uso_borra_jugador_y_sus_vinculos_de_club(db_conexion):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    duplicado = jugador_rep.guardar(Jugador(nombre="Duplicado", apellido="Error", anioNacimiento=2003))
    jugador_rep.link_to_club(JugadorClub("2026-01-01", None, idJugador=duplicado.idJugador, idClub=1))

    assert jugador_rep.jugador_en_uso(duplicado.idJugador) is False
    assert EliminarJugadorUseCase(jugador_rep).ejecutar(duplicado.idJugador) is True
    assert jugador_rep.buscar_por_id(duplicado.idJugador) is None
    assert duplicado.idJugador not in [j.idJugador for j in jugador_rep.buscar_por_club(1)]


def test_eliminar_jugador_con_partido_o_lista_en_seed_es_rechazado(db_conexion):
    """En seed.sql, el jugador 1 (pepe argento) tiene partido cargado y lista; el jugador 3 esta solo en lista."""
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    uc = EliminarJugadorUseCase(jugador_rep)

    with pytest.raises(JugadorEnUsoError):
        uc.ejecutar(1)
    with pytest.raises(JugadorEnUsoError):
        uc.ejecutar(3)
    assert jugador_rep.buscar_por_id(1) is not None
    assert jugador_rep.buscar_por_id(3) is not None


def test_listar_con_club_actual_da_el_club_vigente_o_none(db_conexion, crear_jugador):
    jugador_rep = SqliteJugadorRepositorio(db_conexion)
    libre = jugador_rep.guardar(crear_jugador(nombre="Zeta", apellido="Zzz"))
    jugador_rep.link_to_club(JugadorClub("2020-01-01", None, idJugador=libre.idJugador, idClub=1))
    jugador_rep.cerrar_vinculo(libre.idJugador, "2021-01-01")  # se fue: hoy no tiene club
    con_club = jugador_rep.guardar(crear_jugador(nombre="Yago", apellido="Zzy"))
    jugador_rep.link_to_club(JugadorClub("2021-02-01", None, idJugador=con_club.idJugador, idClub=2))
    nombre_club_2 = db_conexion.execute("SELECT nombre FROM club WHERE idClub = 2").fetchone()[0]

    filas = {f.jugador.idJugador: f.nombreClub for f in jugador_rep.listar_con_club_actual()}

    assert filas[libre.idJugador] is None
    assert filas[con_club.idJugador] == nombre_club_2
    # Un jugador aparece una sola vez aunque tenga vinculos cerrados
    assert len(filas) == db_conexion.execute("SELECT COUNT(*) FROM jugador").fetchone()[0]
