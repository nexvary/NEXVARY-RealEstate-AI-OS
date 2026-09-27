# Growth Intelligence v1.7.0

## Purpose

v1.7.0 brings selected high-value operating patterns from NEXVARY's Marketing OS work into the RealEstate White-Label platform without modifying the NEXVARY-DA source project.

The release focuses only on capabilities that improve real-estate acquisition, sales follow-up, evidence delivery and revenue measurement.

## Campaigns

Each tenant can create campaigns with:

- channel
- objective
- status
- budget
- actual spend
- currency
- UTM source / medium / campaign
- start/end window

Campaign data is tenant isolated.

## Customer Journeys

A chronological journey is maintained per lead.

The core CRM now records important milestones automatically:

- lead_created
- stage changes
- viewing_scheduled
- reservation_created
- deal_won

Additional touchpoints can be recorded with an optional campaign and channel, such as:

- campaign_touch
- message_received
- brochure_sent
- video_sent
- viewing_requested
- follow_up

## Revenue attribution

Campaign reporting uses a clearly named **last-touch** model.

For completed/active contracts, the system finds the most recent campaign touch before signing and reports:

- leads touched
- contracts attributed by last touch
- last-touch contract revenue
- spend
- cost per lead
- last-touch ROAS

This is deterministic attribution based on stored events. It does not claim causality beyond the selected attribution rule.

## Audience 360

Tenant users can define reusable lead segments using structured CRM fields:

- source
- lead status
- minimum score
- preferred city
- minimum budget
- maximum budget

The preview endpoint runs those rules against current tenant leads.

## Property Media Library

Projects and units can have structured media assets:

- image
- video
- PDF
- floorplan
- virtual tour

Each asset records:

- project / unit relationship
- tags
- source kind: company / developer / verified / generated
- verified flag

The grounded AI Sales Copilot now returns related tenant media alongside matching transactional units.

It still does not invent prices, availability or media.

## Sales Playbooks

Teams can create stage-aware playbooks containing repeatable sales steps.

Examples:

- qualification
- viewing preparation
- post-viewing follow-up
- negotiation
- closing

Playbooks guide staff; they do not silently change transactional records.

## Voice of Customer

Feedback can be recorded against a lead or conversation with:

- channel
- category
- optional 1–5 rating
- customer comment

The summary endpoint reports total feedback, rated count, average rating and category counts.

No sentiment is invented when the user did not provide one.

## Safety and tenancy

- All new data is tenant scoped.
- Campaign and media records from another tenant are not visible.
- Project/unit media references are validated against tenant ownership.
- Journey events validate lead, campaign and conversation ownership.
- Revenue attribution uses real Contract values.
- Property media is explicitly separate from transactional price/availability truth.
- Backup export includes the new Growth Intelligence tables.

## Verification

API tests cover:

- campaign creation
- journey milestones
- last-touch contract attribution
- Audience 360 filtering
- verified property media returned by the grounded Sales Copilot
- playbooks
- Voice of Customer
- cross-tenant isolation

The browser Release Gate covers the Growth Intelligence UI flow for campaigns, journeys, audiences, media, playbooks and feedback.
