BEGIN TRANSACTION;

DROP VIEW IF EXISTS v_partidos_resumen;
DROP VIEW IF EXISTS v_boxscore_completo;
DROP VIEW IF EXISTS v_jugador_totales_temporada;
DROP VIEW IF EXISTS v_listas_detalle;

-- Vista 1: Resumen de partidos para UI y Pandas
CREATE VIEW IF NOT EXISTS v_partidos_resumen AS
SELECT
    p.idPartido AS id_partido,
    p.fecha AS fecha_partido,
    p.estadio,
    c.nombre AS competencia,
    c.anio AS anio_competencia,
    cat.nombre AS categoria,
    p.idClubLocal AS id_club_local,
    cl.nombre AS club_local,
    p.idClubVisitante AS id_club_visitante,
    cv.nombre AS club_visitante
FROM partido AS p
    INNER JOIN competencia AS c ON p.idCompetencia = c.idCompetencia
    INNER JOIN categoria AS cat ON p.idCategoria = cat.idCategoria
    INNER JOIN club AS cl ON p.idClubLocal = cl.idCLub
    INNER JOIN club AS cv ON p.idClubVisitante = cv.idClub;

-- Vista 2: Boxscore detallado (fuente principal para Pandas)
CREATE VIEW IF NOT EXISTS v_boxscore_completo AS
SELECT
    part.idPartido AS id_partido,
    part.idJugador AS id_jugador,
    part.idClub AS id_club,
    j.nombre || ' ' || j.apellido AS nombre_jugador,
    c.nombre AS nombre_club,
    part.minutosJugados AS minutos_jugados,
    part.puntos,
    part.T2C AS t2c,
    part.T2L AS t2l,
    part.T3C AS t3c,
    part.T3L AS t3l,
    part.T1C AS t1c,
    part.T1L AS t1l,
    part.rebotesDef AS rebotes_def,
    part.rebotesOf AS rebotes_of,
    (part.rebotesDef + part.rebotesOf) AS rebotes_totales,
    part.asistencias,
    part.recuperos,
    part.perdidas,
    part.taponesRecibidos AS tapones_recibidos,
    part.taponesRealizados AS tapones_realizados,
    part.faltasRecibidas AS faltas_recibidas,
    part.faltasCometidas AS faltas_cometidas
FROM jugadorPartido AS part
    INNER JOIN jugador AS j ON part.idJugador = j.idJugador
    INNER JOIN club AS c ON part.idClub = c.idClub;

-- Vista 3: Acumulados por temporada
CREATE VIEW IF NOT EXISTS v_jugador_totales_temporada AS
SELECT
    j.nombre || ' ' || j.apellido AS nombre_jugador,
    comp.anio AS anio_competencia,
    COUNT(jp.idPartido) AS partidos_jugados,
    SUM(jp.puntos) AS total_puntos,
    SUM(jp.T2C) AS total_t2c,
    SUM(jp.T2L) AS total_t2l,
    SUM(jp.T3C) AS total_t3c,
    SUM(jp.T3L) AS total_t3l,
    SUM(jp.T1C) AS total_t1c,
    SUM(jp.T1L) AS total_t1l,
    SUM(jp.rebotesDef) AS total_rebotes_def,
    SUM(jp.rebotesOf) AS total_rebotes_of,
    SUM(jp.rebotesDef + jp.rebotesOf) AS total_rebotes,
    SUM(jp.asistencias) AS total_asistencias,
    SUM(jp.recuperos) AS total_recuperos,
    SUM(jp.perdidas) AS total_perdidas,
    SUM(jp.taponesRealizados) AS total_tapones_realizados,
    SUM(jp.taponesRecibidos) AS total_tapones_recibidos,
    SUM(jp.faltasCometidas) AS total_faltas_cometidas,
    SUM(jp.faltasRecibidas) AS total_faltas_recibidas,
    CASE WHEN SUM(jp.T2L) > 0 THEN ROUND(CAST(SUM(jp.T2C) AS REAL) / SUM(jp.T2L) * 100, 1) ELSE 0.0 END AS porcentaje_t2,
    CASE WHEN SUM(jp.T3L) > 0 THEN ROUND(CAST(SUM(jp.T3C) AS REAL) / SUM(jp.T3L) * 100, 1) ELSE 0.0 END AS porcentaje_t3,
    CASE WHEN SUM(jp.T1L) > 0 THEN ROUND(CAST(SUM(jp.T1C) AS REAL) / SUM(jp.T1L) * 100, 1) ELSE 0.0 END AS porcentaje_t1
FROM jugadorPartido jp
    INNER JOIN jugador j ON jp.idJugador = j.idJugador
    INNER JOIN partido p ON jp.idPartido = p.idPartido
    INNER JOIN competencia comp ON p.idCompetencia = comp.idCompetencia
GROUP BY j.idJugador, comp.anio;

-- Vista 4: Detalle de inscripciones y listas
CREATE VIEW IF NOT EXISTS v_listas_detalle AS
SELECT
    i.idInscripcion AS id_inscripcion,
    cl.nombre AS nombre_club,
    cat.nombre AS nombre_categoria,
    comp.nombre AS nombre_competencia,
    j.nombre || ' ' || j.apellido AS nombre_jugador
FROM inscripcion i
    INNER JOIN club cl ON i.idClub = cl.idClub
    INNER JOIN categoria cat ON i.idCategoria = cat.idCategoria
    INNER JOIN competencia comp ON i.idCompetencia = comp.idCompetencia
    INNER JOIN listaBuenaFe lbf ON lbf.idInscripcion = i.idInscripcion
    INNER JOIN jugadorListaBuenaFe jlbf ON jlbf.idListaBuenaFe = lbf.idListaBuenaFe
    INNER JOIN jugador j ON jlbf.idJugador = j.idJugador;

COMMIT;
