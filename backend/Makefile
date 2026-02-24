VENV_PYTHON=venv/bin/python
VENV_PIP=venv/bin/pip
UVICORN=venv/bin/uvicorn
ALEMBIC=venv/bin/alembic

.PHONY: dev test migrate upgrade

dev:
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8000

test:
	$(VENV_PYTHON) -m pytest

migrate:
	$(ALEMBIC) revision --autogenerate -m "auto"

upgrade:
	$(ALEMBIC) upgrade head

