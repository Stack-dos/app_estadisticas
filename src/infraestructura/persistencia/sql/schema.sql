BEGIN TRANSACTION;
-- Este script se ejecuta en cada arranque de la app (ver main.inicializar_db): NO debe borrar tablas.
-- Todas las tablas se crean con IF NOT EXISTS, asi el script es idempotente y conserva los datos.
-- Creacion de esquema de base de datos
-- create schema if not exists appbasquet;
-- Tabla usuario
CREATE TABLE IF NOT EXISTS usuario (
    idUsuario integer PRIMARY KEY AUTOINCREMENT,
    nombre text NOT NULL,
    email text NOT NULL UNIQUE,
    contrasenia text NOT NULL
) STRICT;
-- Tabla Club
CREATE TABLE IF NOT EXISTS club (
    idCLub integer PRIMARY KEY AUTOINCREMENT,
    nombre text NOT NULL UNIQUE
) STRICT;
-- Tabla usuarioClub
CREATE TABLE IF NOT EXISTS usuarioClub (
    idUsuario integer NOT NULL,
    idClub integer NOT NULL,
    rolEntrenador text NULL,
    PRIMARY KEY (idUsuario, idClub),
    FOREIGN KEY (idUsuario) REFERENCES usuario (idUsuario) ON DELETE CASCADE on UPDATE CASCADE,
    FOREIGN KEY (idClub) REFERENCES club (idClub) ON DELETE CASCADE on UPDATE CASCADE
) STRICT;
-- Tabla jugador
CREATE TABLE IF NOT EXISTS jugador (
    idJugador integer PRIMARY KEY AUTOINCREMENT,
    nombre text NOT NULL,
    apellido text NOT NULL,
    dni integer null UNIQUE,
    anioNacimiento integer NULL
) STRICT;
-- JugadorClub
CREATE TABLE IF NOT EXISTS jugadorClub (
    idJugador integer NOT NULL,
    idClub integer NOT NULL,
    fechaDesde text NOT NULL,
    fechaHasta text NULL,
    PRIMARY KEY (idJugador, idClub, fechaDesde),
    CHECK (
        fechaHasta IS NULL
        OR fechaHasta >= fechaDesde
    ),
    FOREIGN KEY (idJugador) REFERENCES jugador (idJugador) ON DELETE CASCADE on UPDATE CASCADE,
    FOREIGN KEY (idClub) REFERENCES club (idClub) ON DELETE CASCADE on UPDATE CASCADE
) STRICT;
CREATE UNIQUE INDEX IF NOT EXISTS uq_jugadorclub_activo_por_jugador
ON jugadorClub (idJugador)
WHERE fechaHasta IS NULL;
-- Tabla competencia
CREATE TABLE IF NOT EXISTS competencia (
    idCompetencia integer PRIMARY KEY AUTOINCREMENT,
    nombre text NOT NULL,
    anio integer NOT NULL CHECK(anio > 1900),
    tipo text NULL
) STRICT;
-- Tabla categoria
CREATE TABLE IF NOT EXISTS categoria (
    idCategoria integer PRIMARY KEY AUTOINCREMENT,
    nombre text NOT NULL
) STRICT;
-- Tabla inscripcion
CREATE TABLE IF NOT EXISTS inscripcion (
    idInscripcion integer PRIMARY KEY AUTOINCREMENT,
    idClub integer NOT NULL,
    idCategoria integer NOT NULL,
    idCompetencia integer NOT NULL,
    FOREIGN KEY (idClub) REFERENCES club (idClub) ON DELETE CASCADE on UPDATE CASCADE,
    FOREIGN KEY (idCategoria) REFERENCES categoria (idCategoria) ON DELETE CASCADE on UPDATE CASCADE,
    FOREIGN KEY (idCompetencia) REFERENCES competencia (idCompetencia) ON DELETE CASCADE on UPDATE CASCADE
) STRICT;
-- Tabla Lista de buena Fe
CREATE TABLE IF NOT EXISTS listaBuenaFe (
    idListaBuenaFe integer PRIMARY KEY AUTOINCREMENT,
    fechaPresentacion text NOT NULL,
    idInscripcion integer NOT NULL UNIQUE,
    FOREIGN KEY (idInscripcion) REFERENCES inscripcion (idInscripcion) ON DELETE CASCADE on UPDATE CASCADE
) STRICT;
-- Tabla Jugador Lista Buena Fe
CREATE TABLE IF NOT EXISTS jugadorListaBuenaFe (
    idJugador integer NOT NULL,
    idListaBuenaFe integer NOT NULL,
    PRIMARY KEY (idJugador, idListaBuenaFe),
    FOREIGN KEY (idJugador) REFERENCES jugador (idJugador) ON DELETE CASCADE on UPDATE CASCADE,
    FOREIGN KEY (idListaBuenaFe) REFERENCES listaBuenaFe (idListaBuenaFe) ON DELETE CASCADE on UPDATE CASCADE
) STRICT;
-- Tabla Partido
CREATE TABLE IF NOT EXISTS partido (
    idPartido integer PRIMARY KEY AUTOINCREMENT,
    fecha text NOT NULL,
    estadio text NULL,
    idCompetencia integer NOT NULL,
    idClubLocal integer NOT NULL,
    idClubVisitante integer NOT NULL,
    CHECK(idClubLocal != idClubVisitante),
    FOREIGN KEY (idCompetencia) REFERENCES competencia (idCompetencia) ON DELETE CASCADE on UPDATE CASCADE,
    FOREIGN KEY (idClubLocal) REFERENCES club (idClub) ON DELETE CASCADE on UPDATE CASCADE,
    FOREIGN KEY (idClubVisitante) REFERENCES club (idClub) ON DELETE CASCADE on UPDATE CASCADE
) STRICT;
-- Tabla jugador Partido
CREATE TABLE IF NOT EXISTS jugadorPartido (
    idJugador integer NOT NULL,
    idPartido integer NOT NULL,
    idClub integer NOT NULL,
    minutosJugados real NOT NULL DEFAULT 0 CHECK(
        minutosJugados BETWEEN 0 AND 48
    ),
    puntos integer NOT NULL DEFAULT 0 CHECK(puntos >= 0),
    T2C integer NOT NULL DEFAULT 0 CHECK(T2C >= 0),
    T2L integer NOT NULL DEFAULT 0 CHECK(T2L >= 0),
    T3C integer NOT NULL DEFAULT 0 CHECK(T3C >= 0),
    T3L integer NOT NULL DEFAULT 0 CHECK(T3L >= 0),
    T1C integer NOT NULL DEFAULT 0 CHECK(T1C >= 0),
    T1L integer NOT NULL DEFAULT 0 CHECK(T1L >= 0),
    rebotesDef integer NOT NULL DEFAULT 0 CHECK(rebotesDef >= 0),
    rebotesOf integer NOT NULL DEFAULT 0 CHECK(rebotesOf >= 0),
    asistencias integer NOT NULL DEFAULT 0 CHECK(asistencias >= 0),
    recuperos integer NOT NULL DEFAULT 0 CHECK(recuperos >= 0),
    perdidas integer NOT NULL DEFAULT 0 CHECK(perdidas >= 0),
    taponesRecibidos integer NOT NULL DEFAULT 0 CHECK(taponesRecibidos >= 0),
    taponesRealizados integer NOT NULL DEFAULT 0 CHECK(taponesRealizados >= 0),
    faltasRecibidas integer NOT NULL DEFAULT 0 CHECK(faltasRecibidas >= 0),
    faltasCometidas integer NOT NULL DEFAULT 0 CHECK(faltasCometidas >= 0),
    CHECK(T2C <= T2L),
    CHECK(T3C <= T3L),
    CHECK(T1C <= T1L),
    PRIMARY KEY (idJugador, idPartido),
    FOREIGN KEY (idJugador) REFERENCES jugador (idJugador) ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (idPartido) REFERENCES partido (idPartido) ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (idClub) REFERENCES club (idClub) ON DELETE RESTRICT ON UPDATE RESTRICT
) STRICT;
COMMIT;
