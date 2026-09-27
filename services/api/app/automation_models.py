from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class AutomationWorkflowStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    disabled = "disabled"


class AutomationRunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    waiting_approval = "waiting_approval"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class AutomationNodeRunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    waiting_approval = "waiting_approval"
    succeeded = "succeeded"
    skipped = "skipped"
    failed = "failed"


class AutomationApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AutomationWorkflow(Base):
    __tablename__ = "automation_workflows"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_automation_tenant_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AutomationWorkflowStatus] = mapped_column(
        Enum(AutomationWorkflowStatus),
        default=AutomationWorkflowStatus.draft,
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AutomationNode(Base):
    __tablename__ = "automation_nodes"
    __table_args__ = (UniqueConstraint("workflow_id", "node_key", name="uq_automation_workflow_node_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("automation_workflows.id"), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    config_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    position_x: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    position_y: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AutomationEdge(Base):
    __tablename__ = "automation_edges"
    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "source_node_key",
            "target_node_key",
            "route",
            name="uq_automation_edge",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("automation_workflows.id"), nullable=False, index=True)
    source_node_key: Mapped[str] = mapped_column(String(100), nullable=False)
    target_node_key: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str] = mapped_column(String(40), default="success", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("automation_workflows.id"), nullable=False, index=True)
    status: Mapped[AutomationRunStatus] = mapped_column(
        Enum(AutomationRunStatus),
        default=AutomationRunStatus.queued,
        nullable=False,
        index=True,
    )
    trigger_type: Mapped[str] = mapped_column(String(100), default="manual", nullable=False, index=True)
    input_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    output_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AutomationNodeRun(Base):
    __tablename__ = "automation_node_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("automation_runs.id"), nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("automation_nodes.id"), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[AutomationNodeRunStatus] = mapped_column(
        Enum(AutomationNodeRunStatus),
        default=AutomationNodeRunStatus.pending,
        nullable=False,
        index=True,
    )
    input_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    output_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AutomationApproval(Base):
    __tablename__ = "automation_approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("automation_runs.id"), nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("automation_nodes.id"), nullable=False, index=True)
    status: Mapped[AutomationApprovalStatus] = mapped_column(
        Enum(AutomationApprovalStatus),
        default=AutomationApprovalStatus.pending,
        nullable=False,
        index=True,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
