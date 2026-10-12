# Docker para correr los tests

Esta guía explica **qué problema resuelve Docker** en este proyecto, **qué hace cada línea** del `Dockerfile.test` real y cómo usarlo. Es el mismo mecanismo que corre
en el CI (job `tests-docker` de `.github/workflows/MainAction.yml`).

## El problema que resuelve

Para correr los tests alguien necesita: Python instalado (¿qué versión exacta?), las dependencias instaladas (con las versiones correctas) y que su sistema operativo no tenga
ninguna diferencia rara con el de otro miembro del equipo. "En mi máquina funciona" es el síntoma clásico de no tener esto resuelto.

**Docker** empaqueta "el proyecto + todo lo que necesita para correr" en una **imagen** (un molde inmutable) que después se ejecuta como **contenedor** en cualquier máquina
que tenga Docker instalado, sin importar qué versión de Python tenga esa máquina por fuera. La idea: *empaquetar las dependencias exactas una vez y correr siempre igual en cualquier lado*.

## Los archivos del proyecto

### 1. `Dockerfile.test`

Define, paso a paso, cómo se construye la imagen. Cada instrucción crea una **capa** que Docker guarda en caché:

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim
```
**Imagen base:** ya trae Python instalado, sin todo el peso de una distribución Linux completa (por eso `slim`).
La versión de Python es un **argumento de construcción** (`ARG`): por defecto es la 3.11 (la mínima que soporta el proyecto) y se cambia al construir con `--build-arg PYTHON_VERSION=3.13`.
El CI construye la imagen una sola vez, con la 3.13 (las demás versiones de Python se prueban en el job de Linux). (Un `ARG` declarado *antes* del `FROM` es la forma de parametrizar la imagen base.)

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv
```
**Instala `uv`** (la herramienta que instala las dependencias) copiando el binario desde su imagen oficial. La versión está fijada para que el build sea reproducible.

```dockerfile
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project
```
**Instala las dependencias primero, copiando solo dos archivos.** Esto no es un capricho: como Docker cachea cada capa, mientras `pyproject.toml` y `uv.lock` no cambien, este paso
(el más lento) se **reusa** sin reinstalar nada. Si se copiara todo el código antes, cualquier cambio en un `.py` invalidaría el caché y habría que reinstalar todo cada vez.

- `--locked`: falla si `uv.lock` no coincide con `pyproject.toml` (garantiza las versiones exactas del lockfile).
- `--no-install-project`: instala solo las **dependencias**; el código propio se usa directo desde `src/` (así lo configura `pytest.ini` con `pythonpath = src`).

```dockerfile
ENV PATH="/app/.venv/bin:$PATH"
COPY . .
CMD ["pytest", "-v", "--cov=src", "--cov-report=term"]
```
**Deja el entorno virtual de uv en el `PATH`** (así `pytest` se resuelve sin anteponer nada), **copia el resto del proyecto** y define el **comando por defecto**: al correr el contenedor
sin argumentos, ejecuta los tests con cobertura en la terminal.

### 2. `.dockerignore`

Igual que un `.gitignore`, pero para decirle a Docker qué **no** copiar dentro de la imagen. Evita meter basura que infla la imagen o **rompe** el build:

| Entrada | Por qué se excluye |
| --- | --- |
| `.venv/` | El entorno virtual local es de **Windows** (o de otro sistema): copiarlo a una imagen Linux no sirve y la pisaría al instalar |
| `.git/` | Todo el historial, sin ninguna utilidad dentro de la imagen |
| `*.db`, `logs/` | Datos locales de desarrollo que no deben viajar en la imagen |
| `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.coverage/`, `reportes_cobertura/` | Cachés y reportes generados |

## Cómo se usa

```bash
docker build -f Dockerfile.test -t app-estadisticas-tests .
docker run --rm app-estadisticas-tests
```

(o `make docker_test`, que hace ambos; para otra versión de Python: `make docker_test PYTHON_VERSION=3.13`, que agrega `--build-arg PYTHON_VERSION=3.13` al `docker build`). `docker build` lee el `Dockerfile.test` y arma la imagen (una vez, o cada vez que cambian las dependencias).
`docker run --rm` levanta un contenedor a partir de esa imagen, corre el comando por defecto (los tests) y `--rm` lo borra al terminar para no acumular contenedores muertos.

Para correr **otro comando** dentro del contenedor (por ejemplo solo los unitarios), se agrega al final:

```bash
docker run --rm app-estadisticas-tests pytest tests/unit -v
```

## Qué verificar para saber que está bien armado

- [ ] `docker build` termina sin errores y sin tocar nada del `Dockerfile.test` a mano.
- [ ] `docker run --rm app-estadisticas-tests` corre **los mismos tests que `uv run pytest`** fuera de Docker, con el mismo resultado (todos en verde).
- [ ] Si borrás tu entorno virtual local y corrés *solo* el contenedor, igual funciona: esa es la prueba real de que la imagen no depende de nada de tu máquina.
- [ ] Si cambiás un archivo `.py` y volvés a hacer `docker build`, el paso de instalar dependencias aparece como `CACHED` (el caché de capas funciona).
- [ ] El tamaño de la imagen (`docker images`) es razonable; si ronda varios GB, algo del `.dockerignore` no está filtrando bien.

## Para qué sirve además de "correr los tests"

- **Es lo que valida el CI en un entorno limpio:** el job `tests-docker` construye esta imagen en cada Pull Request. Un `Dockerfile.test` roto o una dependencia mal declarada en `pyproject.toml`
  se detecta en el PR, no cuando alguien lo necesita.
- **Detecta dependencias no declaradas:** si el código importa una librería que solo está instalada en tu máquina pero **no** en `pyproject.toml`, en Docker el test falla con `ModuleNotFoundError`.

## Una idea para más adelante

Cuando el proyecto tenga un `docker-compose.yml` con más de un servicio (por ejemplo, el perfil de observabilidad con Seq mencionado en el PRD), o cuando llegue el empaquetado (Hito 4),
conviene separar una imagen de **desarrollo** (con `pytest`, `ruff`, `mypy`) de una de **producción** (solo lo mínimo para que la app corra): es la técnica de *multi-stage build*.
