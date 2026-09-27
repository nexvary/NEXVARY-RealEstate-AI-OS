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
