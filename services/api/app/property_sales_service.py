from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Lead, Project, Unit
from .property_sales_models import AdPropertyReferral, ConversationPropertyContext
from .workspace_models import InboxConversation


def tenant_row(db: Session, model, record_id: str | None, tenant_id: str):
    if not record_id:
        return None
    return db.scalar(select(model).where(model.id == record_id, model.tenant_id == tenant_id))


def resolve_property_referral(
    db: Session,
    *,
    tenant_id: str,
    channel: str,
    ad_id: str | None,
    project_id: str | None = None,
    unit_id: str | None = None,
) -> tuple[AdPropertyReferral | None, Project | None, Unit | None]:
    direct_project = tenant_row(db, Project, project_id, tenant_id)
    direct_unit = tenant_row(db, Unit, unit_id, tenant_id)
    if project_id and direct_project is None:
        raise ValueError("Project not found")
    if unit_id and direct_unit is None:
        raise ValueError("Unit not found")
    if direct_unit and direct_project and direct_unit.project_id != direct_project.id:
        raise ValueError("Unit belongs to a different project")
    if direct_unit and direct_project is None:
        direct_project = tenant_row(db, Project, direct_unit.project_id, tenant_id)

    referral = None
    if ad_id:
        referral = db.scalar(
            select(AdPropertyReferral).where(
                AdPropertyReferral.tenant_id == tenant_id,
                AdPropertyReferral.channel == channel,
                AdPropertyReferral.ad_id == ad_id,
            )
        )
    if direct_project or direct_unit:
        return referral, direct_project, direct_unit
    if referral is None:
        return None, None, None
    project = tenant_row(db, Project, referral.project_id, tenant_id)
    unit = tenant_row(db, Unit, referral.unit_id, tenant_id)
    return referral, project, unit


def ensure_crm_lead(
    db: Session,
    *,
    tenant_id: str,
    external_contact: str,
    display_name: str | None,
    channel: str,
    campaign_id: str | None,
    ad_id: str | None,
    project: Project | None,
    unit: Unit | None,
) -> Lead:
    lead = db.scalar(
        select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.phone == external_contact,
        ).order_by(Lead.created_at.asc())
    )
    if lead is not None:
        return lead

    referral_bits = [
        f"channel={channel}",
        f"campaign={campaign_id}" if campaign_id else "",
        f"ad={ad_id}" if ad_id else "",
        f"project={project.id}" if project else "",
        f"unit={unit.id}" if unit else "",
    ]
    lead = Lead(
        tenant_id=tenant_id,
        full_name=(display_name or external_contact).strip(),
        phone=external_contact,
        source="whatsapp_ad" if channel == "whatsapp" and ad_id else channel,
        preferred_city=project.city if project else None,
        notes="Inbound referral: " + "; ".join(bit for bit in referral_bits if bit),
    )
    db.add(lead)
    db.flush()
    return lead


def upsert_conversation_property_context(
    db: Session,
    *,
    conversation: InboxConversation,
    referral: AdPropertyReferral | None,
    project: Project | None,
    unit: Unit | None,
    campaign_id: str | None,
    ad_id: str | None,
    source_url: str | None,
) -> ConversationPropertyContext | None:
    if not any((referral, project, unit, campaign_id, ad_id, source_url)):
        return None
    row = db.scalar(
        select(ConversationPropertyContext).where(
            ConversationPropertyContext.tenant_id == conversation.tenant_id,
            ConversationPropertyContext.conversation_id == conversation.id,
        )
    )
    if row is None:
        row = ConversationPropertyContext(
            tenant_id=conversation.tenant_id,
            conversation_id=conversation.id,
        )
        db.add(row)
    if referral:
        row.referral_id = referral.id
    if project:
        row.project_id = project.id
    if unit:
        row.unit_id = unit.id
    if campaign_id:
        row.campaign_id = campaign_id
    if ad_id:
        row.ad_id = ad_id
    if source_url:
        row.source_url = source_url
    elif referral and referral.source_url:
        row.source_url = referral.source_url
    db.flush()
    return row


def property_context_payload(db: Session, row: ConversationPropertyContext | None) -> dict[str, Any] | None:
    if row is None:
        return None
    project = tenant_row(db, Project, row.project_id, row.tenant_id)
    unit = tenant_row(db, Unit, row.unit_id, row.tenant_id)
    return {
        "id": row.id,
        "conversation_id": row.conversation_id,
        "referral_id": row.referral_id,
        "campaign_id": row.campaign_id,
        "ad_id": row.ad_id,
        "source_url": row.source_url,
        "project_id": row.project_id,
        "project_name": project.name if project else None,
        "project_city": project.city if project else None,
        "unit_id": row.unit_id,
        "unit_code": unit.code if unit else None,
    }
