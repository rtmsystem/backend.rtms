.PHONY: help install migrate run test lint format clean docker-build docker-up docker-down

help:
	@echo "Comandos disponibles:"
	@echo "  make install       - Instalar dependencias"
	@echo "  make migrate       - Ejecutar migraciones"
	@echo "  make run           - Ejecutar servidor de desarrollo"
	@echo "  make test          - Ejecutar tests"
	@echo "  make lint          - Ejecutar linters"
	@echo "  make format        - Formatear código"
	@echo "  make clean         - Limpiar archivos temporales"
	@echo "  make docker-build  - Construir imagen Docker"
	@echo "  make docker-up     - Levantar contenedores"
	@echo "  make docker-down   - Detener contenedores"

install:
	python3.11 -m pip install --upgrade pip
	pip install -r requirements.txt
	pre-commit install

migrate:
	python manage.py makemigrations
	python manage.py migrate

createsuperuser:
	python manage.py createsuperuser

run:
	python manage.py runserver 0.0.0.0:8000

test:
	pytest

lint:
	flake8 apps/ config/
	mypy apps/ config/

format:
	isort apps/ config/ tests/
	black apps/ config/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

shell:
	python manage.py shell

dbshell:
	python manage.py dbshell



