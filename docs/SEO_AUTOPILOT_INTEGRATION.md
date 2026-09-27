# White-Label SEO Autopilot Integration

## Source preservation

The original SEO product remains unchanged:

- Repository: `nexvary/NEXVARY-SEO-Autopilot.`
- Source commit copied: `3838cd8030be069db6a3503150bcaccf3210abe3`

No write operation is performed against that repository as part of the integration.

## Integration model

The copied SEO engine lives under:

`services/api/seo_autopilot_core/`

The RealEstate White-Label product wraps that core with tenant-aware models, authenticated APIs, encrypted per-tenant provider configuration and a new tenant-branded React workspace.

The old SEO HTML interface is intentionally not copied into the product shell. This avoids fixed NEXVARY branding and gives every tenant the company name, logo, color and navigation already selected in the White-Label platform.

## Integrated capabilities

- Single-page technical SEO audit.
- Safe same-site crawler with the upstream SSRF protections.
- Google Search Console read-only analytics using per-tenant encrypted credentials.
- Search opportunity engine.
- Content brief engine.
- Structured Data builder from visible facts.
- Core Web Vitals scoring.
- Answer-readiness and AI-evidence readiness engines.
- Index coverage summary from crawl evidence.
- Read-only competitor page radar.
- Guarded Autopilot change planning.

## Safety boundary

The integrated v1.2.0 user interface does **not** expose a live Apply button.

Autopilot plans are forced to `dry_run=true`. The upstream risk classifier is preserved:

- `safe_auto`
- `review_required`
- `protected`

A future live-write layer must keep the original backup, stale-state protection, approval and rollback guarantees and must use tenant-specific encrypted CMS Bridge credentials.

## Tenant isolation

The integration adds tenant-scoped tables for:

- SEO websites/projects.
- Audit/crawl/Search Console snapshots.
- Guarded change-plan drafts.

All project and snapshot lookups include the authenticated tenant ID.

## Search Console configuration

In NEXVARY Platform Admin configure a provider named:

`google-search-console`

Recommended public configuration:

```json
{
  "site_url": "https://company.example"
}
```

Secret configuration:

```json
{
  "access_token": "<runtime OAuth access token>"
}
```

The access token is encrypted by the platform integration store and is never returned in read responses.

## White-label behavior

SEO Autopilot appears inside the tenant workspace and inherits:

- Company display name.
- Company logo.
- Primary brand color.
- Tenant session and RBAC.
- Company navigation shell.

The user-facing SEO workspace therefore does not require the tenant to display NEXVARY unless the tenant's Powered by NEXVARY policy is enabled.

## Release gates

The integration includes API tests for:

- Source provenance.
- Tenant isolation.
- Audit persistence.
- Crawl persistence.
- Schema and Web Vitals.
- Dry-run risk policy.
- Search Console encrypted credential use.
- Cross-site target rejection.

The Playwright UI gate covers:

- Opening SEO Autopilot from tenant navigation.
- Creating a website.
- Building JSON-LD.
- Creating a guarded dry-run change plan.
- Verifying that no live website write is performed.
