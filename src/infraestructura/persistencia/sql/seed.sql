-- Script para cargar datos de prueba a la base de datos
BEGIN TRANSACTION;
-- 1 Usuario
INSERT INTO usuario (nombre, email, contrasenia)
VALUES (
        'juan salvatierra',
        'juan.salvatierra@gmail.com',
        '$2b$10$CwTycUXWue0Thq9StjUM0uJ8s6mG1fK0O9Yx8uWb1x1o1t4bm/FKa'
    );
-- 2 Clubes
INSERT INTO club (nombre)
VALUES ('Atenas'),
    ('Universitario');
-- 10 Jugadores
INSERT INTO jugador (nombre, apellido, anioNacimiento)
VALUES ('pepe', 'argento', 1980),
    ('antonio', 'argentinito', 1985),
    ('Pepa', 'arrigoni', 1999),
    ('Gabriel', 'batistuta', 2001),
    ('LEONEL ANDRES', 'messi', 2005),
    ('Sergio', 'aguero', 1993),
    ('Julian', 'alvarez', 1945),
    ('cristian', 'romero', 1998),
    ('Nico', 'otamendi', 2000),
    ('nahuel', 'molina', 1987);
-- 1 Competencia
INSERT INTO competencia (nombre, anio, tipo)
VALUES ('PROVINCIAL U21', 2026, 'PROVINCIAL');
-- 2 Partidos
INSERT INTO partido (
        fecha,
        estadio,
        idCompetencia,
        idClubLocal,
        idClubVisitante
    )
VALUES ('2026-05-21', 'Cancha Atenas', 1, 1, 2),
    ('2026-06-20', 'Cancha Universitario', 1, 2, 1);
-- categoria
INSERT into categoria (nombre)
VALUES('U21');
--INSCRIPCION A COMPETENCIA
INSERT INTO inscripcion (idCLub, idCategoria, idCompetencia)
VALUES (1, 1, 1),
    (2, 1, 1);
-- LISTAS DE BUENA FE
INSERT INTO listaBuenaFe (fechaPresentacion, idInscripcion)
VALUES (datetime('now'), 1),
    (datetime('now'), 2);
-- LISTAS DE BUENA FE JUGADOR
INSERT INTO jugadorListaBuenaFe (idJugador, idListaBuenaFe)
VALUES (1, 1),
    (2, 1),
    (3, 1),
    (4, 1),
    (5, 1),
    (6, 2),
    (7, 2),
    (8, 2),
    (9, 2),
    (10, 2);
-- 3 JugadorPartido
INSERT INTO jugadorPartido (
        idJugador,
        idPartido,
        idClub,
        minutosJugados,
        puntos,
        T2C,
        T2L,
        T3C,
        T3L,
        T1C,
        T1L,
        rebotesDef,
        rebotesOf,
        asistencias,
        recuperos,
        perdidas,
        taponesRecibidos,
        taponesRealizados,
        faltasCometidas,
        faltasRecibidas
    )
VALUES (
        1,
        1,
        1,
        20,
        10,
        2,
        5,
        2,
        5,
        0,
        4,
        10,
        2,
        3,
        2,
        5,
        1,
        5,
        2,
        3
    ),
    (
        6,
        1,
        2,
        12.4,
        3,
        0,
        8,
        0,
        12,
        3,
        8,
        2,
        3,
        5,
        3,
        5,
        1,
        5,
        2,
        3
    ),
    (
        2,
        2,
        1,
        36,
        10,
        2,
        5,
        2,
        5,
        0,
        4,
        10,
        2,
        3,
        2,
        5,
        1,
        5,
        2,
        3
    );
COMMIT;
