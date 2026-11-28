# Protocolos y clases abstractas (`Protocol` vs `ABC`) en Python

En la Arquitectura Limpia que usa StatsPro, el **Dominio** necesita hablar con el mundo exterior (por ejemplo, guardar un jugador) sin conocer SQLite. Para eso define un
**contrato** (también llamado *puerto* o *interfaz*): una lista de métodos que cualquier "guardador" debe ofrecer. En Python hay **dos herramientas** para escribir ese contrato:

1. `typing.Protocol` (tipado estructural, *duck typing* estático).
2. `abc.ABC` + `@abstractmethod` (clase base abstracta, herencia explícita).

Esta guía explica las dos, para qué sirve cada una y **cuál usa hoy el proyecto** (spoiler: `ABC`).

---

## 1. `typing.Protocol` — "si tiene los métodos, cumple el contrato"

Un `Protocol` define qué métodos debe tener una clase para ser considerada, por ejemplo, un "Repositorio de jugadores", **sin importar de quién herede**.
Es el llamado *Static Duck Typing* (tipado estructural): si camina como pato y hace "cuac", el verificador de tipos (`mypy`) lo acepta como pato.

```python
from typing import Protocol

from dominio.entidades.jugador import Jugador


class JugadorRepositorio(Protocol):
    """Contrato que define cómo se deben persistir los jugadores."""

    def guardar(self, jugador: Jugador) -> Jugador | None:
        """Guarda un jugador en el sistema."""
        ...  # los puntos suspensivos son literales en Python para protocolos

```

La implementación concreta **no necesita heredar** del protocolo. Si tiene los mismos métodos con las mismas firmas, `mypy` entiende que "cumple":

```python
class SqliteJugadorRepositorio:            # <- no hereda de nada
    def __init__(self, conexion): ...

    def guardar(self, jugador: Jugador) -> Jugador | None: ...
```

**Ventaja:** desacople total (la implementación ni sabe que existe el protocolo). **Desventaja:** si olvidás un método, **nada falla al ejecutar**: recién `mypy` te avisa (y solo si lo corrés).

---

## 2. `abc.ABC` — "tenés que declarar que cumplís el contrato"

Una clase abstracta define los métodos con `@abstractmethod` y las implementaciones **heredan explícitamente** de ella:

```python
from abc import ABC, abstractmethod


class JugadorRepositorio(ABC):
    "Maneja Jugador y JugadorClub"

    @abstractmethod
    @abstractmethod
    def guardar(self, jugador: Jugador) -> Jugador | None:
        pass


class SqliteJugadorRepositorio(JugadorRepositorio):     # <- hereda explícitamente
    ...
```

**Ventaja:** si a `SqliteJugadorRepositorio` le falta un método abstracto, **Python se niega a instanciarla** (`TypeError: Can't instantiate abstract class...`)
aunque nadie corra `mypy`. Es una red de seguridad en tiempo de ejecución. **Desventaja:** la implementación queda atada (por herencia) al módulo del dominio.

---

## 3. Comparación

| | `Protocol` | `ABC` |
| --- | --- | --- |
| ¿La implementación tiene que heredar? | No (tipado estructural) | Sí (herencia explícita) |
| ¿Cuándo detecta un método faltante? | Solo `mypy` / el IDE (estático) | Python al **instanciar** (en ejecución) y también `mypy` |
| Acoplamiento de la implementación al contrato | Ninguno | Importa y hereda del contrato |
| Puede traer código compartido (métodos concretos) | No es su fin | Sí (métodos normales dentro del ABC) |
| Ideal para | Aceptar clases de terceros que no controlás | Contratos propios donde querés obligar a implementarlos |

---

## 4. Qué usa este proyecto hoy

**`ABC`**. Los cinco contratos viven en `src/dominio/repositorios/` (`ClubRepositorio`, `JugadorRepositorio`, `CompetenciaRepositorio`, `PartidoRepositorio`, `UsuarioRepositorio`)
y las implementaciones SQLite (`src/infraestructura/repositorios/sqlite_*_repositorio.py`) heredan de ellos.

Por qué tiene sentido para este proyecto: los contratos son **propios** (no hay implementaciones de terceros que adaptar) y el equipo prefiere que un método faltante
falle **al arrancar** y no recién cuando alguien corra `mypy`.

> El PRD menciona `typing.Protocol` como alternativa y sugiere dejar la decisión registrada en un ADR corto (registro de decisión de arquitectura).
> Migrar de `ABC` a `Protocol` sería un cambio mecánico: sacar la herencia y los `@abstractmethod`, y el resto del código (casos de uso, tests) no se enteraría.

### ¿Y en los tests?

Da igual cuál se use: `MagicMock(spec=JugadorRepositorio)` copia la lista de métodos de la clase que se le pasa, ya sea `ABC` o `Protocol`, y solo deja llamar a los métodos que existen
(ver [09-testing.md](09-testing.md), sección de `unittest.mock`). Por eso los casos de uso se testean sin base de datos, con un repositorio falso.

---

## 5. Regla práctica

- ¿El contrato lo escribís vos y querés que sea obligatorio implementarlo? → **`ABC`** (lo que usa el proyecto).
- ¿Querés aceptar objetos que vienen de una librería que no controlás, sin obligarlos a heredar de nada? → **`Protocol`**.
