# Informe de sesión (2026-11-08): US-105, GUI base con Flet y retiro de la CLI

> **Para quién es este documento:** para cualquier integrante del equipo que no estuvo en la sesión y quiera entender **qué cambió, por qué y qué
> decisiones se tomaron**. Los conceptos de Flet (handlers, rutas, `View`, router) están explicados en
> [13-gui-flet-y-eventos.md](../info_modulo/13-gui-flet-y-eventos.md); este informe no los repite.
>
> **Rama:** `feature/us105`. **Autor:** Nico, trabajando con un asistente de IA (Claude). Los cambios están en el árbol de trabajo **sin commitear**.

## 1. Resumen

La interfaz del sistema pasó de una CLI (`argparse`) a una app de escritorio con **Flet 1.1.2**. Hoy se puede crear una cuenta, iniciar sesión y
cerrarla. Toda la CLI (comandos, formatter, scripts de bash y sus tests) se borró. Dominio, casos de uso, DTOs y repositorios **no cambiaron**:
solo se cambió el adaptador de entrada (`ui/`), que es lo que la arquitectura limpia promete.

**Qué hay que hacer al bajar estos cambios:**

1. `uv sync`: el lock cambió (sale `tabulate`, entra `flet[desktop]`). La primera vez que se abre la app, Flet descarga su cliente de escritorio.
2. Python **3.12 o más**: el mínimo subió de 3.11 (ver la sección 3).
3. Abrir la app con `uv run python src/main.py` y hacer la prueba manual de la sección 6.

## 2. Qué se hizo, paso por paso

| Paso | Qué | Archivos principales |
| --- | --- | --- |
| 1 | `SessionManager` en memoria: iniciar, cerrar (idempotente), `is_authenticated`, `usuario_actual` | `aplicacion/servicios/session_manager.py` |
| 2 | Dependencia `flet[desktop]==1.1.2` y esqueleto de la app | `pyproject.toml`, `uv.lock` |
| 3 | Composition root: `Dependencias` + `construir_dependencias` + `ejecutar()` | `ui/flet/app.py`, `test_sesion_flujo.py` |
| 4 | Rutas, ruta protegida (`resolver_ruta`) y router (`on_route_change`) | `ui/flet/app.py`, `test_navegacion.py` |
| 5 | Manejador común de errores de los handlers | `ui/flet/errores.py`, `test_errores.py` |
| 6 | Pantalla de registro | `screens/registro_screen.py`, `test_registro_screen.py` |
| 7 | Pantalla de login | `screens/login_screen.py`, `test_login_screen.py` |
| 8 | Pantalla de inicio con "Cerrar sesión" en la `AppBar` | `screens/inicio_screen.py`, `test_inicio_screen.py` |
| 9 | Test de integración registro → login → sesión (hecho en el paso 3) | `test_sesion_flujo.py` |
| 10 | Borrado de la CLI, `scripts/`, sus tests, `abortar`, `fecha_iso`, `abrir_conexion` y `tabulate`; `main.py` solo llama a `ejecutar()` | `src/main.py`, `src/utils.py`, `database_manager.py` |
| 11 | Lo que cubría `test_cli_e2e.py` pasó a tests de casos de uso | `test_flujo_casos_de_uso.py` |
| 12 | Smoke test del CI: `python -c "import main"` en vez de `main.py --help` | `.github/actions/coverage/{linux,windows}/action.yml`, ADR-009 |
| 13 | Documentación | README, RUNBOOK, guías 03, 04, 05, 06, 08, 09, 13, `ideas-aprendizaje.md`, PRD |

## 3. Decisiones y alternativas

| Decisión | Alternativas descartadas | Por qué |
| --- | --- | --- |
| `Dependencias` guarda **solo** la sesión y los casos de uso | Guardar también conexión, repositorios y hasher | Si una pantalla tuviera un repositorio, podría guardar datos salteándose las reglas del caso de uso |
| Cada pantalla recibe **solo** lo que usa (`crear_login_view(page, login_uc, sesion)`) | Pasarle `Dependencias` entero | Se ve en la firma qué usa cada pantalla y los tests arman menos mocks |
| Pantallas como **funciones** que devuelven `ft.View`, con handlers como _closures_ | Una clase por pantalla | Sin estado propio que justifique una clase; las closures ya recuerdan los campos |
| Ruta protegida como **función pura** (`resolver_ruta`) separada del router | El `if` adentro del router | Se testea con `parametrize`, sin ventana ni mocks |
| Errores debajo del formulario, en un `ft.Text` | `TextField.error_text` por campo; `SnackBar` | `DatoInvalidoError` no dice qué campo falló; un `SnackBar` se borra solo y el error hay que corregirlo |
| `except Exception` en `ejecutar_mostrando_errores` con `logger.exception` | Dejar que la excepción suba | Si sube, Flet muestra el traceback en la ventana y la sesión queda rota. Es el borde de la app: el bug no se esconde, queda en `logs/app.log` |
| Pantallas testeadas sin ventana (`MagicMock(spec=ft.Page)` + llamar al handler) | Solo prueba manual; herramientas de UI | Flet no tiene un harness maduro; con `page` por parámetro y handlers sin argumentos alcanza con mocks |
| Python mínimo 3.12 | Override de mypy para numpy; quedarse en 3.11 | Los _stubs_ de numpy usan la sentencia `type` de 3.12; el override no alcanzaba |
| `flet[desktop]` en vez de `flet` | `flet` solo | Sin el extra, Flet instala `flet-desktop` por su cuenta al arrancar, fuera del lock |
| Login con un solo mensaje para "email inexistente" y "contraseña incorrecta" | Mensajes distintos | Evita la **enumeración de usuarios** (averiguar quién tiene cuenta). La regla ya estaba en `LoginLocalUseCase` |
| Inicio sin menú | Un menú vacío | No hay secciones todavía; llega con las US-106 y US-107 |

## 4. Hallazgos e incidentes

- **Un test abrió la ventana real.** `test_auth_flujo.test_flujo_cli_auth_e2e` llamaba a `main.main()`. Con la CLI eso corría un comando y
  terminaba; con la GUI abrió la ventana de Flet y la corrida de pytest se colgó. Se borró ese test (su caso de login fallido pasó a
  `test_sesion_flujo.py`) y se agregó en `tests/conftest.py` una fixture `autouse` que reemplaza `flet.run` por una función que falla.
- **`RegistrarEntrenadorUseCase` devuelve `UsuarioDTO | None`** porque `SqliteUsuarioRepositorio.guardar` atrapa `sqlite3.Error` y devuelve
  `None`. La pantalla lo trata como bug (`RuntimeError` → mensaje genérico + traceback en el log). Queda como deuda: el repositorio se traga
  el error original, así que el log no dice qué falló en SQLite.
- **`ft.TextButton` no hereda de `ft.Button`** en Flet 1.1.2: el ayudante de tests busca los dos tipos.
- **`ft.app` y `page.go` no existen en Flet 1.x** (son de 0.x, y mucho material en internet todavía los usa). En 1.x: `ft.run` y `page.navigate`.
- **Hilos:** en Flet 1.x el bucle de eventos corre en el hilo principal y los handlers síncronos también, así que una sola conexión SQLite sirve
  para toda la app.

## 5. Estado de la verificación

Corrida sobre una copia del repositorio (no sobre la carpeta real, que comparten Windows y WSL): pytest con cobertura sobre el mínimo del CI,
`mypy` estricto, `ruff check`, `ruff format --check` y el smoke test `import main`, que no crea la base. Lo que **no** se cubre con
tests automáticos: `ejecutar()` (abre la ventana) y cómo se ven las pantallas.

## 6. Prueba manual pendiente (AC1 a AC4)

1. `uv run python src/main.py`: abre en el login en pocos segundos (la primera vez tarda más por la descarga del cliente).
2. "Crear cuenta" → registrarse: entra directo al inicio y saluda con el nombre.
3. "Cerrar sesión" → vuelve al login con los campos vacíos.
4. Login con contraseña equivocada y con un email que no existe: el mismo mensaje en los dos casos.
5. Registro con email repetido, email inválido, nombre vacío y contraseña de menos de 8 caracteres: mensaje en rojo, la app sigue abierta.
6. Enter en el campo de la contraseña equivale al botón (login y registro).
7. La contraseña se ve oculta y el ícono del ojo la muestra.
8. Revisar `logs/app.log`: no aparece ninguna contraseña.

## 7. Próximos pasos

- Prueba manual, commits chicos y PR de la US-105.
- US-106: "Recordarme" (sesión en `~/.statspro/session.json`) y club activo, sobre el mismo `SessionManager`.
- Evaluar que `SqliteUsuarioRepositorio.guardar` deje subir o loguee el `sqlite3.Error` en vez de devolver `None` sin rastro.
