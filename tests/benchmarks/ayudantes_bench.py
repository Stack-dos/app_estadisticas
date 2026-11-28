"""Ayudantes de los benchmarks: datos de volumen y el helper que mide una consulta y guarda su plan de ejecución.

Dos escalas (cada benchmark corre una vez por escala, ver el fixture `datos`):
- "temporada": una liga de 16 clubes con 15 jugadores cada uno, ida y vuelta (240 partidos, 24 jugadores por partido).
- "x10": diez temporadas seguidas de esa liga, con 3 bajas y 3 altas por club en cada pretemporada.

Se importan directo (`from ayudantes_bench import ...`) porque pytest agrega la carpeta del test al `sys.path`.
Comparar las dos escalas muestra cómo crece el tiempo de cada consulta cuando los datos se multiplican por 10.
Los datos salen de un `random.Random` con semilla fija: son siempre los mismos, en cualquier máquina.
"""

import random
import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import permutations
from typing import Any

import config.rutas as ruta

CLUBES = 16
PLANTEL = 15  # jugadores activos por club
EN_CANCHA = 12  # jugadores por club en cada boxscore y en cada lista de buena fe
RECAMBIO = 3  # bajas (y altas) por club en cada pretemporada
ULTIMO_ANIO = 2026
CATEGORIAS = ["Primera", "U21", "U19", "U17"]
ID_CATEGORIA_LIGA = 1  # id de "Primera" en la base generada
ESCALAS = {"temporada": 1, "x10": 10}


@dataclass
class Datos:
    escala: str
    conexion: sqlite3.Connection
    ids: dict[str, Any] = field(default_factory=dict)  # ids representativos para consultar
    conteos: dict[str, int] = field(default_factory=dict)  # filas por tabla, para el reporte


def _estadistica_jugador(rng: random.Random, id_jugador: int, id_partido: int, id_club: int) -> tuple[Any, ...]:
    t2l, t3l, t1l = rng.randint(0, 12), rng.randint(0, 8), rng.randint(0, 8)
    t2c, t3c, t1c = rng.randint(0, t2l), rng.randint(0, t3l), rng.randint(0, t1l)
    otros = [rng.randint(0, 8) for _ in range(9)]
    minutos = round(rng.uniform(0, 40), 1)
    return (id_jugador, id_partido, id_club, minutos, 2 * t2c + 3 * t3c + t1c, t2c, t2l, t3c, t3l, t1c, t1l, *otros)


def construir_base(escala: str) -> Datos:
    """Arma una base en memoria con el schema y las vistas reales, y la llena con `ESCALAS[escala]` temporadas."""
    temporadas = ESCALAS[escala]
    rng = random.Random(42)  # noqa: S311 - datos de prueba, no criptografía
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON;")
    with open(ruta.SCHEMA_SQL, encoding="utf-8") as schema, open(ruta.VISTA_SQL, encoding="utf-8") as vistas:
        con.executescript(schema.read())
        con.executescript(vistas.read())

    with con:
        # Clubes y un entrenador por club, más usuarios sueltos para que la tabla no sea trivial
        con.executemany("INSERT INTO club (nombre) VALUES (?)", [(f"Club {i:02d}",) for i in range(1, CLUBES + 1)])
        usuarios = 50 * temporadas
        con.executemany(
            "INSERT INTO usuario (nombre, email, contrasenia) VALUES (?, ?, ?)",
            [(f"Usuario {i}", f"usuario{i}@statspro.test", "hash-de-prueba") for i in range(1, usuarios + 1)],
        )
        con.executemany(
            "INSERT INTO usuarioClub (idUsuario, idClub, rolEntrenador) VALUES (?, ?, 'principal')",
            [(i, i) for i in range(1, CLUBES + 1)],
        )
        con.executemany("INSERT INTO categoria (nombre) VALUES (?)", [(c,) for c in CATEGORIAS])

        proximo_jugador = 1
        planteles: dict[int, list[int]] = {}
        jugador_con_historial = None
        primer_anio = ULTIMO_ANIO - temporadas + 1
        for t, anio in enumerate(range(primer_anio, ULTIMO_ANIO + 1)):
            # Pretemporada: la primera vez se arma el plantel; después, RECAMBIO bajas y altas por club
            for id_club in range(1, CLUBES + 1):
                plantel = planteles.setdefault(id_club, [])
                if t > 0:
                    for id_jugador in plantel[:RECAMBIO]:
                        con.execute(
                            "UPDATE jugadorClub SET fechaHasta = ? WHERE idJugador = ? AND fechaHasta IS NULL",
                            (f"{anio - 1}-12-31", id_jugador),
                        )
                    jugador_con_historial = jugador_con_historial or plantel[0]
                    del plantel[:RECAMBIO]
                altas = PLANTEL - len(plantel)
                nuevos = list(range(proximo_jugador, proximo_jugador + altas))
                proximo_jugador += altas
                con.executemany(
                    "INSERT INTO jugador (idJugador, nombre, apellido, anioNacimiento) VALUES (?, ?, ?, ?)",
                    [(j, f"Nombre{j}", f"Apellido{j}", rng.randint(1985, 2008)) for j in nuevos],
                )
                con.executemany(
                    "INSERT INTO jugadorClub (idJugador, idClub, fechaDesde) VALUES (?, ?, ?)",
                    [(j, id_club, f"{anio}-01-01") for j in nuevos],
                )
                plantel.extend(nuevos)

            # Competencia de la temporada, con sus categorías, inscripciones y listas de buena fe
            id_comp = con.execute(
                "INSERT INTO competencia (nombre, anio, tipo) VALUES (?, ?, 'liga')", (f"Liga {anio}", anio)
            ).lastrowid
            con.executemany(
                "INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (?, ?)",
                [(id_comp, c) for c in range(1, len(CATEGORIAS) + 1)],
            )
            for id_club in range(1, CLUBES + 1):
                id_insc = con.execute(
                    "INSERT INTO inscripcion (idClub, idCategoria, idCompetencia) VALUES (?, ?, ?)",
                    (id_club, ID_CATEGORIA_LIGA, id_comp),
                ).lastrowid
                id_lista = con.execute(
                    "INSERT INTO listaBuenaFe (fechaPresentacion, idInscripcion) VALUES (?, ?)",
                    (f"{anio}-02-01", id_insc),
                ).lastrowid
                con.executemany(
                    "INSERT INTO jugadorListaBuenaFe (idJugador, idListaBuenaFe) VALUES (?, ?)",
                    [(j, id_lista) for j in planteles[id_club][:EN_CANCHA]],
                )

            # Ida y vuelta: cada club recibe una vez a cada uno de los otros
            for k, (local, visitante) in enumerate(permutations(range(1, CLUBES + 1), 2)):
                fecha = date(anio, 3, 1) + timedelta(days=k // (CLUBES // 2))
                id_partido = con.execute(
                    "INSERT INTO partido (fecha, estadio, idCompetencia, idCategoria, idClubLocal, idClubVisitante)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (fecha.isoformat(), f"Estadio {local:02d}", id_comp, ID_CATEGORIA_LIGA, local, visitante),
                ).lastrowid
                filas = [
                    _estadistica_jugador(rng, j, id_partido, club)
                    for club in (local, visitante)
                    for j in rng.sample(planteles[club], EN_CANCHA)
                ]
                marcadores = ",".join("?" * len(filas[0]))  # el f-string solo arma los "?"; los valores van aparte
                con.executemany(f"INSERT INTO jugadorPartido VALUES ({marcadores})", filas)  # noqa: S608

    con.row_factory = sqlite3.Row  # como db_conexion en tests/conftest.py: los repositorios leen por nombre
    tablas = ["usuario", "club", "jugador", "jugadorClub", "competencia", "inscripcion", "jugadorListaBuenaFe"]
    conteos = {
        # los nombres de tabla son constantes de esta lista, no entrada de usuario
        t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # noqa: S608
        for t in [*tablas, "partido", "jugadorPartido"]
    }
    ultima = con.execute("SELECT MAX(idCompetencia), MAX(anio) FROM competencia").fetchone()
    ids = {
        "id_club": 1,
        "id_usuario": 1,
        "email": f"usuario{usuarios}@statspro.test",  # el último: no sirve "encontrarlo primero"
        "nombre_club": f"Club {CLUBES:02d}",
        "id_jugador": planteles[1][-1],
        "id_jugador_con_historial": jugador_con_historial or planteles[1][0],
        "id_competencia": ultima[0],
        "id_categoria": ID_CATEGORIA_LIGA,
        "anio": ultima[1],
        "id_inscripcion": con.execute("SELECT MAX(idInscripcion) FROM inscripcion WHERE idClub = 1").fetchone()[0],
        "id_partido": conteos["partido"] // 2,
    }
    ids["id_lista"] = con.execute(
        "SELECT idListaBuenaFe FROM listaBuenaFe WHERE idInscripcion = ?", (ids["id_inscripcion"],)
    ).fetchone()[0]
    return Datos(escala=escala, conexion=con, ids=ids, conteos=conteos)


def copiar_base(datos: Datos) -> sqlite3.Connection:
    """Copia en memoria de la base de una escala: para las escrituras, que no pueden ensuciar la compartida."""
    copia = sqlite3.connect(":memory:")
    datos.conexion.backup(copia)
    copia.execute("PRAGMA foreign_keys = ON;")
    copia.row_factory = sqlite3.Row
    return copia


def plan_de_ejecucion(conexion: sqlite3.Connection, funcion: Any, *args: Any) -> list[dict[str, Any]]:
    """Corre `funcion` una vez capturando cada SELECT que ejecuta, y devuelve el EXPLAIN QUERY PLAN de cada uno.

    set_trace_callback recibe el SQL con los parámetros ya reemplazados por sus valores, así que se puede
    pasar directo a EXPLAIN QUERY PLAN. Las líneas "SCAN tabla" son recorridos completos de la tabla.
    """
    consultas: list[str] = []
    conexion.set_trace_callback(consultas.append)
    try:
        funcion(*args)
    finally:
        conexion.set_trace_callback(None)
    planes = []
    for sql in dict.fromkeys(consultas):  # sin repetidos, en orden
        if sql.lstrip().upper().startswith(("SELECT", "WITH")):
            pasos = [fila[3] for fila in conexion.execute(f"EXPLAIN QUERY PLAN {sql}").fetchall()]
            planes.append({"sql": " ".join(sql.split())[:300], "plan": pasos})
    return planes


def medir_lectura(benchmark: Any, datos: Datos, funcion: Any, *args: Any) -> Any:
    """Mide una consulta de lectura y guarda en el reporte (extra_info) la escala, las filas y el plan."""
    resultado = benchmark(funcion, *args)
    benchmark.extra_info.update(
        escala=datos.escala,
        datos=datos.conteos,
        filas=len(resultado) if isinstance(resultado, list) else int(resultado is not None),
        plan=plan_de_ejecucion(datos.conexion, funcion, *args),
    )
    return resultado
