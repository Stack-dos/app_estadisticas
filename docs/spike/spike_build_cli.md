# Spike: Empaquetado e Instalación de la CLI

| Campo           | Valor                                                                        |
| --------------- | ---------------------------------------------------------------------------- |
| Estado          | Propuesto (no iniciado)                                                      |
| Fecha           | 2026-10-17                                                                   |
| Rama sugerida   | `spike/build-cli`                                                            |
| Timebox         | 1–2 días. Si se pasa, se corta y se documenta lo aprendido.                  |
| Relacionado con | US-404 (Empaquetado y Distribución), ADR-001 (Local-First), ADR-008 (Backup) |
| Entregable      | Este documento completado + lista de cambios a llevar a una US/tarea real    |

---

## 1. Contexto

Hoy la CLI se usa de dos formas:

- `uv run python src/main.py ...` desde la raíz del repo.
- **Desde 2026-10-17:** `uv tool install --editable .` instala el comando `statspro`
  (`[project.scripts]` en `pyproject.toml`). Ver RUNBOOK, sección 2.

La instalación editable sirve para **usar y probar la CLI ya mismo**, pero no es un build real:
el código, la base y los logs siguen viviendo en la carpeta del repo. Si se genera un wheel
(`uv build`) y se instala en otra máquina, hoy **no funcionaría bien**. Este spike investiga qué
hace falta para un paquete instalable de verdad, adelantando parte de la US-404 con riesgo bajo
(la CLI es mucho más simple de empaquetar que la GUI Flet).

## 2. Pregunta que el spike tiene que responder

> **¿Puedo generar un wheel con `uv build`, instalarlo en un entorno limpio (sin el repo) y usar
> `statspro` con la base de datos y los logs en la carpeta de datos del usuario?**

Preguntas secundarias:

1. ¿Cuánto cuesta el refactor a un paquete raíz `statspro`?
2. ¿Dónde deben vivir la DB y los logs en Windows / Linux / macOS?
3. ¿Cómo se migra la `estadisticas.db` existente de un usuario a la nueva ubicación?
4. ¿Se puede distribuir un ejecutable único (sin Python instalado)? ¿Vale la pena para la CLI?

**Fuera de alcance:** empaquetado de la GUI Flet, firma de binarios, publicación en PyPI o
tiendas, instaladores `.msi`/`.deb`.

## 3. Problemas detectados en el código actual

### 3.1 Paquetes de primer nivel con nombres genéricos

`[tool.setuptools.packages.find]` con `where = ["src"]` instala cada carpeta de `src/` como un
paquete independiente en `site-packages`:

```
site-packages/
├── aplicacion/
├── config/        ← nombre muy común: choca con otras librerías
├── dominio/
├── infraestructura/
├── main.py        ← idem
└── utils.py       ← idem
```

Si otra librería del mismo entorno trae un `config` o `utils`, uno pisa al otro. Con
`uv tool install` el entorno es aislado, así que el riesgo baja, pero sigue siendo frágil (y
`pip install` en un entorno compartido rompería).

**Solución estándar:** un único paquete raíz.

```
src/
└── statspro/
    ├── __init__.py
    ├── __main__.py      ← permite "python -m statspro"
    ├── main.py
    ├── utils.py
    ├── config/
    ├── aplicacion/
    ├── dominio/
    └── infraestructura/
```

Implica cambiar **todos** los imports (`from dominio.x import Y` → `from statspro.dominio.x
import Y`), en `src/` y en `tests/`. Es mecánico (se puede hacer con un script o con
`ruff` + búsqueda y reemplazo), pero toca muchos archivos: conviene hacerlo en un PR propio, sin
mezclar con otros cambios.

### 3.2 La base de datos y los logs se ubican relativos al código

`src/config/rutas.py`:

```python
RUTA_SRC = os.path.dirname(os.path.dirname(__file__))
RUTA_RAIZ = os.path.dirname(RUTA_SRC)
DB_FILE = os.path.join(RUTA_RAIZ, "estadisticas.db")
LOG_DIR = os.path.join(RUTA_RAIZ, "logs")
```

Instalado como wheel, `RUTA_RAIZ` pasa a ser `site-packages/..` → la base terminaría en la
carpeta interna del entorno: **se pierde al desinstalar/actualizar** y puede no tener permisos de
escritura.

**Solución:** carpeta de datos del usuario, con `platformdirs`:

| Sistema                | Ubicación típica de `user_data_dir("StatsPro")`   |
| ---------------------- | ------------------------------------------------- |
| Windows                | `C:\Users\<user>\AppData\Local\StatsPro\StatsPro` |
| Linux                  | `~/.local/share/StatsPro`                         |
| macOS                  | `~/Library/Application Support/StatsPro`          |
| Android (Flet, Hito 4) | carpeta privada de la app                         |

Sugerencia de diseño:

- Variable de entorno `STATSPRO_HOME` que, si existe, pisa la ubicación. Sirve para tests, para
  desarrollo (apuntar al repo) y para correr instancias separadas en Windows y WSL.
- Modo desarrollo: si se corre desde el repo (`uv run python src/...`), se puede mantener la DB en
  la raíz para no cambiar el flujo de trabajo actual. A decidir en el spike.

### 3.3 Los archivos `.sql` no viajan en el wheel

Los `.sql` (`schema.sql`, `views.sql`, `seed.sql`, `limpieza.sql`) no son `.py`, así que setuptools
no los incluye por defecto. Además se leen con `os.path.join(RUTA_SRC, ...)`.

**Solución:**

```toml
[tool.setuptools.package-data]
"statspro.infraestructura.persistencia" = ["sql/*.sql"]
```

y leerlos con `importlib.resources` (funciona aunque el paquete esté dentro de un zip):

```python
from importlib.resources import files

schema = files("statspro.infraestructura.persistencia").joinpath("sql/schema.sql").read_text("utf-8")
```

### 3.4 Detalles menores

- El parser se llama `stats` (`prog` de argparse), pero el comando instalado es `statspro`:
  unificar el nombre.
- Falta `statspro --version` (leerlo con `importlib.metadata.version("statspro-basketball")`).
- Al cambiar a paquete raíz, actualizar `[project.scripts]` a `statspro = "statspro.main:main"`,
  `pythonpath`/`mypy_path` y el `omit` de coverage si hace falta.

## 4. Formas de distribución a comparar

| Opción                                              | Cómo se instala                                                                                                | A favor                                                                    | En contra                                                                              |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **`uv tool install` desde el wheel o desde git** ⭐ | `uv tool install statspro_basketball-0.1.0-py3-none-any.whl` o `uv tool install git+https://github.com/<repo>` | Entorno aislado, actualización simple (`uv tool upgrade`), multiplataforma | Requiere tener `uv` (y que uv baje Python si no hay)                                   |
| `pipx install`                                      | Igual que la anterior, con pipx                                                                                | Conocido                                                                   | Otra herramienta más; el proyecto ya usa uv                                            |
| `pip install` en un venv                            | Manual                                                                                                         | Universal                                                                  | El usuario maneja el venv; poco amigable para un DT                                    |
| **Ejecutable único** (PyInstaller / Nuitka)         | Descargar `statspro.exe`                                                                                       | No requiere Python                                                         | Binario pesado (pandas: ~50–100 MB), uno por SO, antivirus que marcan falsos positivos |
| Publicar en PyPI                                    | `uv tool install statspro-basketball`                                                                          | Lo más cómodo                                                              | Público; prematuro para v0.1                                                           |

Para probadores (vos, colegas DTs con algo de manejo técnico), `uv tool install` desde git o
desde un wheel adjunto a un GitHub Release alcanza. El ejecutable único es más relevante para
la GUI del Hito 4 (Flet trae su propio `flet build`).

## 5. Paso a paso

> ⚠️ Igual que en el resto del proyecto: **no usar la `estadisticas.db` real ni el `.venv` real**.
> Trabajar sobre una copia del repo (o en la rama del spike con `STATSPRO_HOME` apuntando a una
> carpeta temporal) y verificar con `md5sum estadisticas.db` antes y después.

### Paso 1 — Rama

```bash
git checkout main && git pull
git checkout -b spike/build-cli
```

### Paso 2 — Build del estado actual (línea base)

```bash
uv build                                  # genera dist/*.whl y dist/*.tar.gz
unzip -l dist/statspro_basketball-*.whl   # ver qué entró
```

Anotar: ¿qué paquetes de primer nivel aparecen? ¿Están los `.sql`? (Esperado: sin `.sql` y con
`config/`, `utils.py`, etc. sueltos.)

### Paso 3 — Instalar en entorno limpio y ver qué falla

Desde **otra carpeta** (fuera del repo), para que nada se resuelva contra el código fuente:

```bash
uv tool install /ruta/al/repo/dist/statspro_basketball-0.1.0-py3-none-any.whl
cd ~ && statspro club list
```

Anotar los errores (esperado: no encuentra `schema.sql`, o crea la DB en una carpeta rara).
Desinstalar con `uv tool uninstall statspro-basketball`.

Alternativa más aislada: hacerlo dentro de un contenedor (`docker run -it python:3.12-slim`) para
garantizar que no hay nada del repo a la vista.

### Paso 4 — Paquete raíz `statspro`

1. `git mv` de las carpetas de `src/` a `src/statspro/`.
2. Reemplazar imports en `src/` y `tests/` (script de búsqueda/reemplazo; revisar el diff).
3. Agregar `src/statspro/__init__.py` y `__main__.py`.
4. Actualizar `pyproject.toml`: `[project.scripts]`, `pythonpath`, `mypy_path`.
5. Correr tests, ruff y mypy.

Medir: cantidad de archivos tocados y tiempo invertido (dato para estimar la tarea real).

### Paso 5 — Rutas de usuario

1. `uv add platformdirs`.
2. Reescribir `config/rutas.py`: DB y logs en `STATSPRO_HOME` o en `user_data_dir("StatsPro")`.
3. SQL con `importlib.resources` + `package-data`.
4. Ajustar los tests que dependan de rutas (idealmente vía `STATSPRO_HOME` en una fixture con
   `tmp_path`).

### Paso 6 — Build e instalación de nuevo

Repetir los pasos 2 y 3. Criterio: `statspro club add ...` y `statspro club list` funcionan desde
cualquier carpeta, la DB aparece en la carpeta de datos del usuario y `uv tool uninstall` **no**
borra la base.

### Paso 7 — Migración de la base existente

Definir qué pasa con quien ya tiene `estadisticas.db` en la raíz del repo:

- Opción A: comando explícito `statspro db importar <ruta>` (copia con el backup online de SQLite,
  reutilizable para la US-402 / ADR-008).
- Opción B: al arrancar, si no hay DB en la carpeta de usuario y existe una en la ubicación vieja,
  copiarla y avisar.

Recomendación previa: A — es explícito y aprovecha el trabajo de backup que igual hay que hacer.

### Paso 8 (opcional) — Ejecutable único

Probar `uv run --with pyinstaller pyinstaller --onefile -n statspro src/statspro/__main__.py`
(agregando los `.sql` con `--add-data`) y medir tamaño y tiempo de arranque. Solo para decidir si
vale la pena; no es objetivo del spike.

### Paso 9 (opcional) — Build en CI

Un job de GitHub Actions que corra `uv build`, instale el wheel en un entorno limpio y ejecute
`statspro --help` (prueba de humo del paquete). Podría adjuntar el wheel a cada GitHub Release.

## 6. Criterios de éxito

| #   | Criterio                                  | Resultado esperado                                                     |
| --- | ----------------------------------------- | ---------------------------------------------------------------------- |
| C1  | `uv build`                                | Genera wheel con un solo paquete raíz `statspro` y los `.sql` adentro  |
| C2  | Instalar el wheel fuera del repo          | `statspro --help` y `statspro --version` funcionan                     |
| C3  | Primera ejecución                         | La DB se crea en la carpeta de datos del usuario, con esquema completo |
| C4  | `STATSPRO_HOME=/tmp/x statspro club list` | Usa esa carpeta                                                        |
| C5  | Desinstalar y reinstalar                  | La base y sus datos siguen ahí                                         |
| C6  | Suite de tests, ruff y mypy               | Todo verde después del refactor, cobertura ≥ 85 % en Linux             |
| C7  | Windows y Linux/WSL                       | Funciona en ambos, cada uno con su propia DB                           |

## 7. Riesgos

- **Refactor de imports grande:** genera un diff enorme y conflictos con ramas abiertas (por
  ejemplo `feature/us104`). Hacerlo en un momento sin ramas en vuelo y en un PR exclusivo.
- **Cambio de ubicación de la DB:** quien hoy usa `estadisticas.db` en el repo puede "perder" sus
  datos si no hay migración clara (Paso 7).
- **Windows + WSL:** con la carpeta compartida, hoy ambos sistemas tocan la misma DB; con
  `platformdirs` cada sistema tendría la suya (es una mejora, pero hay que comunicarlo).
- **Tests que dependen de rutas fijas:** pueden romperse al mover `rutas.py`.

## 8. Entregables al cerrar el spike

- [ ] Rama `spike/build-cli` con los cambios (puede mergearse si queda limpia, o rehacerse como
      tarea real).
- [ ] Tabla de la sección 6 completada.
- [ ] Decisión sobre distribución (sección 4) y sobre migración de la DB (Paso 7).
- [ ] Actualizar US-404 y la sección 20 del plan (`docs/plan_desarrollo_detallado.md`), RUNBOOK
      (instalación) y, si corresponde, un ADR de distribución.

## 9. Resultados

_(Completar al terminar el spike.)_

| Criterio | Resultado | Observaciones |
| -------- | --------- | ------------- |
| C1       |           |               |
| C2       |           |               |
| C3       |           |               |
| C4       |           |               |
| C5       |           |               |
| C6       |           |               |
| C7       |           |               |

**Archivos tocados por el refactor de imports:** _…_

**Tamaño del wheel / del ejecutable (si se probó):** _…_

**Conclusión / recomendación:** _…_
