# Automation Studio v1.6.0

## Purpose

Automation Studio adds a visual workflow layer to the White-Label RealEstate AI OS. It is inspired by node-based automation tools, but execution is deliberately constrained to authenticated, tenant-scoped application actions.

It does **not** expose PowerShell, shell commands or arbitrary code execution.

## Visual builder

Each workflow is a directed acyclic graph composed of nodes and routed edges.

The desktop interface provides:

- workflow creation and selection
- node palette grouped by trigger, data, logic, action, approval and output
- drag-to-position nodes on a grid canvas
- visual SVG connections
- route labels such as success / true / false / approved / rejected
- node configuration inspector
- graph validation and save
- workflow activation / disabling
- workflow duplication
- manual release-test runner
- run history
- human approval controls

Once a workflow has execution history its graph becomes immutable. The user duplicates it to create an editable revision, preserving auditability of historical runs.

## Safe node catalog

v1.6.0 provides these node types:

- `trigger.manual`
- `trigger.lead_created`
- `trigger.unit_updated`
- `data.lead_lookup`
- `data.inventory_search`
- `condition.field_equals`
- `action.create_task`
- `action.prepare_message`
- `action.internal_note`
- `action.seo_sync_project`
- `approval.human`
- `output.summary`

The trigger node types define reusable entry semantics. v1.6.0 includes a real manual runner; automatic scheduler/webhook dispatch for every trigger type is a later runtime layer and is not falsely represented as active.

## Transactional grounding

Inventory Search queries the authenticated tenant's transactional database and returns only units whose current status is `available`.

Optional filters include:

- city
- unit type
- bedrooms
- maximum price
- result limit

Lead Lookup reads only the authenticated tenant's CRM.

SEO Project Sync reuses the deterministic project/unit SEO generator and therefore derives price, availability and project/unit facts from the database.

## Message safety

`action.prepare_message` creates prepared text inside the workflow context.

It does **not** imply that WhatsApp, Messenger or another external provider actually sent the message.

External delivery must use a separately configured provider action with the required channel policy, credentials and audit controls.

## Human approval

The Human Approval node pauses a workflow and creates a pending approval record.

An authorized owner/admin/sales manager can:

- approve
- reject

Approved and rejected edges can lead to different downstream nodes. The decision and reviewer are persisted.

## Tenant isolation

Workflow definitions, nodes, edges, runs, node runs and approvals all carry `tenant_id`.

Internal-note actions additionally verify that the target conversation belongs to the authenticated tenant before inserting any message.

## Audit and backup

Automation definitions and run history are included in the tenant operational backup:

- workflows
- nodes
- edges
- runs
- node runs
- approvals

Material graph changes and runs also generate AuditEvent records.

## Release gates

API tests verify:

- no shell execution capability in the node catalog
- DAG cycle rejection
- internal task/message workflow execution
- true/false routing
- human approval pause/resume
- immutable run history
- duplicate-before-edit behavior
- tenant isolation
- cross-tenant conversation protection

Playwright verifies that a user can build a visual workflow through the GUI, connect nodes, save the graph and run it successfully.

The Windows release gate then builds the production web UI, runs the API and browser tests, freezes the desktop application, compiles the Inno Setup installer and generates SHA-256.
