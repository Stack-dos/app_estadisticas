# Testing — conceptos, técnicas y ejemplos aplicados al proyecto

> Guía de referencia, pensada para consultarse cada vez que arranquen un test nuevo — no hace
> falta leerla entera de una sentada. Todos los ejemplos usan clases y tests **reales** del
> proyecto (`Jugador`, `JugadorRepositorio`, `RegistrarJugadorUseCase`, `crear_boxscore`…), no
> ejemplos genéricos. Cada técnica se explica con el mismo esquema: **qué es → cómo se usa →
> ejemplo del proyecto → cuándo NO usarla**.

## Índice

0. [Cómo está organizada la suite](#0-cómo-está-organizada-la-suite)
1. [Los tipos de test (y cuáles usa este proyecto)](#1-los-tipos-de-test-y-cuáles-usa-este-proyecto)
2. [Test doubles: el vocabulario de los objetos de prueba](#2-test-doubles-el-vocabulario-de-los-objetos-de-prueba)
3. [`unittest.mock`: la herramienta para crear repositorios falsos](#3-unittestmock-la-herramienta-para-crear-repositorios-falsos)
4. [Ejemplo completo: testear un caso de uso](#4-ejemplo-completo-testear-un-caso-de-uso)
5. [Tests de excepciones de dominio](#5-tests-de-excepciones-de-dominio)
6. [`@pytest.mark.parametrize`: muchos casos, un solo test](#6-pytestmarkparametrize-muchos-casos-un-solo-test)
7. [El patrón `**overrides`: fábricas de datos de prueba](#7-el-patrón-overrides-fábricas-de-datos-de-prueba)
8. [Fixtures y `conftest.py`](#8-fixtures-y-conftestpy)
9. [Testeando comandos CLI](#9-testeando-comandos-cli-ejecutar-main-y-de-punta-a-punta)
10. [Cobertura](#10-cobertura-coverage)
11. [Buenas prácticas](#11-buenas-prácticas)
12. [Checklist: agregar un caso de uso o un comando nuevo](#12-checklist-agregar-un-caso-de-uso-o-un-comando-nuevo)

---

## 0. Cómo está organizada la suite

**Cómo se corre** (ver el [RUNBOOK](../../RUNBOOK.md) para el resto de los comandos):

```bash
uv run pytest                                  # toda la suite
uv run pytest tests/unit                       # solo los unitarios (rápidos, sin base de datos)
uv run pytest -k "vincular"                    # solo los tests cuyo nombre contiene "vincular"
uv run pytest -v --cov=src --cov-report=html   # con reporte de cobertura (también: make run_test)
```

**Dónde vive cada cosa:**

| Carpeta / archivo | Qué contiene |
| --- | --- |
| `tests/unit/` | Tests que **no tocan SQLite**: entidades, excepciones, casos de uso (con repositorios falsos), comandos de la CLI, helpers |
| `tests/integration/` | Tests con **SQLite real** en memoria (repositorios, esquema y vistas SQL) y el recorrido completo de la CLI contra una base temporal |
| `tests/conftest.py` | Fixtures compartidas: bases de datos en memoria (`db_conexion`, `db_conexion_sin_seed`, `db_conexion_sandbox`) y **fábricas de datos** (`crear_jugador`, `crear_partido`, `crear_boxscore`) |
| `pyproject.toml` → `[tool.pytest.ini_options]` | `pythonpath = src` (los tests importan `dominio`, `aplicacion`… directo) y `testpaths = tests` |
| `pyproject.toml` → `[tool.coverage.*]` | Qué medir (con cobertura de ramas, `branch = true`) y el mínimo de cobertura (`fail_under`) |

**Sobre los nombres de archivo y `__init__.py`:** en el proyecto **no hay `__init__.py`** (ni en `src/` ni en `tests/`): desde Python 3.3 las carpetas funcionan como
paquetes "namespace" sin ese archivo. La única consecuencia práctica para los tests es que **dos archivos de test no pueden llamarse igual**, aunque estén en carpetas
distintas (pytest los confundiría). Por eso los archivos tienen nombres únicos (`test_uc_jugadores.py`, `test_cli_comandos.py`…).

---

## 1. Los tipos de test (y cuáles usa este proyecto)

"Test" es una palabra muy amplia. En la industria se distinguen varios **tipos** según *qué* prueban y *cuánto* del sistema real usan. Conocerlos sirve para elegir bien
dónde poner cada prueba. Se suelen ordenar en una **pirámide**: muchos tests baratos abajo, pocos tests caros arriba.

```text
            ▲  pocos, lentos, frágiles
           /E2E\            recorren TODA la aplicación
          /------\
         /integra-\         varias piezas reales juntas (ej. repositorio + SQLite)
        /  ción    \
       /------------\
      /  unitarios   \      una pieza aislada, sin nada externo
     /________________\
        ▼ muchos, rápidos, estables
```

| Tipo | Qué prueba | Cuándo conviene | En este proyecto |
| --- | --- | --- | --- |
| **Unitario** | Una unidad de lógica **aislada** (una clase, una función). Lo externo (base de datos, archivos, red) se reemplaza por un doble de prueba | Reglas de negocio, validaciones, ramas de error. Es la base de la pirámide | `tests/unit/`: entidades, casos de uso con `MagicMock`, comandos con repos falsos |
| **De integración** | Que dos o más piezas **reales** funcionen bien juntas | Todo lo que habla con algo externo: SQL, archivos, esquema de la base | `tests/integration/test_repositorios_*.py` (repositorio + SQLite en memoria), `test_database.py` (esquema y vistas) |
| **End-to-end (E2E)** | Un flujo completo, "como lo usaría el usuario", de la entrada a la salida | Pocos, para los recorridos críticos | `tests/integration/test_cli_e2e.py`: `main()` real contra una base temporal (crear club → jugador → vínculo → competencia → inscripción) |
| **De humo (smoke)** | Solo que "**prende**": lo mínimo indispensable funciona | Verificación rápida tras un cambio o un deploy | `test_schema_sql_ejecuta_sin_errores`, `test_seed_sql_ejecuta_sin_errores` (¿los scripts SQL se aplican sin explotar?) |
| **De regresión** | Que un bug **ya corregido** no vuelva a aparecer | Cada vez que se arregla un bug: se agrega el test que lo habría detectado | `test_los_datos_persisten_entre_ejecuciones` (el `schema.sql` borraba las tablas en cada arranque) y `test_buscar_por_club_excluye_vinculos_cerrados` |
| **De aceptación** | Que se cumple un **criterio de aceptación** de la historia de usuario, en el lenguaje del negocio | Cerrar una US: "¿hace lo que el PRD pidió?" | Los AC de la US-103 (ej. AC3 "errores sin traceback") están cubiertos por `test_cli_main.py` y `test_cli_e2e.py` |
| **De contrato** | Que una implementación **cumple el contrato** de su interfaz | Cuando hay varias implementaciones de lo mismo (ej. SQLite hoy, otra base mañana) | *Todavía no aplica*: hay una sola implementación por repositorio. `MagicMock(spec=...)` ya protege parte de esto |
| **Basado en propiedades** | Una regla que debe cumplirse para **miles de entradas generadas al azar** (con la librería `hypothesis`) | Lógica matemática (ej. "los puntos siempre = T2C·2 + T3C·3 + T1C") | *Todavía no aplica*. Buen candidato para el motor de estadísticas del Hito 2 |
| **De snapshot / golden** | Que una salida compleja (un reporte, un PDF, una tabla) **no cambie** respecto de una versión guardada | Reportes y exportaciones | *Todavía no aplica* (Hito 3: reportes) |
| **De rendimiento / carga** | Cuánto tarda o cuánta memoria usa algo con muchos datos | Importar un Excel grande, consultas pesadas | *Todavía no aplica* (US-201: importación de Excel) |
| **De mutación** | La **calidad de los propios tests**: se rompe el código a propósito y se verifica que algún test falle | Para saber si los tests realmente detectan errores (cobertura alta no lo garantiza) | Se hizo **a mano** al armar esta suite (romper una validación y confirmar que falla). Existen herramientas (`mutmut`) para automatizarlo |
| **Estáticos** | Errores **sin ejecutar** el código: tipos, estilo, dependencias vulnerables | Siempre, en el CI: son baratos | `mypy --strict`, `ruff`, `pip-audit` (corren en el CI, ver [ideas-aprendizaje.md](../ideas-aprendizaje.md), sección 8) |

**Regla práctica para decidir dónde va un test nuevo:** si para escribirlo necesitás una fixture que abra una conexión SQLite, es de **integración**.
Si podés escribirlo pasando objetos Python comunes (dataclasses, un repositorio falso armado con `MagicMock`), es **unitario** y va en `tests/unit/`.

La diferencia **no** es "está en la carpeta `unit` o `integration`" — eso es solo convención. Es **qué tan real es lo que hay del otro lado**:

| | Unitario | Integración |
| --- | --- | --- |
| Dependencias externas (DB, archivos, red) | Reemplazadas por un doble de prueba | Reales (o una réplica fiel, ej. SQLite `:memory:`) |
| Velocidad | Microsegundos | Más lento: arma el esquema, corre SQL real |
| Qué significa que falle | Hay un bug en la lógica de esa unidad | Hay un bug en cómo se usa SQL/el filesystem, o en el propio SQL |

**Ejemplo con código del proyecto — la misma regla probada en dos niveles:**

- `tests/unit/test_uc_jugadores.py::test_registrar_jugador_con_dni_duplicado_deja_subir_la_excepcion` (**unitario**): el repositorio falso *dice* "DNI duplicado" y se verifica que el caso de uso deja subir la excepción. No hay SQL.
- `tests/integration/test_repositorios_jugador.py::test_guardar_jugador_dni_duplicado_lanza_excepcion` (**integración**): el `INSERT` real compite contra una fila sembrada. Si mañana cambia la columna `dni` en `schema.sql`, **este** test lo detecta y el unitario no.

Los dos hacen falta: el unitario prueba la lógica; el de integración prueba que el SQL funciona.

---

## 2. Test doubles: el vocabulario de los objetos de prueba

"Mock" es el término que todo el mundo usa como genérico, pero en realidad hay **cinco tipos**
distintos de "objeto de prueba" (test double), cada uno con un propósito distinto. Vale la pena
distinguirlos porque usar el tipo equivocado hace tests confusos o frágiles:

| Tipo | Qué hace | Ejemplo en este proyecto |
| --- | --- | --- |
| **Dummy** | Se pasa porque hace falta el parámetro, pero nunca se usa de verdad. | Un `Jugador` de relleno pasado a una función que ni lo mira. |
| **Stub** | Devuelve respuestas fijas y predefinidas a los llamados que recibe, sin lógica. | Un repositorio cuyo `buscar_por_dni()` siempre devuelve `None`, sin importar el DNI. |
| **Fake** | Tiene una implementación **real pero simplificada** (funciona de verdad, pero no es la de producción). | Un `JugadorRepositorio` respaldado por un `dict` en memoria en vez de SQLite: guardás y después lo encontrás, pero no persiste a disco. |
| **Mock** | Además de responder, **registra cómo lo llamaron** para poder verificar después ("¿se llamó una vez? ¿con qué argumentos?"). | `MagicMock(spec=JugadorRepositorio)` de `unittest.mock`, verificado con `.assert_called_once_with(...)`. |
| **Spy** | Como un Mock, pero envuelve un objeto **real** y deja que la llamada real pase, además de registrarla. | Poco común en este proyecto: útil cuando querés confirmar que se llamó a un servicio real sin reemplazar su comportamiento. |

Los casos de uso de este proyecto se testean sobre todo con **Mock** (sección 3). El **Fake** (sección 4.1) es la alternativa cuando el test necesita que el repositorio
"se comporte bien" a través de varias llamadas.

---

## 3. `unittest.mock`: la herramienta para crear repositorios falsos

**Qué es:** un módulo que **viene con Python** (no hay que instalar nada; el proyecto no usa `pytest-mock`) para crear objetos falsos que aceptan llamadas,
devuelven lo que uno les indique y **recuerdan cómo los llamaron**.

**Para qué sirve acá:** los casos de uso reciben repositorios por constructor (Inyección de Dependencias). En un test unitario se les pasa un repositorio falso en vez del de SQLite:
el test corre en microsegundos, no depende de ninguna base y se puede simular cualquier respuesta (incluso errores difíciles de provocar de verdad).

### 3.1 `Mock` y `MagicMock`

Un `Mock` **acepta cualquier atributo o llamada** que le hagas y por defecto devuelve otro `Mock`. No tiene comportamiento propio: hay que decirle qué devolver.
`MagicMock` es lo mismo, pero además soporta los métodos "mágicos" de Python (`__len__`, `__iter__`, `__enter__`…).

```python
from unittest.mock import MagicMock

repo_falso = MagicMock()
repo_falso.buscar_por_dni.return_value = None      # "cuando te llamen así, devolvé None"

repo_falso.buscar_por_dni(12345678)                # -> None
```

El proyecto usa `MagicMock` (con `spec`, ver abajo) por costumbre: se comporta igual que `Mock` para los repositorios y evita sorpresas si algún día un caso de uso usa `len()` o `for` sobre un resultado.

### 3.2 `spec=`: la protección contra errores de tipeo

El problema de un mock a secas es que **acepta cualquier nombre de método**, incluso uno que no existe en la interfaz real. Si escribís `repo.buscar_por_dnii` (con una `i` de más),
el mock lo deja pasar y el test "pasa" probando algo que no es lo que creías. `spec=` lo evita:

```python
from unittest.mock import MagicMock
from dominio.repositorios.jugador_repositorio import JugadorRepositorio

repo_falso = MagicMock(spec=JugadorRepositorio)
repo_falso.buscar_por_dnii(123)   # AttributeError: no existe ese método en JugadorRepositorio
```

- `spec=Clase`: solo se pueden **leer/llamar** los atributos que tiene `Clase`.
- `spec_set=Clase`: además **no se pueden asignar** atributos nuevos (más estricto).
- `create_autospec(Clase)`: además verifica que las **firmas** coincidan (si el método real pide 2 argumentos y lo llamás con 3, falla).

**Recomendación:** usar siempre `spec=` cuando se mockea algo con una interfaz real (como `JugadorRepositorio`). Es casi gratis y evita una categoría entera de tests rotos en silencio.
Si el contrato cambia (se renombra un método del repositorio), los tests que lo usan fallan **antes** de que el error llegue a producción.

### 3.3 `return_value` y `side_effect`

- **`return_value`:** siempre devuelve lo mismo, sin importar los argumentos.
- **`side_effect`:** hace algo distinto en cada llamada. Según lo que se le asigne:
  - una **excepción** (clase o instancia) → el mock la **lanza** (así se simula "esto falla");
  - una **lista** → devuelve un elemento distinto por cada llamada, en orden;
  - una **función** → se ejecuta con los argumentos recibidos y su resultado es lo que se devuelve.

```python
# Simular que el repositorio real detecta un DNI repetido (tests/unit/test_uc_jugadores.py)
repo_jugador.guardar.side_effect = DNIDuplicadoError("Ya existe un jugador con DNI 20111222")

# Devolver algo distinto en cada llamada
repo_falso.buscar_por_id.side_effect = [Jugador(...), None]     # 1ª llamada: un jugador. 2ª: None

# Lógica condicional
repo_falso.buscar_por_dni.side_effect = lambda dni: Jugador(...) if dni == 12351689 else None
```

**`configure_mock`** permite configurar varias cosas de una vez con claves punteadas (así lo hacen los tests de comandos de la CLI):

```python
repo = MagicMock(spec=ClubRepositorio)
repo.configure_mock(**{"guardar.return_value": Club("Atenas", idClub=3)})
```

### 3.4 Verificar las llamadas (la parte "Mock" del Mock)

```python
repo.guardar.assert_called_once()                      # se llamó exactamente una vez
repo.guardar.assert_called_once_with(club=Club("Atenas"))   # ... y con exactamente esos argumentos
repo.link_to_club.assert_not_called()                  # nunca se llamó
repo.guardar.call_count                                # cuántas veces se llamó
repo.guardar.call_args                                 # con qué argumentos fue la última llamada
```

Esto es lo que un Fake no da gratis: el Mock es la herramienta cuando lo que importa verificar es **la interacción** ("¿el caso de uso le pasó al repositorio la entidad correcta?"),
y sobre todo lo que **no** debe pasar: `assert_not_called()` demuestra que ante un dato inválido el caso de uso **cortó antes** de intentar guardar.

> Las entidades son `dataclass`, así que se comparan **por valor**: `assert_called_once_with(jugador=Jugador("Manu", "Ginobili", 20111222, 1977))` funciona
> aunque no sea el mismo objeto en memoria.

### 3.5 `patch` vs `monkeypatch`: cuando el código crea su propia dependencia

Ambos sirven para **reemplazar algo temporalmente** durante un test (y lo restauran solos al terminar):

- **`unittest.mock.patch("modulo.nombre")`:** reemplaza un nombre por un mock. Se usa como `with patch(...)` o como decorador.
- **`monkeypatch` (fixture de pytest):** reemplaza atributos, variables de entorno o `sys.argv`; sin `with`, se restaura al terminar el test.

```python
# tests/unit/test_cli_main.py: main() no debe tocar la base real, así que se reemplaza inicializar_db
monkeypatch.setattr(main, "inicializar_db", lambda: None)
monkeypatch.setattr(sys, "argv", ["stats", "club", "add", "--nombre", "Atenas"])
```

Con Inyección de Dependencias bien aplicada, **casi nunca hace falta `patch`**: al caso de uso o al comando se le pasa el repositorio falso por parámetro. Si se encuentran necesitando
`patch` seguido, suele ser señal de que esa clase debería recibir la dependencia por constructor. En el proyecto se usa `monkeypatch` solo para lo que es global por naturaleza:
`sys.argv`, la ruta de la base (`rutas.DB_FILE`) y funciones de arranque como `inicializar_db`.

---

## 4. Ejemplo completo: testear un caso de uso

Dos versiones del mismo test: con **Mock** (lo que usa el proyecto, en `tests/unit/test_uc_jugadores.py`) y con **Fake** (alternativa).

### 4.1 Con Mock (verificando la interacción)

```python
from unittest.mock import MagicMock
import pytest

from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.dtos.jugador_dto import CrearJugadorDTO, JugadorDTO
from dominio.entidades.jugador import Jugador
from dominio.exceptions import DNIDuplicadoError
from dominio.repositorios.jugador_repositorio import JugadorRepositorio


@pytest.fixture
def repo_jugador():
    return MagicMock(spec=JugadorRepositorio)


def test_registrar_jugador_devuelve_el_dto_con_el_id_asignado(repo_jugador):
    # Arrange: el repositorio "guarda" y devuelve el jugador con su id
    repo_jugador.guardar.return_value = Jugador("Manu", "Ginobili", 20111222, 1977, idJugador=7)
    dto = CrearJugadorDTO(nombre="Manu", apellido="Ginobili", dni=20111222, anioNacimiento=1977)

    # Act
    resultado = RegistrarJugadorUseCase(repo_jugador).ejecutar(dto)

    # Assert: el resultado y la interacción
    assert resultado == JugadorDTO(nombre_completo="Manu Ginobili", id=7, anioNacimiento=1977)
    repo_jugador.guardar.assert_called_once_with(jugador=Jugador("Manu", "Ginobili", 20111222, 1977))


def test_registrar_jugador_con_dni_duplicado_deja_subir_la_excepcion(repo_jugador):
    repo_jugador.guardar.side_effect = DNIDuplicadoError("Ya existe un jugador con DNI 20111222")
    dto = CrearJugadorDTO(nombre="Manu", apellido="Ginobili", dni=20111222, anioNacimiento=1977)

    with pytest.raises(DNIDuplicadoError, match="20111222"):
        RegistrarJugadorUseCase(repo_jugador).ejecutar(dto)
```

### 4.2 Con Fake (una implementación real y simplificada)

```python
class JugadorRepositorioFake(JugadorRepositorio):
    """Repositorio en memoria: cumple la interfaz real, sin tocar SQLite."""

    def __init__(self):
        self._jugadores: dict[int, Jugador] = {}

    def buscar_por_dni(self, dni_jugador):
        return next((j for j in self._jugadores.values() if j.dni == dni_jugador), None)

    def guardar(self, jugador):
        if self.buscar_por_dni(jugador.dni) is not None:
            raise DNIDuplicadoError(f"Ya existe un jugador con DNI {jugador.dni}")
        id_nuevo = len(self._jugadores) + 1
        guardado = Jugador(jugador.nombre, jugador.apellido, jugador.dni, jugador.anioNacimiento, idJugador=id_nuevo)
        self._jugadores[id_nuevo] = guardado
        return guardado

    # ... y hay que implementar TODOS los métodos abstractos de la interfaz (buscar_por_id, buscar_por_club, link_to_club, club_activo)
```

**¿Cuándo usar cada uno?** El **Mock** cuando lo único que importa es **qué le pasaron a un método puntual** o que **no** lo llamaron; no hace falta escribir una clase.
El **Fake** cuando la prueba necesita que el repositorio se comporte bien a través de **varias llamadas** (guardar y después poder buscar lo guardado); a cambio, hay que implementar
todos los métodos abstractos de la interfaz aunque el test no los use. En este proyecto ganó el Mock porque cada test necesita pocas respuestas puntuales.

---

## 5. Tests de excepciones de dominio

**Qué son:** las excepciones de dominio (`src/dominio/exceptions.py`) son los **errores de negocio esperables**: `DNIDuplicadoError`, `ClubNoEncontradoError`, `VinculoActivoExistenteError`…
Todas heredan de `ErrorDeDominio`. No son bugs: son la forma en que una regla de negocio dice "esto no está permitido".

**Por qué se testean:** cada regla de negocio de un caso de uso tiene dos caminos: el que funciona y el que la rompe. Si solo se prueba el primero, la regla **no está probada**
(y es común que la cobertura muestre el `raise` sin cubrir).

### 5.1 `pytest.raises`: la herramienta

```python
import pytest

def test_vincular_jugador_con_club_activo_lanza_excepcion(repo_jugador, repo_club):
    _preparar_vinculo(repo_jugador, repo_club, club_activo=Club("Instituto", idClub=9))

    with pytest.raises(VinculoActivoExistenteError, match="idClub=9"):
        VincularJugadorAClubUseCase(repo_jugador, repo_club).ejecutar(_dto_vinculo())

    repo_jugador.link_to_club.assert_not_called()      # ...y NO se guardó nada
```

Tres cosas para fijarse:

1. **El tipo:** `pytest.raises(VinculoActivoExistenteError)` falla si se lanza *otra* excepción o si **no se lanza ninguna**.
2. **El mensaje, con `match=`:** es una expresión regular que se busca en el mensaje (`str(excepcion)`). Sirve para asegurar que la excepción es **por el motivo correcto**
   (por ejemplo, que el error habla del club 9 y no de otro).
3. **El efecto secundario que NO debe ocurrir:** `assert_not_called()` demuestra que la regla **cortó antes de guardar**. Es la mitad más importante del test.

Si necesitás inspeccionar la excepción (no solo su mensaje): `with pytest.raises(X) as info:` y luego `info.value` (la instancia) o `info.value.code` (útil con `SystemExit`).

### 5.2 Qué probar en cada caso de uso

| Qué | Cómo | Ejemplo real |
| --- | --- | --- |
| Cada regla de negocio lanza **su** excepción | Un caso por regla, con el mock configurado para romperla | `test_uc_competencias.py`: club/competencia/categoría inexistente y duplicado, `parametrize` con 4 casos |
| La excepción **sube**, no se traga | El caso de uso no la atrapa (la atrapa `main()`) | `test_registrar_jugador_con_dni_duplicado_deja_subir_la_excepcion` |
| Ante el error, **no se guarda nada** | `assert_not_called()` sobre el método de escritura | Todos los `test_*_lanza_excepcion_y_no_guarda` |
| El repositorio **falló** (devuelve `None`) | No es excepción de dominio: el caso de uso devuelve `None` | `test_crear_club_devuelve_none_si_el_repositorio_no_pudo_guardar` |

### 5.3 Testear la jerarquía de excepciones

`tests/unit/test_exceptions.py` verifica la **estructura**: que toda excepción de `dominio/exceptions.py` herede de `ErrorDeDominio` y que se pueda capturar con la clase base
conservando su mensaje. Es lo que permite que `main()` use **un único** `except ErrorDeDominio`. El test descubre las clases con `inspect.getmembers`, así que
**si mañana alguien agrega una excepción nueva que olvide heredar de `ErrorDeDominio`, el test falla solo**, sin tener que actualizarlo.

### 5.4 Cuándo NO usar `pytest.raises`

- Para errores que **no** son de negocio (un bug real, como el `RuntimeError` de `id_persistido`): se testean para asegurar que **no** se esconden (ver `test_main_no_esconde_los_errores_que_no_son_de_dominio`).
- Para "cualquier excepción" (`pytest.raises(Exception)`): es demasiado laxo, pasaría con cualquier error, incluso uno inesperado. Siempre la clase más específica posible.

---

## 6. `@pytest.mark.parametrize`: muchos casos, un solo test

**Qué es:** un decorador que **ejecuta el mismo test varias veces**, cada vez con valores distintos. En el reporte cada combinación aparece como un test independiente.

**Para qué sirve:** cuando la lógica es la misma y solo cambian los datos (varias entradas inválidas, varios límites). Evita copiar y pegar el test 10 veces, y cuando una combinación falla
se ve **cuál** exactamente.

### 6.1 Uso básico

```python
import pytest

@pytest.mark.parametrize("anio", [1900, 1899, 1000, 0, -5])
def test_competencia_anio_menor_o_igual_a_1900_lanza_value_error(anio):
    with pytest.raises(ValueError):
        Competencia(nombre="Liga Vieja", anio=anio)
```

Esto genera 5 tests: el nombre del parámetro (`"anio"`) tiene que coincidir con el argumento de la función.

### 6.2 Varios parámetros y `pytest.param(..., id=)`

Con varios parámetros, se pasa el nombre separado por comas y una lista de tuplas. `pytest.param` permite ponerle un **`id` legible** a cada caso (aparece en el reporte y en `-k`):

```python
@pytest.mark.parametrize(
    "overrides, fragmento_del_mensaje",
    [
        pytest.param({"minutosJugados": 48.1}, "Minutos", id="minutos-mayor-a-48"),
        pytest.param({"puntos": 10}, "Puntos", id="puntos-no-coinciden-con-los-tiros"),
        pytest.param({"asistencias": -1}, "Asistencias", id="asistencias-negativas"),
    ],
)
def test_boxscore_que_rompe_una_regla_lanza_value_error(crear_boxscore, overrides, fragmento_del_mensaje):
    with pytest.raises(ValueError, match=fragmento_del_mensaje):
        crear_boxscore(**overrides)
```

(del archivo real `tests/unit/test_entidad_jugador_partido.py`). El reporte muestra `test_boxscore_que_rompe_una_regla_lanza_value_error[minutos-mayor-a-48]` en vez de `[overrides0-Minutos]`.
Convención del proyecto: **ids sin tildes ni ñ** (salen escapados en algunos reportes).

### 6.3 Combinar con fixtures y con listas generadas

Los parámetros conviven con las fixtures (`crear_boxscore` arriba viene de `conftest.py`). Y la lista de casos puede **construirse con código**: `tests/unit/test_entidades.py`
arma un caso por cada campo de cada entidad a partir de una tabla `ENTIDADES`, generando decenas de tests con una sola función:

```python
CASOS_INVALIDOS = [
    pytest.param(clase, validos, campo, valor, id=f"{clase.__name__}.{campo}={valor!r}")
    for clase, validos, invalidos in ENTIDADES
    for campo, valor in invalidos.items()
]

@pytest.mark.parametrize("clase, validos, campo, valor", CASOS_INVALIDOS)
def test_entidad_con_tipo_invalido_lanza_type_error(clase, validos, campo, valor):
    with pytest.raises(TypeError, match=f"recibido {type(valor).__name__}"):
        clase(**{**validos, campo: valor})
```

Si se apilan **dos** `@parametrize`, pytest prueba **todas las combinaciones** (producto cartesiano).

### 6.4 Cuándo NO usarlo

- Si los casos necesitan **lógica distinta** en el cuerpo del test (un `if` para cada caso): son tests distintos, escribilos por separado.
- Si un solo test tiene 30 casos ilegibles: agrupar en varios tests parametrizados con nombre claro (uno por regla).
- Si dos casos comparten **un setup caro** (armar una base): usar una fixture (sección 8) o un test aparte.

---

## 7. El patrón `**overrides`: fábricas de datos de prueba

**El problema:** un `JugadorPartido` tiene **20 campos**. Para probar que "un boxscore con `idJugador` inexistente no se guarda", hay que construir uno válido completo y cambiar **un solo dato**.
Antes de este patrón, `test_repositorios_partido.py` copiaba los 20 campos **cinco veces**: 120 líneas donde lo único que cambiaba era una línea. Ruido difícil de leer, y si una regla nueva
exigía un campo más, había que editar cinco lugares.

**La solución:** una **fábrica** (una función que arma una entidad válida con valores por defecto) que acepta `**overrides`: los campos que el test quiere **pisar**.
En Python, `**overrides` recolecta cualquier argumento con nombre en un diccionario.

```python
# tests/conftest.py
@pytest.fixture
def crear_boxscore():
    def _crear(**overrides) -> JugadorPartido:
        datos = {"idJugador": 1, "idPartido": 2, "idClub": 1, "minutosJugados": 20.0, "puntos": 9,
                 "t2c": 2, "t2l": 5, "t3c": 1, "t3l": 5, "t1c": 2, "t1l": 5,
                 # ... el resto de los campos con valores válidos ...
                 }
        return JugadorPartido(**{**datos, **overrides})      # los overrides pisan a los defaults
    return _crear
```

`{**datos, **overrides}` mezcla dos diccionarios: si una clave está en los dos, **gana la de `overrides`**.

**Cómo se usa en un test:** solo se nombra lo que importa.

```python
def test_guardar_boxscore_con_referencia_inexistente_devuelve_none(db_conexion, crear_boxscore):
    boxscore = crear_boxscore(idJugador=40000)        # todo válido, salvo el jugador
    assert SqlitePartidoRepositorio(db_conexion).guardar_boxscore(boxscore=boxscore) is None
```

Se lee de un vistazo qué se está probando. Fábricas disponibles: `crear_jugador`, `crear_partido`, `crear_boxscore`.

**Se combina con `parametrize`:** el parámetro es directamente el diccionario de overrides (así están escritos los tests de reglas del boxscore, ver 6.2).

**Cuidados:**

- **Campos derivados:** en `crear_boxscore`, `puntos` tiene que ser `t2c*2 + t3c*3 + t1c`. Si el test cambia `t2c`, **tiene que pisar también `puntos`**; si no, falla por *otra* regla
  y el test prueba algo distinto de lo que dice. (Por eso los casos de `T2C > T2L` traen `puntos` explícito.)
- **Defaults válidos y estables:** la fábrica nunca debe devolver algo inválido por defecto, o todos los tests que la usan se rompen a la vez.
- **Cuándo NO usarlo:** una entidad de 2 o 3 campos no necesita fábrica (`Club("Atenas")` alcanza).

---

## 8. Fixtures y `conftest.py`

**Qué es una fixture:** una función marcada con `@pytest.fixture` que **prepara algo que el test necesita** (una conexión, un repositorio falso, datos). El test la pide **poniendo su nombre como parámetro**
y pytest se la entrega. Reemplaza al típico `setUp`/`tearDown`.

```python
@pytest.fixture
def db_conexion():
    conexion = sqlite3.connect(":memory:")     # <- preparar
    # ... crear esquema y seed ...
    yield conexion                             # <- el test corre acá, usando la conexión
    conexion.close()                           # <- limpiar (siempre se ejecuta al terminar)
```

- **`yield`:** lo de antes es la preparación; lo de después, la limpieza.
- **`conftest.py`:** las fixtures que están ahí se comparten con **todos** los tests de esa carpeta y sus subcarpetas, sin importarlas.
- **Cada test recibe una fixture nueva** (alcance por defecto: función): las bases en memoria se recrean por test, así ningún test depende de lo que dejó otro.

Fixtures del proyecto:

| Fixture | Qué entrega |
| --- | --- |
| `db_conexion` | SQLite en memoria con esquema, vistas y **seed** (datos de ejemplo) |
| `db_conexion_sin_seed` | Igual pero **vacía** (para probar restricciones sin datos previos) |
| `crear_jugador`, `crear_partido`, `crear_boxscore` | **Fábricas** de entidades válidas (sección 7) |
| `repo_jugador`, `repo_club`… | (definidas en cada archivo de test) `MagicMock(spec=...)` del repositorio |

Fixtures **nativas** de pytest que se usan mucho: `tmp_path` (carpeta temporal), `monkeypatch` (reemplazos temporales) y `capsys` (captura de lo impreso, sección 9).

---

## 9. Testeando comandos CLI (`ejecutar`, `main()` y de punta a punta)

> **Aviso (2026-10-31):** la CLI y sus tests se borran en la **US-105**. Esta sección queda como referencia hasta entonces; en la GUI, la lógica se testea en los casos de uso y en el `SessionManager`, y las pantallas se mantienen finas (ver la US-105 en el PRD).

Hay tres niveles, del más chico al más grande:

### 9.1 El comando solo: `Namespace` a mano + repo falso + `capsys`

No hace falta simular una terminal: `argparse.Namespace` es solo un objeto con atributos, y se le inyecta un repositorio falso.

```python
def test_club_add_informa_el_club_creado(capsys):
    repo = MagicMock(spec=ClubRepositorio)
    repo.configure_mock(**{"guardar.return_value": Club("Atenas", idClub=3)})

    club_add.ejecutar(argparse.Namespace(nombre="Atenas"), repo)      # sin sys.argv ni terminal

    assert capsys.readouterr().out == "Club creado: Atenas (id=3)\n"
```

**`capsys`** es una fixture nativa que **captura lo que se imprimió**. `capsys.readouterr()` devuelve `.out` (stdout) y `.err` (stderr): los errores van a `err` y los mensajes normales a `out`,
y los tests verifican cada uno por separado.

**Es testeable porque el comando recibe el repositorio como parámetro** (`ejecutar(args, repo=None)`): en producción no se pasa y arma el real; en los tests se inyecta uno falso.
Si el comando armara la conexión SQLite adentro sin forma de reemplazarla, cada test tocaría la base real.

### 9.2 Comandos que terminan el programa: `SystemExit`

`abortar()` llama a `sys.exit(1)`. En un test, eso se captura con `pytest.raises(SystemExit)` y se mira el código:

```python
with pytest.raises(SystemExit) as info:
    competencia_add.ejecutar(argparse.Namespace(nombre="Vieja", anio=1900, tipo=None), repo)

assert info.value.code == 1
assert capsys.readouterr().err.startswith("Error:")      # el mensaje va a stderr, sin traceback
```

Convención de códigos de salida: **0** = éxito, **1** = error de negocio, **2** = uso incorrecto de la CLI (lo devuelve `argparse` solo).

### 9.3 El parser y `main()`

`tests/unit/test_cli_main.py` prueba (sin base de datos) que el parser asocia cada comando con su función y que `main()` traduce los errores:

```python
args = main.construir_parser().parse_args(["club", "add", "--nombre", "Atenas"])
assert args.func is club_add.ejecutar and args.nombre == "Atenas"
```

Pasarle una lista a `parse_args()` hace que lea esa lista en vez de `sys.argv`: el test no depende de cómo se ejecutó pytest. Para `main()`, se reemplaza `sys.argv` con `monkeypatch`
y se neutraliza `inicializar_db` para **no tocar nunca la base real**.

### 9.4 De punta a punta (E2E) con una base temporal

`tests/integration/test_cli_e2e.py` corre `main()` completo contra un archivo SQLite en `tmp_path`, simulando ejecuciones sucesivas del programa. La ruta de la base se cambia con
`monkeypatch.setattr(rutas, "DB_FILE", ...)`. Este nivel encontró un bug real: cada arranque borraba los datos (el `schema.sql` tenía `DROP TABLE`), algo que ningún test unitario podía ver.

---

## 10. Cobertura (`coverage`)

`make run_test` corre `pytest -v --cov=src --cov-report=html`, que genera un reporte HTML navegable en `reportes_cobertura/html/index.html`. El piso mínimo (`fail_under = 60`) está en `[tool.coverage.report]` de `pyproject.toml`; el job de Linux del CI exige además **85 %** (parámetro `cobertura-minima` de `.github/actions/coverage/linux/action.yml`) y guarda el reporte HTML como _artifact_. Ideas para leerlo bien:

- **El % global importa menos que las líneas rojas específicas**: un 85% con las ramas de error sin cubrir es peor que un 80% donde solo falta un `print` cosmético.
- Prestar atención a que estén cubiertas **las dos ramas** de cada caso de uso: la del camino feliz y la del `raise` de la excepción de dominio.
- Cobertura alta **no prueba que la lógica sea correcta**: solo que esa línea se ejecutó. Un test sin `assert` significativo da 100% y no prueba nada. Es una red para encontrar código que **nadie**
  está probando, no un reemplazo de pensar los casos (para eso están los tests de mutación, sección 1).

---

## 11. Buenas prácticas

- **Arrange–Act–Assert:** armar los datos, ejecutar la acción bajo prueba, verificar el resultado, en ese orden y como bloques separados.
- **Nombres descriptivos:** `test_vincular_jugador_que_rompe_una_regla_lanza_excepcion_y_no_guarda` dice qué se prueba y qué se espera con solo leerlo.
- **Un test, una razón de fallar:** varios `assert` sobre el **mismo** resultado están bien (`nombre`, `apellido`, `dni` del mismo jugador); no mezclar comportamientos distintos en un test.
- **Tests deterministas:** nada de `datetime.now()` sin fijar ni `random` sin semilla. Si un test falla "a veces" sin que cambie el código, el problema está en el test.
- **Independientes entre sí:** cada test arma su estado desde cero; nunca asume que otro corrió antes (por eso las fixtures recrean la base en cada test).
- **Un bug corregido = un test de regresión:** antes de dar por cerrado un arreglo, escribir el test que lo habría detectado y comprobar que **falla sin el arreglo**.
- **Verificar que el test puede fallar:** romper a propósito el código un momento y confirmar que el test lo detecta (mutación a mano). Un test que nunca falla no protege nada.
- **No testear la librería:** no hace falta probar que `argparse` convierte `"5"` en `5`; sí que el parser del proyecto asocia el argumento correcto al comando.

---

## 12. Checklist: agregar un caso de uso o un comando nuevo

Por cada **caso de uso** nuevo (en `tests/unit/`):

- [ ] Test del **camino feliz**, con `MagicMock(spec=<Repositorio>)`, verificando el DTO devuelto y `assert_called_once_with` sobre el repositorio.
- [ ] Un test por **cada excepción de dominio** que pueda lanzar (con `match=` y `assert_not_called()` sobre la escritura); agrupables con `@parametrize`.
- [ ] El caso en que el repositorio devuelve `None` (no pudo guardar) o una lista vacía.
- [ ] Si hace más de una escritura (como `InscribirClubEnCompetenciaUseCase`), un test **de integración** del método del repositorio que confirme la **atomicidad**: forzar que la segunda escritura falle y comprobar que la primera tampoco quedó.

Por cada **comando de la CLI**:

- [ ] En `test_cli_comandos.py`: mensaje de éxito (con `capsys`) y el caso de "el repositorio no pudo guardar" (`SystemExit` con código 1 y mensaje en stderr).
- [ ] En `test_cli_main.py`: que el parser asocia el comando con su función y con los tipos correctos, y qué pasa si faltan argumentos.
- [ ] Si lista datos: que la salida sea una tabla y que el caso "sin resultados" muestre un aviso.
- [ ] En `test_cli_e2e.py`: sumarlo al recorrido completo si es parte de un flujo importante.

Por cada **entidad o regla de dominio** nueva:

- [ ] `@parametrize` con un caso por regla (usando la fábrica `**overrides` si la entidad tiene muchos campos) y el caso **límite** de cada rango (el valor justo permitido y el justo prohibido).
