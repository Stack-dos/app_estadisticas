BEGIN TRANSACTION;

-- 1. Borrar datos de tablas con restricciones RESTRICT o relaciones de muchos a muchos
-- Borrar estadísticas de jugadores (Restricción RESTRICT)
DELETE FROM jugadorPartido;

-- Borrar relación Jugador-Lista de buena fe
DELETE FROM jugadorListaBuenaFe;

-- Borrar Listas de buena fe
DELETE FROM listaBuenaFe;

-- Borrar Inscripciones
DELETE FROM inscripcion;

-- Borrar categorias habilitadas por competencia (US-107): despues de las inscripciones, que las referencian
DELETE FROM competenciaCategoria;

-- 2. Borrar datos de tablas base con filtros específicos del SEED
-- Borrar partidos
DELETE FROM partido WHERE fecha IN ('2026-05-21', '2026-06-20');

-- Borrar categorías
DELETE FROM categoria WHERE nombre = 'U21';

-- Borrar competencias
DELETE FROM competencia WHERE nombre = 'PROVINCIAL U21';

-- Borrar clubes
DELETE FROM club WHERE nombre IN ('Atenas', 'Universitario');

-- Borrar jugadores
DELETE FROM jugador
WHERE (nombre = 'pepe' AND apellido = 'argento')
   OR (nombre = 'antonio' AND apellido = 'argentinito')
   OR (nombre = 'Pepa' AND apellido = 'arrigoni')
   OR (nombre = 'Gabriel' AND apellido = 'batistuta')
   OR (nombre = 'LEONEL ANDRES' AND apellido = 'messi')
   OR (nombre = 'Sergio' AND apellido = 'aguero')
   OR (nombre = 'Julian' AND apellido = 'alvarez')
   OR (nombre = 'cristian' AND apellido = 'romero')
   OR (nombre = 'Nico' AND apellido = 'otamendi')
   OR (nombre = 'nahuel' AND apellido = 'molina');

-- Borrar usuarios
DELETE FROM usuario WHERE nombre = 'juan salvatierra';

COMMIT;
