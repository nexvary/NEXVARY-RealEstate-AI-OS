.PHONY: api web test infra

infra:
	docker compose up -d postgres redis n8n

api:
	cd services/api && python -m uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && npm install && npm run dev

test:
	cd services/api && pytest -q
	cd apps/web && npm run build
