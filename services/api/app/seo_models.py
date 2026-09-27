from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class SEOSnapshotKind(str, enum.Enum):
    audit = "audit"
    crawl = "crawl"
    search_console = "search_console"


class SEOChangeStatus(str, enum.Enum):
    planned = "planned"
    cancelled = "cancelled"


class SEOProject(Base):
    __tablename__ = "seo_projects"
    __table_args__ = (UniqueConstraint("tenant_id", "site_url", name="uq_seo_project_tenant_site"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    site_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SEOSnapshot(Base):
    __tablename__ = "seo_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("seo_projects.id"), nullable=False, index=True)
    kind: Mapped[SEOSnapshotKind] = mapped_column(Enum(SEOSnapshotKind), nullable=False, index=True)
    score: Mapped[int | None] = mapped_column(Integer)
    grade: Mapped[str | None] = mapped_column(String(8))
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class SEOChangeDraft(Base):
    __tablename__ = "seo_change_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("seo_projects.id"), nullable=False, index=True)
    upstream_change_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    risk: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[SEOChangeStatus] = mapped_column(Enum(SEOChangeStatus), default=SEOChangeStatus.planned, nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
