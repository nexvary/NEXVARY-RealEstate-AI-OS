# NEXVARY RealEstate AI OS

AI-first, white-label operating system for real-estate companies.

> **Status:** foundation build in progress. Multi-tenant transactional core, CRM primitives, unit search, Arabic/English dashboard and CI are being developed first.

## Product rule: AI never owns the truth

The platform deliberately separates data that must be exact from AI-generated reasoning:

- **PostgreSQL is authoritative** for price, unit availability, reservations, installments, commissions and customer records.
- **RAG is used** for brochures, policies, contracts, FAQs and other documents.
- **n8n orchestrates** messaging and repetitive workflows; it is not the business database.
- **Human approval gates** protect contractual, financial and inventory-changing actions.

## Current foundation

- FastAPI service with health endpoint, CRM lead creation, deterministic lead scoring, inventory search and overview metrics.
- Initial multi-tenant models for tenants, projects, units, leads, appointments and audit events.
- React/Vite management UI with Arabic RTL + English, responsive layout, working navigation, language switcher and add-lead flow.
- PostgreSQL/pgvector-ready development stack, Redis and n8n via Docker Compose.
- GitHub Actions build/test gate for Python and web UI.
- Architecture and product roadmap documentation.

## Quick start

### 1. API

```bash
cd services/api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Open API docs at `http://localhost:8000/docs`.

### 2. Web control center

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173`.

### 3. Infrastructure

Copy `.env.example` to `.env`, change development secrets, then:

```bash
docker compose up -d postgres redis n8n
```

n8n will be available at `http://localhost:5678`.

### 4. Verification

```bash
make test
```

Or run each gate separately:

```bash
cd services/api && pytest -q
cd apps/web && npm install && npm run build
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)

## Planned platform areas

CRM · Inventory · Sales Pipeline · Viewings · Reservations · Contracts · Installments · Broker Commissions · Omnichannel Inbox · RAG Knowledge Base · AI Sales Agent · AI Customer Service · Marketing Studio · White Label · Audit & Analytics
