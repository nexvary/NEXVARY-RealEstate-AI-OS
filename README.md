# NEXVARY RealEstate AI OS

AI-first, multi-tenant, white-label operating system for real-estate companies.

## Current release line

**v1.2.0 — Platform Admin + White-Label SEO Autopilot**

The product now has two isolated workspaces:

1. **Company workspace** — CRM, inventory, viewings, reservations, contracts, installments, commissions, tasks, inbox, knowledge base and grounded AI.
2. **NEXVARY Platform Admin** — create and manage multiple real-estate companies from one control plane.

The Windows desktop build is designed for normal installation and first-run configuration without Python, Node.js, Docker or terminal commands.

## Product rule: AI never owns the truth

The platform separates exact transactional data from probabilistic AI:

- **Transactional database** is authoritative for price, unit availability, reservations, contracts, installments, commissions and customer records.
- **Knowledge retrieval** is used for brochures, policies, contracts, FAQs and other documents.
- **Grounded AI Sales Copilot** combines tenant-scoped inventory tools with tenant-scoped knowledge evidence.
- **Human and RBAC gates** protect financial, contractual, administrative and inventory-changing actions.

## Platform Admin capabilities

- Create a new company and its first owner from the GUI.
- Starter / Professional / Enterprise plans.
- Active / Trial / Suspended tenant lifecycle.
- Enforced limits for users, projects, units and monthly AI requests.
- Live platform totals and per-company usage.
- Custom domains with public branding resolution.
- White-label brand name, primary color, logo and social/contact links.
- Optional **Powered by NEXVARY** policy per tenant.
- Encrypted per-tenant integration credentials for providers such as WhatsApp, OpenAI and Telegram.
- Platform-admin authentication separated from company-user authentication.
- Upgrade path: an existing first-company owner can claim the Platform Admin console once.

## Company workspace

- CRM leads and deterministic lead scoring.
- Projects, buildings, units and payment plans.
- Sales pipeline and viewings.
- Reservation locking and cancellation/release rules.
- Contracts, installment schedules and broker commissions.
- Follow-up tasks.
- Unified conversation/inbox data model.
- Tenant knowledge base and evidence-oriented retrieval.
- Grounded AI Sales Copilot.
- Users and database-backed RBAC.
- Company audit log.
- Safe operational JSON export.
- Arabic RTL + English.
- Responsive desktop/mobile web UI.
- Company logo, social links and custom white-label identity.
- Integrated White-Label SEO Autopilot workspace copied from the preserved original SEO project.
- Technical audits, bounded crawling, Search Console read-only analytics, opportunities, schema, performance and guarded dry-run SEO planning.

## Security boundaries

- Tenant identity and roles come from signed authenticated sessions, not trusted request headers.
- Suspended tenants are blocked centrally.
- Platform Admin uses a distinct token type.
- Passwords use salted PBKDF2-SHA256 hashes.
- Provider credentials are encrypted at rest and secret values are never returned by read APIs.
- Operational backup exports exclude password hashes and integration secret ciphertext.
- Desktop runtime secrets are generated automatically per installation.

## Verification

GitHub Actions runs:

- Python API test suite.
- TypeScript/Vite production build.
- Browser UI Release Gate with Playwright on desktop and mobile.
- Windows PyInstaller freeze.
- Inno Setup compilation.
- SHA-256 generation for the installer artifact.

## Developer quick start

### API

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

### Web control center

```bash
cd apps/web
npm install
npm run dev
```

### Infrastructure

```bash
docker compose up -d postgres redis n8n
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Stage 170 release](docs/STAGE_170_RELEASE.md)
- [Platform Admin & White Label](docs/PLATFORM_ADMIN.md)
- [White-Label SEO Autopilot integration](docs/SEO_AUTOPILOT_INTEGRATION.md)
