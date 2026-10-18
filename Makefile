.PHONY: install migrate seed dev test clean

install:
	pip install -e ".[dev]"

migrate:
	python -m nbo.db migrate

seed:
	python -m nbo.db seed

test:
	pytest -q

clean:
	rm -rf .venv nbo.db src/*.egg-info
