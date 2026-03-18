.PHONY: up down restart migrate migrate-new test test-unit test-integration test-cov check dev ui worker lint type-check format clean

# ── Docker services ───────────────────────────────────────────────────────────

up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart fastapi celery

logs:
	docker compose logs -f fastapi

# ── Database migrations ───────────────────────────────────────────────────────

migrate:
	docker compose exec fastapi alembic upgrade head

migrate-new:
	@[ -n "$(name)" ] || (echo "Usage: make migrate-new name=<migration_name>"; exit 1)
	docker compose exec fastapi alembic revision --autogenerate -m "$(name)"

migrate-down:
	docker compose exec fastapi alembic downgrade -1

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	pytest tests/unit/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e --timeout=120

test-cov:
	pytest tests/unit/ tests/integration/ \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=80 \
		-v

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
	ruff check src/ tests/

lint-fix:
	ruff check src/ tests/ --fix

format:
	ruff format src/ tests/

type-check:
	mypy src/

check: lint type-check test-cov

# ── Development servers ───────────────────────────────────────────────────────

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

ui:
	streamlit run src/ui/app.py --server.port 8501

worker:
	celery -A src.tasks.celery_app worker \
		--loglevel=info \
		-Q ingestion,enrichment,outreach,ml \
		--concurrency=4

# ── Utilities ────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete; \
	rm -rf .coverage coverage.xml .mypy_cache .pytest_cache .ruff_cache

shell:
	docker compose exec fastapi bash
