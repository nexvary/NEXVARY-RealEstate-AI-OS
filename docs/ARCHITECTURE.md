# Architecture

## System boundary

NEXVARY RealEstate AI OS deliberately separates **transactional truth** from **probabilistic AI**.

### Transactional source of truth

PostgreSQL owns:
- tenants and white-label configuration
- users, roles and authorization scopes
- projects, buildings and units
- price, availability and inventory state
- leads and sales pipeline
- appointments
- reservations, contracts, installments and commissions
- audit events

An AI model is never authoritative for these values.

### Knowledge/RAG plane

Documents such as brochures, FAQs, contracts, policies and project specifications are chunked and embedded into a pgvector-backed knowledge store. Retrieval results must retain document identity, page/section metadata and tenant scope.

### Automation plane

n8n is an orchestration layer, not the database. It handles messaging webhooks, scheduled follow-ups, notification delivery, document-ingestion triggers and integration adapters. Business invariants remain inside the API/domain layer.

## Multi-tenancy

Every business record carries a tenant identifier. Application queries must always be tenant-scoped. Database-level Row Level Security is planned as an additional production guardrail.

## AI safety rules

1. Price/availability/reservation answers must be tool-grounded from transactional data.
2. RAG answers retain source metadata.
3. Low-confidence or high-risk actions escalate to a human.
4. AI cannot execute financial, contractual or inventory-changing actions without a policy gate.
5. Prompts, tool calls and material AI actions are auditable.

## Initial services

- `apps/web`: React/Vite Arabic-first control center.
- `services/api`: FastAPI transactional API.
- PostgreSQL + pgvector: data and vector retrieval.
- Redis: queues/cache/rate-limit support.
- n8n: external workflow orchestration.
