# Bank Transfer Billing v1.4.0

## Policy

NEXVARY RealEstate AI OS v1.4.0 uses **bank transfer only** for platform subscription payments.

There is no card-payment gateway in this release.

A bank transfer never marks an invoice paid automatically. The required sequence is:

1. Platform Admin creates one or more receiving bank accounts.
2. A tenant sees only active receiving accounts.
3. The tenant selects an open/overdue invoice.
4. The tenant submits:
   - receiving bank account
   - exact invoice amount/currency
   - sender name
   - sender bank (optional)
   - transfer reference
   - transfer date/time
   - optional receipt link/note
5. The invoice enters `pending_verification`.
6. Platform Admin compares the submission against the bank statement.
7. Platform Admin approves or rejects the transfer.
8. Only approval changes the invoice to `paid`.

## Controls

### Amount and currency matching

The API rejects a transfer when:

- the amount is not exactly equal to the invoice total;
- the transfer currency differs from the invoice currency;
- the selected receiving account uses a different currency;
- the receiving account is inactive.

### Duplicate protection

The same transfer reference cannot be reused for the same receiving bank account.

An invoice cannot have a second pending/approved transfer while another valid verification record exists.

### Tenant isolation

Tenant billing APIs return only the authenticated tenant's:

- invoices
- transfer submissions

Receiving bank accounts are platform configuration and are exposed read-only to tenants when active.

### Approval

When Platform Admin approves a transfer:

- transfer status becomes `approved`;
- reviewer email and review time are recorded;
- invoice status becomes `paid`;
- invoice `paid_at` is set;
- linked SaaS subscription becomes active;
- linked subscription period is renewed according to its billing cycle;
- an audit event is recorded.

### Rejection

When rejected:

- transfer status becomes `rejected`;
- rejection reason, reviewer and review time are recorded;
- the invoice returns to `open` or `overdue`;
- an audit event is recorded.

## UI

Tenant owners/admins receive a dedicated **Subscription & Bank Transfer** workspace with:

- invoice list
- active bank accounts
- transfer instructions
- transfer-submission form
- pending-verification state
- transfer history

Platform Admin receives:

- bank-account management
- pending transfer queue
- receipt/reference information
- approve/reject actions

Direct "mark paid" is not exposed in the Platform Admin user interface; the normal payment path is verified bank transfer.

## Security

Bank-transfer records contain no card data.

Bank details are non-secret operational configuration.

Integration secrets used elsewhere in the platform remain encrypted at rest and are not mixed with billing transfer records.
