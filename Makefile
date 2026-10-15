.PHONY: install migrate seed dev test lint clean

install:
	pip install -e ".[dev]"
	cd web && npm ci

migrate:
	python -m nbo.db.migrate

seed:
	python -m nbo.db.seed

dev:
	docker compose up -d db redis
	python -m uvicorn api.main:app --reload --port 8000 &
	cd web && npm run dev

test:
	pytest
	cd web && npm run test

lint:
	ruff check src/
	cd web && npm run lint

clean:
	docker compose down -v
	rm -rf .venv node_modules web/node_modules
