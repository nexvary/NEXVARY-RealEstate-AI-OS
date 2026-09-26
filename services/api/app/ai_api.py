from __future__ import annotations

import re
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Project, Unit, UnitStatus
from .policy import RequestContext, get_request_context
from .quota import consume_ai_request
from .workspace_models import KnowledgeChunk, KnowledgeDocument

router = APIRouter(prefix="/api/v1")


def terms(value: str) -> set[str]:
    return {item for item in re.findall(r"[A-Za-z0-9]+|[\u0621-\u063A\u0641-\u064A]+", value.casefold()) if len(item) > 2}


class SalesAssistRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    city: str | None = None
    max_price: Decimal | None = Field(default=None, ge=0)
    min_price: Decimal | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0, le=30)
    unit_type: str | None = None
    limit: int = Field(default=6, ge=1, le=20)


class UnitSuggestion(BaseModel):
    id: str
    code: str
    project_id: str
    unit_type: str
    bedrooms: int | None
    area_sqm: Decimal
    price: Decimal
    currency: str


class KnowledgeEvidence(BaseModel):
    document_title: str
    source_name: str | None
    chunk_position: int
    text: str
    score: int


class SalesAssistResponse(BaseModel):
    answer: str
    units: list[UnitSuggestion]
    evidence: list[KnowledgeEvidence]
    grounding: list[str]
    mode: str = "grounded-local-copilot"


@router.post("/ai/sales/assist", response_model=SalesAssistResponse)
def sales_assist(
    payload: SalesAssistRequest,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> SalesAssistResponse:
    consume_ai_request(db, ctx.tenant_id)
    unit_query = (
        select(Unit)
        .join(Project, Unit.project_id == Project.id)
        .where(Unit.tenant_id == ctx.tenant_id, Unit.status == UnitStatus.available)
    )
    if payload.city:
        unit_query = unit_query.where(func.lower(Project.city) == payload.city.lower())
    if payload.max_price is not None:
        unit_query = unit_query.where(Unit.price <= payload.max_price)
    if payload.min_price is not None:
        unit_query = unit_query.where(Unit.price >= payload.min_price)
    if payload.bedrooms is not None:
        unit_query = unit_query.where(Unit.bedrooms == payload.bedrooms)
    if payload.unit_type:
        unit_query = unit_query.where(func.lower(Unit.unit_type) == payload.unit_type.lower())

    units = list(db.scalars(unit_query.order_by(Unit.price.asc()).limit(payload.limit)).all())

    query_terms = terms(payload.question)
    evidence_rows = db.execute(
        select(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeChunk.tenant_id == ctx.tenant_id)
    ).all()
    evidence: list[KnowledgeEvidence] = []
    for chunk, document in evidence_rows:
        haystack = " ".join(
            [document.title, document.source_name or "", chunk.text]
        ).casefold()
        score = sum(10 for term in query_terms if term.casefold() in haystack)
        if score > 0:
            evidence.append(
                KnowledgeEvidence(
                    document_title=document.title,
                    source_name=document.source_name,
                    chunk_position=chunk.position,
                    text=chunk.text,
                    score=score,
                )
            )
    evidence.sort(key=lambda item: item.score, reverse=True)
    evidence = evidence[:5]

    arabic = bool(re.search(r"[\u0600-\u06FF]", payload.question))
    if arabic:
        if units:
            answer = f"وجدت {len(units)} وحدة متاحة مطابقة للمرشحات الحالية. الأسعار وحالة التوافر مأخوذة مباشرة من قاعدة البيانات."
        else:
            answer = "لم أجد وحدة متاحة مطابقة للمرشحات الحالية في قاعدة البيانات."
        if evidence:
            answer += f" كما وجدت {len(evidence)} مرجعًا مرتبطًا بالسؤال في قاعدة المعرفة."
    else:
        if units:
            answer = f"I found {len(units)} currently available units matching the active filters. Pricing and availability come directly from the transactional database."
        else:
            answer = "I found no currently available units matching the active filters in the transactional database."
        if evidence:
            answer += f" I also found {len(evidence)} relevant knowledge-base references."

    return SalesAssistResponse(
        answer=answer,
        units=[
            UnitSuggestion(
                id=item.id,
                code=item.code,
                project_id=item.project_id,
                unit_type=item.unit_type,
                bedrooms=item.bedrooms,
                area_sqm=item.area_sqm,
                price=item.price,
                currency=item.currency,
            )
            for item in units
        ],
        evidence=evidence,
        grounding=["transactional_inventory", "tenant_scoped_knowledge"],
    )
