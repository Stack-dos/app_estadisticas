"""Version de la app, embebida en el codigo (spike de aviso de version nueva, punto 4.2 (a); AC4 de la US-404).

La app empaquetada con `flet build` no trae la metadata del paquete (`importlib.metadata` no la encuentra),
asi que la version vive aca. El job `version` de `release.yml` frena el release si no coincide con el tag.
Al sacar una version se sube aca y en `[project].version` de `pyproject.toml` (RUNBOOK, "Sacar una version").
"""

VERSION = "1.0.0"
