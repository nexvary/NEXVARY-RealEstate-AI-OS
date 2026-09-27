# Qt 6 / C++20 / QML Migration Plan

## Objective

Move the Windows desktop experience of NEXVARY RealEstate AI OS toward the same native architecture proven in NEXVARY Avionics Lab, without sacrificing the tested v1.8 product.

## Architecture

```text
QML / Qt Quick UI
        │
        ▼
C++20 Application State + Native Services
        │
        ├── Qt Network ─────────► FastAPI transactional/AI services
        ├── Qt SQL (next phase) ► native cache / offline state
        └── Qt process bridge ──► packaged Python service during transition
```

The Python/FastAPI service remains the transactional source of truth while domain modules are migrated deliberately.

## Gates inherited from the Avionics approach

1. C++ warnings enabled.
2. CTest on every native build.
3. Qt/QML runtime screenshot gate.
4. Explicit Arabic RTL geometry verification.
5. Back-stack verification.
6. Windows and Linux compilation.
7. Existing API and Web tests continue running.
8. No legacy module is removed until its native replacement reaches feature parity.
9. Release packaging remains a separate final gate.

## Migration sequence

- Phase N1: Native shell, RTL, login, live dashboard, API bridge.
- Phase N2: Leads and inventory create/edit flows.
- Phase N3: Appointments, finance, tasks, team and company settings.
- Phase N4: Knowledge, Omnichannel/WhatsApp and grounded AI.
- Phase N5: Growth Intelligence, SEO Autopilot and Automation Studio.
- Phase N6: Native company branding/cover management and installer integration.
- Phase N7: Sidecar lifecycle, local Qt SQL cache, offline-safe startup and recovery.
- Phase N8: Full parity test matrix and switch the primary Windows launcher to Qt.

## Non-goal

This is not a rewrite that discards the current backend. It is a controlled UI/application-core migration with testable boundaries.


## Current parity status

Implemented and wired in the Qt native client:

- Authentication, bilingual Arabic/English shell, true RTL, native back stack and digital clock.
- Dashboard, Leads, Inventory, Appointments, Reservations and Finance.
- Enterprise CRM: proposals, invoices/payments, expenses, tickets, reminders and Universal Customer Timeline.
- Knowledge Base, Tasks, Team/RBAC.
- Omnichannel/WhatsApp workspace, sales state, grounded reply preparation, human handoff and outbox actions.
- Growth Intelligence.
- SEO Autopilot.
- Automation Studio.
- AI Sales Copilot with live inventory, knowledge evidence and verified media.
- White-Label Settings, tenant logo/cover import and Company Page.
- Native About/System page.
- Windows local FastAPI sidecar bootstrap and native packaging pipeline.

The React v1.8 shell remains intact until the native installer passes the complete release matrix and the sidecar lifecycle is validated on an installed Windows machine.

## Native Windows packaging

The native client automatically looks for `NEXVARY-RealEstate-API.exe` next to the Qt executable. When present, it selects a free localhost port, starts the sidecar, points Qt Network to that local service, and terminates the sidecar when the desktop application exits.

The CI packaging path uses:

1. CMake/Qt build and CTest.
2. PyInstaller API sidecar.
3. `windeployqt` for the Qt/QML runtime.
4. Inno Setup for a separate Native Preview installer.
5. SHA256 generation and artifact upload.

The original v1.8 installer is not overwritten by this preview pipeline.
