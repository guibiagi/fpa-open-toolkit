.PHONY: install data test lint app clean

install:
	pip install -e ".[dev]"

data:
	python -m src.data_generation.synthetic_generator

test:
	pytest -v --cov=src --cov-report=term-missing

lint:
	ruff check src tests app
	ruff format src tests app

app:
	uvicorn app.main:app --reload --port 8000

clean:
	rm -rf data/outputs/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
