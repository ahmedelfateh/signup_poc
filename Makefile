.PHONY: run migrate makemigrations shell test coverage lint format help

help:
	@echo "Available commands:"
	@echo "  run              - Run Django development server"
	@echo "  migrate          - Apply database migrations"
	@echo "  makemigrations   - Create new migrations based on model changes"
	@echo "  shell            - Open Django shell"
	@echo "  test             - Run tests"
	@echo "  coverage         - Run tests with coverage report"
	@echo "  lint             - Run code linting (ruff)"
	@echo "  format           - Format code (ruff format)"
	@echo "  clean            - Clean up Python cache files"

run:
	python manage.py runserver_plus

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell_plus --ipython

test:
	pytest

coverage:
	pytest --cov=. --cov-report=html

lint:
	ruff check .

format:
	ruff format .

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	find . -name "*.coverage" -delete
	find . -name "htmlcov" -type d -exec rm -rf {} +
