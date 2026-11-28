# Guía de Estudio: Patrón Repositorio en StatsPro Basketball

---

## 1. Fundamentos Teóricos

### ¿Qué es el Patrón Repositorio?

Un **repositorio** es un mediador. Se ubica entre la lógica de negocio (dominio) y el sistema de persistencia (base de datos), y su única responsabilidad es la de **traducir** en ambas direcciones:

```txt
Base de datos (filas SQL)  ──►  Repositorio  ──►  Objetos de dominio (@dataclass)
Objetos de dominio         ──►  Repositorio  ──►  Base de datos (INSERT / UPDATE)
```

Desde el punto de vista del dominio, el repositorio parece una **colección en memoria**: simplemente pedís un jugador por ID y te lo devuelve. No importa si viene de SQLite, PostgreSQL o un archivo JSON. Eso es transparencia total.

---

### ¿Por qué se usa en Clean Architecture?

Clean Architecture organiza el código en capas concéntricas donde **las dependencias solo apuntan hacia adentro** (hacia el dominio). El patrón Repositorio es el mecanismo concreto que lo hace posible en la capa de persistencia.

| Beneficio                     | ¿Cómo lo resuelve el repositorio?                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| **Desacoplamiento**           | El Dominio solo conoce la interfaz abstracta (`ABC`). Nunca importa `sqlite3`.                |
| **Testabilidad**              | Los tests usan la misma implementación SQLite, pero contra una DB `:memory:` efímera.         |
| **Intercambiabilidad**        | Reemplazar SQLite por PostgreSQL = escribir una nueva clase, sin tocar el dominio.            |
| **Mapeo estricto**            | Cada fila SQL se convierte en un `@dataclass` tipado; nunca circulan `dict` o `tuple` crudas. |
| **Centralización de queries** | Todas las SQL de una entidad viven en un solo archivo. Fácil de auditar.                      |

---

### Convención de Retornos del Proyecto

Seguimos una regla única y consistente para los tipos de retorno. **Memorizarla evita bugs silenciosos.**

| Tipo de operación     | Retorno esperado               | Ejemplo                                     |
| --------------------- | ------------------------------ | ------------------------------------------- |
| Búsqueda individual   | `Entidad \| None`              | `buscar_por_id(1)` → `Jugador` o `None`     |
| Búsqueda de colección | `list[Entidad]` (nunca `None`) | `obtener_todos()` → `[...]` o `[]`          |
| Escritura exitosa     | `Entidad` (con ID asignado)    | `guardar(j)` → `Jugador(idJugador=42, ...)` |
| Escritura fallida     | `None` (error de DB)           | `guardar(j)` → `None`                       |
| Error de negocio      | `raise ErrorDeDominio(...)`    | una regla de dominio → lanza su excepción |

---

## 2. Anatomía de un Repositorio en el Proyecto

### Mapa de Capas

```txt
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                       │
│              (Casos de Uso / Servicios)                     │
│                                                             │
│   caso_de_uso = RegistrarEntrenador(entrenador_repo)        │
│   entrenador_repo.guardar(entrenador)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │  depende de (inyección)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE DOMINIO                          │
│          src/dominio/repositorios/entrenador_repositorio.py │
│                                                             │
│   class EntrenadorRepositorio(ABC):        ◄── CONTRATO     │
│       @abstractmethod                                       │
│       def guardar(self, e: Entrenador) -> Entrenador | None │
│       @abstractmethod                                       │
│       def buscar_por_id(self, id: int) -> Entrenador | None │
└───────────────────────┬─────────────────────────────────────┘
                        │  implementa
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 CAPA DE INFRAESTRUCTURA                     │
│    src/infraestructura/repositorios/                        │
│    sqlite_entrenador_repositorio.py                         │
│                                                             │
│   class SqliteEntrenadorRepositorio(EntrenadorRepositorio): │
│       def __init__(self, conexion: sqlite3.Connection)      │
│       def _row_to_entity(self, row) -> Entrenador           │
│       def guardar(self, e: Entrenador) -> Entrenador | None │
│       def buscar_por_id(self, id: int) -> Entrenador | None │
└─────────────────────────────────────────────────────────────┘
```

### Estructura de archivos del proyecto

```txt
src/
├── dominio/
│   ├── entidades/
│   │   ├── jugador.py          # @dataclass Jugador, JugadorClub
│   │   ├── club.py             # @dataclass Club, UsuarioClub
│   │   └── partido.py          # @dataclass Partido, JugadorPartido
│   ├── repositorios/
│   │   ├── jugador_repositorio.py      # ABC – interfaz pura
│   │   ├── club_repositorio.py         # ABC – interfaz pura
│   │   └── partido_repositorio.py      # ABC – interfaz pura
│   └── exceptions.py           # ErrorDeDominio y excepciones de dominio
│
└── infraestructura/
    ├── logger.py               # get_logger(__name__)
    └── repositorios/
        ├── sqlite_jugador_repositorio.py   # Implementación concreta
        ├── sqlite_club_repositorio.py      # Implementación concreta
        └── sqlite_partido_repositorio.py   # Implementación concreta

tests/
└── integration/
    ├── conftest.py                         # Fixture db_conexion (:memory:)
    ├── test_repositorios_jugador.py
    ├── test_repositorios_club.py
    └── test_repositorios_partido.py
```
