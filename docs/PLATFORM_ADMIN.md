# NEXVARY Platform Admin & White-Label SaaS

## Purpose

The Platform Admin control plane turns NEXVARY RealEstate AI OS from a single-company application into a multi-company product that can be operated by NEXVARY and white-labeled for individual real-estate businesses.

## Authentication separation

Company users and platform administrators use separate token types.

- Company session: tenant-scoped JWT resolved against an active user and tenant.
- Platform session: platform-admin JWT resolved against an active PlatformAdmin record.

A company user cannot become a platform administrator by changing a request header.

For an existing installation upgraded from the earlier desktop release, the first company owner can claim the Platform Admin console once using their company identifier, email and password.

## Tenant lifecycle

Each company has one SaaS profile with:

- plan: starter / professional / enterprise
- lifecycle: active / trial / suspended
- custom domain
- Powered by NEXVARY flag
- user/project/unit limits
- monthly AI request allowance
- logo and social/contact identity

Suspension is enforced centrally by the authenticated request context, so business routes stop operating for a suspended tenant.

## Quotas

Default plan allowances:

| Plan | Users | Projects | Units | Monthly AI requests |
| --- | ---: | ---: | ---: | ---: |
| Starter | 8 | 15 | 750 | 1,500 |
| Professional | 25 | 100 | 5,000 | 10,000 |
| Enterprise | 250 | 1,000 | 100,000 | 200,000 |

Platform administrators can override limits for an individual tenant.

## White label

Per-company branding supports:

- displayed company/brand name
- primary UI color
- PNG/JPEG/WEBP logo
- contact email
- website
- Facebook
- LinkedIn
- YouTube
- X
- TikTok
- custom domain
- optional Powered by NEXVARY display

The company workspace reads its own tenant settings and renders the selected identity.

## Custom domains

A custom domain is normalized as a hostname such as:

`crm.company.com`

The public branding resolver maps the host to the correct tenant identity. A web deployment can use this to preselect the tenant at sign-in without asking for the company slug.

DNS, TLS certificates and reverse-proxy routing remain deployment infrastructure responsibilities; they are not fabricated by the application.

## Integration credentials

The Platform Admin can store per-tenant provider configuration. Public configuration and secret configuration are separated.

Secret configuration is encrypted using Fernet with a key derived from the installation's integration master secret. Read APIs return only the names of configured secret keys, never their values.

Examples:

- WhatsApp Business
- OpenAI
- Telegram
- Instagram / Messenger
- custom providers

## Desktop security

The Windows desktop launcher automatically generates and persists:

- JWT secret
- platform administration key
- integration encryption master secret

The user does not need a terminal to create these values.

## Audit and backups

Company-level material changes remain auditable. Operational exports exclude:

- user password hashes
- integration encrypted-secret ciphertext

The white-label SaaS profile and non-secret integration configuration are included so operational configuration is not lost.
