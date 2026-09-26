# Stage 170 Release

NEXVARY RealEstate AI OS Stage 170 is the first Windows desktop release candidate.

## What Stage 170 contains

The work from the platform foundation through Stage 170 is grouped into these release tracks:

- **Stages 1–20 — Platform foundation:** FastAPI service, React control center, multi-tenant data model, transactional source-of-truth rules, Docker development stack and CI.
- **Stages 21–45 — CRM and sales:** leads, deterministic scoring, pipeline, assignments, appointments, search and dashboard metrics.
- **Stages 46–70 — Inventory:** projects, buildings, units, payment plans, availability controls and tenant-scoped inventory search.
- **Stages 71–90 — Reservations and transactions:** unit locking, cancellation/release behavior, reservation-to-contract conversion and sold-state enforcement.
- **Stages 91–110 — Finance:** contracts, installment schedules, payment recording, broker commissions and finance views.
- **Stages 111–125 — Knowledge and AI:** document chunking, tenant-scoped grounded retrieval and a sales copilot that reads price/availability only from transactional inventory.
- **Stages 126–140 — Communications and operations:** unified inbox data model, messages, channels, follow-up tasks and operational workspaces.
- **Stages 141–150 — Security and governance:** PBKDF2 password hashing, JWT sessions, database-backed RBAC, audit events, tenant isolation and first-owner bootstrap.
- **Stages 151–158 — White label:** company brand name/color configuration, About links and tenant-scoped settings.
- **Stages 159–164 — Data portability:** safe JSON operational export with password hashes excluded.
- **Stages 165–168 — Desktop runtime:** local SQLite runtime, generated runtime secrets, bundled FastAPI + web UI, pywebview shell and program icon.
- **Stage 169 — UI Release Gate:** desktop/mobile Playwright checks for first-run setup, navigation, lead creation, inventory workflow, language switching and responsive overflow.
- **Stage 170 — Windows installer gate:** API tests, frontend production build, UI Release Gate, PyInstaller freeze, Inno Setup compilation and SHA-256 artifact.

## Important architecture guarantees

1. AI is not authoritative for price, availability, reservation state, contracts or payments.
2. Every business query is tenant scoped after authenticated identity resolution.
3. Reservation conversion changes the unit state transactionally.
4. Knowledge retrieval is evidence-oriented and separated from transactional inventory.
5. Password hashes are not included in the operational JSON export.
6. Desktop first-run setup creates the first tenant and owner without requiring command-line setup.

## External integrations

The inbox models WhatsApp, Instagram, Messenger, Telegram, website, phone and manual channels. Live provider delivery requires the relevant provider credentials/API configuration and is intentionally not embedded into the Windows installer.

The Windows installer is intended to run the core application without requiring Python, Node.js, npm, Docker or terminal commands from the end user.
