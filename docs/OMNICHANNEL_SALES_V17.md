# Omnichannel Sales v1.7.0

## Source inspiration

This release reviews and adapts useful commerce patterns from the separate NEXVARY-DA project while leaving that project unchanged.

Reviewed source:
- Repository: \`nexvary/NEXVARY-DA\`
- Branch snapshot: \`dev/stage-551-product-evidence\`
- Commit: \`67e3f7e85e8f30c3679812efedd054d7dca45e44\`

The RealEstate platform does not copy NEXVARY-DA's product-camera catalog or video-specific logic. It adopts only reusable sales/commerce architecture that fits real-estate operations.

## Added to RealEstate White-Label

### Durable sales state
Each conversation has a tenant-scoped sales state containing:
- text / voice preference
- journey stage
- lead score
- assigned user
- campaign / ad attribution
- grounded auto-reply preference
- human-handoff requirement and reason

### Inbound deduplication
Inbound events are persisted with a unique tenant + channel + external-message identifier. Repeated provider deliveries do not create duplicate customer messages or duplicate campaign-conversation events.

### Grounded sales replies
Reply preparation reads:
- available units from the transactional database
- related tenant knowledge evidence

Price and availability are never invented.

If no matching inventory is available, the platform does not fabricate a substitute. It marks the conversation for human handoff and creates a follow-up task.

### Approval-aware Outbox
Prepared outbound messages are durable records with:
- type
- body / media URL
- grounding flag
- confidence
- approval requirement
- attempts
- provider message ID
- failure detail
- sent timestamp

Automatic approval requires all of:
- tenant explicitly enabled grounded auto-replies for the conversation
- response is grounded
- no human handoff is required
- source confidence >= 0.82

Otherwise the message waits for human approval.

### Official WhatsApp dispatch foundation
Approved WhatsApp messages can be sent through the configured tenant WhatsApp Cloud API channel.

The transport:
- uses HTTPS Meta Graph endpoints
- reads the encrypted tenant access token at runtime
- never returns the access token to the browser
- records provider message ID
- records failures and attempt count
- writes the successfully sent text back into conversation history

Real provider delivery still requires valid Meta credentials and permissions for that tenant.

### Human handoff
Operators can explicitly hand a conversation to staff. Missing grounded inventory also triggers handoff automatically. A follow-up task is created so the request is not lost.

### Voice preference
The system persists whether the customer prefers text or voice. For voice-preferring customers the reply planner produces at most three short segments using a professional female voice profile. TTS synthesis remains a separate provider step.

### Marketing attribution
Campaign and ad identifiers can persist from first conversation and later receive events such as:
- conversation
- qualified
- viewing
- reservation
- contract
- revenue

Campaign summaries expose event counts and attributed revenue per tenant.

## Safety boundary

v1.7.0 does not enable uncontrolled autonomous messaging.

The system fails closed:
- low confidence -> approval
- no grounding -> approval / handoff
- missing inventory -> handoff
- disabled auto-replies -> approval
- provider failure -> failed outbox record, not silent success
