# Commercial Platform v1.3.0

## Scope

v1.3.0 moves the White-Label RealEstate AI OS from a technically multi-tenant product toward an operable commercial SaaS control plane.

The original `main` branch and the original `NEXVARY-SEO-Autopilot.` repository remain outside this release line.

## 1. Subscription management

Platform Admin can maintain one commercial subscription per tenant with:

- plan
- status: trial / active / past_due / cancelled
- monthly / yearly / custom billing cycle
- recurring amount and currency
- current billing period
- cancel-at-period-end flag
- provider and optional external subscription ID

Changing the plan can also reapply the default SaaS limits for that plan.

This is provider-neutral. v1.3.0 does not pretend that a payment processor charged a card unless a future provider integration records that event.

## 2. Invoice ledger

Platform Admin can create, list, mark paid and void invoices for a tenant.

Stored invoice facts include:

- unique invoice number
- subtotal
- tax
- total
- currency
- due date
- paid timestamp
- description
- subscription relationship

Paid invoices cannot be voided.

## 3. Reusable tenant templates

Platform Admin can create reusable templates containing:

- SaaS plan
- brand color
- Powered by NEXVARY policy
- plan limits
- feature flags
- default integration provider placeholders
- default subscription price, currency and cycle

## 4. One-click provisioning

A template can provision a complete new company in one action:

- tenant
- first owner
- SaaS profile
- plan limits
- feature flags
- commercial subscription
- custom domain
- contact/website configuration
- encrypted-integration placeholders

No terminal setup is required.

## 5. Per-tenant WhatsApp channels

Each tenant now has a dedicated WhatsApp Channels workspace.

Stored per channel:

- display name
- Meta Phone Number ID
- WABA ID
- business phone
- Graph API version
- default-channel flag
- readiness state

Access token and App Secret are stored only in the encrypted tenant integration store. Read responses expose secret key names, not secret values.

The readiness endpoint verifies local configuration presence only. It deliberately does not claim that Meta accepted credentials unless a later live provider validation succeeds.

## 6. Transactional Real Estate SEO pages

SEO Autopilot can generate deterministic page specifications directly from the real-estate database.

### Project pages

Generated only from:

- project name
- city
- developer
- stored project description

### Unit pages

Generated only from:

- project identity and city
- unit code/type
- bedrooms
- area
- price and currency
- current transactional availability status

The output includes:

- deterministic slug
- canonical target URL
- title
- meta description
- structured body facts
- JSON-LD
- source hash
- ready/published state

The page generator reports `hallucinated_fields: 0` in bulk synchronization because no unstored amenities, discounts, delivery dates or availability claims are invented.

## 7. Source-hash refresh

Each generated page stores a SHA-256 source hash. When the underlying real-estate facts change, regeneration updates the page specification and its structured data.

This gives SEO a direct relationship with the transactional inventory rather than treating marketing copy as the source of truth.

## 8. Release gates

v1.3.0 adds API tests for:

- subscription creation/update
- invoice totals and paid lifecycle
- tenant template creation
- complete one-click provisioning
- encrypted WhatsApp credentials
- tenant isolation
- WhatsApp readiness
- deterministic project/unit SEO generation
- inventory-status propagation into generated SEO pages

The Playwright Windows release gate additionally checks:

- creating a reusable company template
- provisioning a company through the GUI
- creating a tenant WhatsApp channel
- confirming no access token appears in the rendered UI
- WhatsApp readiness
- opening the Real Estate Pages tab in SEO Autopilot
- synchronizing a real-estate project from live database facts
