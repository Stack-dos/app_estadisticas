# ADR-001: Arquitectura Local-First con SQLite

- **Estado**: Aprobado
- **Fecha**: 2026-10-03

## Contexto

La aplicación está pensada para un entrenador (DT) que la usa desde su propia computadora,
muchas veces en polideportivos o canchas donde no hay garantía de conectividad a internet. No hay
un backend propio ni se planea tener uno en el corto plazo: cada instalación es de un solo
usuario, trabajando con sus propios datos (clubes, jugadores, partidos). La app necesita poder
guardar y consultar esos datos sin depender de una red ni de un servicio externo.

## Alternativas Consideradas

No se hizo una evaluación formal de alternativas: SQLite embebido, sin servidor, se adoptó desde
el arranque del proyecto como la opción obvia para este escenario (una app de escritorio de un
solo usuario, sin backend). Se dejan mencionadas acá, solo como contraste y para que quede
registrado qué se descartó implícitamente:

- **Servidor de base de datos propio (Postgres/MySQL):** pensado para acceso concurrente
  multi-usuario o multi-dispositivo desde una red — no aplica al escenario actual (un DT, una
  computadora, sin servidor que mantener).
- **Backend cloud-first (Firebase/Supabase o similar):** requiere conectividad a internet
  constante y delega la sincronización/autenticación a un proveedor externo — contradice
  directamente el requisito de uso sin conexión en polideportivos.
- **Archivos planos (JSON/CSV):** no ofrece un motor de consultas real (joins, vistas,
  transacciones) y hubiera obligado a reimplementar a mano lo que SQLite ya da — solo viable para
  algo mucho más chico que lo que pide el PRD.

## Decisión Tomada

SQLite embebido (un único archivo `.db` por instalación), con arquitectura **offline-first**: la
aplicación nunca depende de una conexión de red para funcionar. Ya es la base de todo el código
implementado (capa de infraestructura, `database_manager.py`, esquema y vistas en
`src/infraestructura/persistencia/sql/`).

## Ventajas y Desventajas

### Ventajas

- Cero dependencia de infraestructura externa: no hay servidor que instalar, configurar ni
  mantener.
- Funciona sin conexión a internet, que es un requisito real (polideportivos, canchas).
- Despliegue simple: el motor viaja embebido en Python (`sqlite3` de la librería estándar) y los
  datos viven en un solo archivo, fácil de ubicar, copiar o respaldar a mano.
- Transacciones ACID reales (fundamental para la US-106, carga atómica de partidos).

### Desventajas

- **No sincroniza entre dispositivos.** Si el mismo entrenador usa la app desde dos computadoras
  distintas (o PC + celular más adelante), cada una tiene su propio archivo `.db` y no hay nada
  que los mantenga iguales — habría que agregar una capa de sincronización aparte si en algún
  momento se pide ese caso de uso (hoy no está en el alcance de ningún hito del PRD).
- **No soporta multi-usuario concurrente real.** SQLite permite varios procesos leyendo a la vez,
  pero las escrituras concurrentes desde dos procesos distintos sobre el mismo archivo son
  limitadas — no es un problema hoy (un usuario, un proceso CLI por comando) pero sí sería una
  restricción a revisar si el proyecto evoluciona hacia un escenario con varios entrenadores
  compartiendo el mismo club al mismo tiempo.
- Backups y migraciones de esquema son responsabilidad manual de la aplicación (no hay un
  servidor con herramientas de administración ya hechas) — es lo que cubren ADR-004
  (versionado de DB) y ADR-008 (estrategia de backup).
