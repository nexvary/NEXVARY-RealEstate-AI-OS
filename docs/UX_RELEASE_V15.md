# UX & Development Release v1.5.0

## Purpose

v1.5.0 improves the White-Label desktop development cycle and makes the application easier to evaluate repeatedly while the product is still under active development.

The original `main` branch remains unchanged. This release belongs only to the White-Label product line.

## Development reinstall safety

Desktop runtime data remains outside Program Files under LocalAppData, so uninstalling and reinstalling the application does not delete runtime secrets or the local database by default.

A development workspace created with **Skip setup — Development mode** also writes a development profile marker.

When a later build declares an incompatible development schema generation:

1. the old development database is archived automatically,
2. the archive is kept under `development-backups`,
3. a clean database is created on startup,
4. runtime secrets remain available,
5. the tester can recreate the development workspace with one click.

This behavior is limited to the explicit development workspace. Normal customer/company data is not silently reset.

## One-click development setup

The first-run screen now contains:

**Skip setup — Development mode**

It creates a local development tenant and owner automatically without requiring the tester to enter company information.

After that, the normal sign-in screen exposes:

**Quick entry to development workspace**

This obtains a fresh local desktop session without requiring remembered test credentials.

The development shortcut is not available as a production-cloud authentication mechanism.

## Internal Back navigation

The header Back button now maintains an internal view history.

Example:

Dashboard → Leads → Inventory Management → Back → Leads → Back → Dashboard.

It no longer exits the program and does not blindly force every page back to Dashboard.

## About the System

A dedicated **About the System** page documents the major product capabilities:

- CRM and sales
- real-estate inventory
- reservations and contracts
- bank-transfer billing
- WhatsApp/channel configuration
- SEO Autopilot
- grounded AI
- White-Label/SaaS
- security and audit

It also contains the official NEXVARY developer links.

## About the Company

A separate **About the Company** page displays the current tenant identity:

- company/brand name
- logo
- plan
- lifecycle status
- tenant identifier
- website
- Facebook
- LinkedIn
- YouTube
- X
- TikTok
- contact email

These company links come from tenant settings, preserving White-Label isolation.

## Interface polish

- clearer icon treatment in the sidebar
- distinct icons for finance, billing, inbox and WhatsApp
- improved hover/active visual states
- polished development buttons
- separate About pages
- horizontally scrollable single-row mobile navigation to avoid icon overlap
- About pages remain reachable on mobile
