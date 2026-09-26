from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Lead, User
from .policy import RequestContext, get_request_context, write_sales
from .workspace_models import (
    ConversationChannel,
    FollowUpTask,
    InboxConversation,
    InboxMessage,
    KnowledgeChunk,
    KnowledgeDocument,
    MessageDirection,
    TaskStatus,
)

router = APIRouter(prefix="/api/v1")


def tenant_record(db: Session, model, record_id: str, tenant_id: str):
    record = db.scalar(select(model).where(model.id == record_id, model.tenant_id == tenant_id))
    if record is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return record


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(compact):
        end = min(len(compact), start + size)
        if end < len(compact):
            boundary = compact.rfind(" ", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunks.append(compact[start:end].strip())
        if end >= len(compact):
            break
        start = max(end - overlap, start + 1)
    return [item for item in chunks if item]


def terms(value: str) -> set[str]:
    return {item for item in re.findall(r"[\w\u0600-\u06FF]+", value.lower()) if len(item) > 2}


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=2, max_length=220)
    category: str = Field(default="general", min_length=2, max_length=80)
    source_name: str | None = Field(default=None, max_length=255)
    content: str = Field(min_length=20)


class KnowledgeDocumentRead(BaseModel):
    id: str
    title: str
    category: str
    source_name: str | None
    chunk_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class KnowledgeQuery(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    limit: int = Field(default=5, ge=1, le=12)


class KnowledgeHit(BaseModel):
    document_id: str
    document_title: str
    source_name: str | None
    chunk_position: int
    text: str
    score: int


class KnowledgeQueryResult(BaseModel):
    question: str
    mode: str = "local-grounded-retrieval"
    hits: list[KnowledgeHit]


class ConversationCreate(BaseModel):
    lead_id: str | None = None
    channel: ConversationChannel = ConversationChannel.manual
    external_contact: str = Field(min_length=2, max_length=180)
    display_name: str | None = Field(default=None, max_length=180)


class ConversationRead(BaseModel):
    id: str
    lead_id: str | None
    channel: ConversationChannel
    external_contact: str
    display_name: str | None
    status: str
    last_message_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    direction: MessageDirection
    sender: str = Field(min_length=1, max_length=180)
    body: str = Field(min_length=1, max_length=10000)


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    direction: MessageDirection
    sender: str
    body: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    lead_id: str | None = None
    assigned_user_id: str | None = None
    title: str = Field(min_length=2, max_length=220)
    notes: str | None = None
    due_at: datetime | None = None


class TaskRead(BaseModel):
    id: str
    lead_id: str | None
    assigned_user_id: str | None
    title: str
    notes: str | None
    due_at: datetime | None
    status: TaskStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.post("/knowledge/documents", response_model=KnowledgeDocumentRead, status_code=201)
def create_document(
    payload: KnowledgeDocumentCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> KnowledgeDocument:
    pieces = chunk_text(payload.content)
    document = KnowledgeDocument(
        tenant_id=ctx.tenant_id,
        title=payload.title,
        category=payload.category,
        source_name=payload.source_name,
        content=payload.content,
        chunk_count=len(pieces),
    )
    db.add(document)
    db.flush()
    for index, piece in enumerate(pieces):
        db.add(
            KnowledgeChunk(
                tenant_id=ctx.tenant_id,
                document_id=document.id,
                position=index,
                text=piece,
            )
        )
    db.commit()
    db.refresh(document)
    return document


@router.get("/knowledge/documents", response_model=list[KnowledgeDocumentRead])
def list_documents(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[KnowledgeDocument]:
    return list(
        db.scalars(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.tenant_id == ctx.tenant_id)
            .order_by(KnowledgeDocument.created_at.desc())
        ).all()
    )


@router.post("/knowledge/query", response_model=KnowledgeQueryResult)
def query_knowledge(
    payload: KnowledgeQuery,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> KnowledgeQueryResult:
    query_terms = terms(payload.question)
    rows = db.execute(
        select(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeChunk.tenant_id == ctx.tenant_id)
    ).all()
    scored: list[KnowledgeHit] = []
    for chunk, document in rows:
        chunk_terms = terms(chunk.text)
        overlap = len(query_terms & chunk_terms)
        phrase_bonus = 3 if payload.question.lower() in chunk.text.lower() else 0
        score = overlap * 10 + phrase_bonus
        if score <= 0:
            continue
        scored.append(
            KnowledgeHit(
                document_id=document.id,
                document_title=document.title,
                source_name=document.source_name,
                chunk_position=chunk.position,
                text=chunk.text,
                score=score,
            )
        )
    scored.sort(key=lambda item: item.score, reverse=True)
    return KnowledgeQueryResult(question=payload.question, hits=scored[: payload.limit])


@router.post("/inbox/conversations", response_model=ConversationRead, status_code=201)
def create_conversation(
    payload: ConversationCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> InboxConversation:
    if payload.lead_id:
        tenant_record(db, Lead, payload.lead_id, ctx.tenant_id)
    conversation = InboxConversation(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/inbox/conversations", response_model=list[ConversationRead])
def list_conversations(
    channel: ConversationChannel | None = Query(default=None),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[InboxConversation]:
    query = select(InboxConversation).where(InboxConversation.tenant_id == ctx.tenant_id)
    if channel:
        query = query.where(InboxConversation.channel == channel)
    return list(db.scalars(query.order_by(InboxConversation.last_message_at.desc()).limit(300)).all())


@router.post("/inbox/conversations/{conversation_id}/messages", response_model=MessageRead, status_code=201)
def create_message(
    conversation_id: str,
    payload: MessageCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> InboxMessage:
    conversation = tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    message = InboxMessage(
        tenant_id=ctx.tenant_id,
        conversation_id=conversation.id,
        **payload.model_dump(),
    )
    conversation.last_message_at = datetime.now(timezone.utc)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/inbox/conversations/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[InboxMessage]:
    tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    return list(
        db.scalars(
            select(InboxMessage)
            .where(
                InboxMessage.tenant_id == ctx.tenant_id,
                InboxMessage.conversation_id == conversation_id,
            )
            .order_by(InboxMessage.created_at.asc())
        ).all()
    )


@router.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(
    payload: TaskCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> FollowUpTask:
    if payload.lead_id:
        tenant_record(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.assigned_user_id:
        tenant_record(db, User, payload.assigned_user_id, ctx.tenant_id)
    task = FollowUpTask(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[FollowUpTask]:
    query = select(FollowUpTask).where(FollowUpTask.tenant_id == ctx.tenant_id)
    if status_filter:
        query = query.where(FollowUpTask.status == status_filter)
    return list(db.scalars(query.order_by(FollowUpTask.due_at.asc().nullslast(), FollowUpTask.created_at.desc()).limit(300)).all())


@router.post("/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(
    task_id: str,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> FollowUpTask:
    task = tenant_record(db, FollowUpTask, task_id, ctx.tenant_id)
    if task.status == TaskStatus.cancelled:
        raise HTTPException(status_code=409, detail="Cancelled task cannot be completed")
    task.status = TaskStatus.done
    db.commit()
    db.refresh(task)
    return task
