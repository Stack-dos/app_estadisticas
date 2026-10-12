instalar_dependencias:
	@echo "Instalando dependencias con uv (lee pyproject.toml y uv.lock)..."
	uv sync

run_test:
	@echo "Ejecutando test..."
	uv run pytest -v --cov=src --cov-report=html

run_linter_ruf:
	uv run ruff check .
	uv run ruff format --check .

corregir_linter:
	uv run ruff check --fix . && uv run ruff format .
	uv run ruff check .

pre_commit:
	uvx pre-commit run --all-files

# Version de Python de la imagen Docker. Uso: make docker_test PYTHON_VERSION=3.13
PYTHON_VERSION ?= 3.11

docker_test:
	docker build -f Dockerfile.test --build-arg PYTHON_VERSION=$(PYTHON_VERSION) -t app-estadisticas-tests .
	docker run --rm app-estadisticas-tests

static_check:
	uv run mypy src/ --strict --explicit-package-bases
