from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .automation_models import (
    AutomationApproval,
    AutomationApprovalStatus,
    AutomationEdge,
    AutomationNode,
    AutomationNodeRun,
    AutomationNodeRunStatus,
    AutomationRun,
    AutomationRunStatus,
    AutomationWorkflow,
    AutomationWorkflowStatus,
)
from .commercial_api import _project_page, _unit_page
from .db import get_db
from .models import AuditEvent, Lead, Project, Unit, UnitStatus, UserRole
from .policy import RequestContext, get_request_context, require_roles
from .seo_models import SEOProject
from .workspace_models import FollowUpTask, InboxMessage, MessageDirection

router = APIRouter(prefix="/api/v1/automations")
automation_editor = require_roles(UserRole.owner, UserRole.admin, UserRole.sales_manager)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


def dumps(value: Any) -> str:
    return json.dumps(json_value(value), ensure_ascii=False, separators=(",", ":"))


def loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


NODE_CATALOG = [
    {
        "type": "trigger.manual",
        "category": "trigger",
        "label_ar": "تشغيل يدوي",
        "label_en": "Manual Trigger",
        "description_ar": "بدء الـWorkflow من زر Run.",
        "description_en": "Start the workflow from the Run button.",
    },
    {
        "type": "trigger.lead_created",
        "category": "trigger",
        "label_ar": "عميل جديد",
        "label_en": "Lead Created",
        "description_ar": "نقطة دخول مخصصة لحدث عميل جديد.",
        "description_en": "Entry point for a new-lead event.",
    },
    {
        "type": "trigger.unit_updated",
        "category": "trigger",
        "label_ar": "تحديث وحدة",
        "label_en": "Unit Updated",
        "description_ar": "نقطة دخول عند تغير بيانات وحدة.",
        "description_en": "Entry point for a unit-change event.",
    },
    {
        "type": "data.lead_lookup",
        "category": "data",
        "label_ar": "قراءة العميل",
        "label_en": "Lead Lookup",
        "description_ar": "قراءة عميل من قاعدة الشركة.",
        "description_en": "Load a tenant lead from the database.",
    },
    {
        "type": "data.inventory_search",
        "category": "data",
        "label_ar": "بحث المخزون",
        "label_en": "Inventory Search",
        "description_ar": "البحث في الوحدات المتاحة فقط.",
        "description_en": "Search available transactional inventory.",
    },
    {
        "type": "condition.field_equals",
        "category": "logic",
        "label_ar": "شرط",
        "label_en": "Condition",
        "description_ar": "تقسيم المسار إلى true/false.",
        "description_en": "Route execution through true/false edges.",
    },
    {
        "type": "action.create_task",
        "category": "action",
        "label_ar": "إنشاء مهمة",
        "label_en": "Create Task",
        "description_ar": "إنشاء متابعة داخل CRM.",
        "description_en": "Create a CRM follow-up task.",
    },
    {
        "type": "action.prepare_message",
        "category": "action",
        "label_ar": "تجهيز رد",
        "label_en": "Prepare Message",
        "description_ar": "تجهيز نص رسالة دون إرسال خارجي تلقائي.",
        "description_en": "Prepare message text without external delivery.",
    },
    {
        "type": "action.internal_note",
        "category": "action",
        "label_ar": "ملاحظة داخلية",
        "label_en": "Internal Note",
        "description_ar": "إضافة ملاحظة إلى محادثة موجودة.",
        "description_en": "Add an internal note to an existing conversation.",
    },
    {
        "type": "action.seo_sync_project",
        "category": "action",
        "label_ar": "مزامنة SEO",
        "label_en": "SEO Project Sync",
        "description_ar": "تحديث صفحة المشروع وكل وحداته من قاعدة البيانات.",
        "description_en": "Refresh project and unit SEO pages from transactional data.",
    },
    {
        "type": "approval.human",
        "category": "approval",
        "label_ar": "اعتماد بشري",
        "label_en": "Human Approval",
        "description_ar": "إيقاف التشغيل حتى اعتماد مسؤول.",
        "description_en": "Pause the run until an authorized user decides.",
    },
    {
        "type": "output.summary",
        "category": "output",
        "label_ar": "إرجاع النتيجة",
        "label_en": "Return Result",
        "description_ar": "تسجيل ملخص Context النهائي.",
        "description_en": "Persist a compact final workflow result.",
    },
]
ALLOWED_NODE_TYPES = {item["type"] for item in NODE_CATALOG}


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=2000)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=2000)
    status: AutomationWorkflowStatus | None = None


class NodeInput(BaseModel):
    node_key: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")
    node_type: str
    title: str = Field(min_length=1, max_length=180)
    config: dict[str, Any] = Field(default_factory=dict)
    position_x: int = Field(default=80, ge=0, le=10000)
    position_y: int = Field(default=80, ge=0, le=10000)


class EdgeInput(BaseModel):
    source_node_key: str = Field(min_length=1, max_length=100)
    target_node_key: str = Field(min_length=1, max_length=100)
    route: str = Field(default="success", min_length=1, max_length=40)


class GraphInput(BaseModel):
    nodes: list[NodeInput] = Field(min_length=1, max_length=100)
    edges: list[EdgeInput] = Field(default_factory=list, max_length=300)


class RunRequest(BaseModel):
    trigger_type: str = Field(default="manual", max_length=100)
    input: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    decision: AutomationApprovalStatus
    note: str | None = Field(default=None, max_length=2000)


class WorkflowRead(BaseModel):
    id: str
    name: str
    description: str | None
    status: AutomationWorkflowStatus
    version: int
    created_at: datetime
    updated_at: datetime
    nodes_count: int = 0
    edges_count: int = 0


class GraphRead(BaseModel):
    workflow: WorkflowRead
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class RunRead(BaseModel):
    id: str
    workflow_id: str
    status: AutomationRunStatus
    trigger_type: str
    input: dict[str, Any]
    output: dict[str, Any]
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    node_runs: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)


def workflow_for_tenant(db: Session, workflow_id: str, tenant_id: str) -> AutomationWorkflow:
    workflow = db.scalar(
        select(AutomationWorkflow).where(
            AutomationWorkflow.id == workflow_id,
            AutomationWorkflow.tenant_id == tenant_id,
        )
    )
    if workflow is None:
        raise HTTPException(status_code=404, detail="Automation workflow not found")
    return workflow


def run_for_tenant(db: Session, run_id: str, tenant_id: str) -> AutomationRun:
    run = db.scalar(
        select(AutomationRun).where(
            AutomationRun.id == run_id,
            AutomationRun.tenant_id == tenant_id,
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Automation run not found")
    return run


def workflow_read(db: Session, row: AutomationWorkflow) -> WorkflowRead:
    nodes = int(
        db.scalar(
            select(func.count()).select_from(AutomationNode).where(
                AutomationNode.workflow_id == row.id,
                AutomationNode.tenant_id == row.tenant_id,
            )
        )
        or 0
    )
    edges = int(
        db.scalar(
            select(func.count()).select_from(AutomationEdge).where(
                AutomationEdge.workflow_id == row.id,
                AutomationEdge.tenant_id == row.tenant_id,
            )
        )
        or 0
    )
    return WorkflowRead(
        id=row.id,
        name=row.name,
        description=row.description,
        status=row.status,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
        nodes_count=nodes,
        edges_count=edges,
    )


def graph_read(db: Session, workflow: AutomationWorkflow) -> GraphRead:
    nodes = db.scalars(
        select(AutomationNode)
        .where(
            AutomationNode.workflow_id == workflow.id,
            AutomationNode.tenant_id == workflow.tenant_id,
        )
        .order_by(AutomationNode.created_at.asc())
    ).all()
    edges = db.scalars(
        select(AutomationEdge)
        .where(
            AutomationEdge.workflow_id == workflow.id,
            AutomationEdge.tenant_id == workflow.tenant_id,
        )
        .order_by(AutomationEdge.created_at.asc())
    ).all()
    return GraphRead(
        workflow=workflow_read(db, workflow),
        nodes=[
            {
                "id": row.id,
                "node_key": row.node_key,
                "node_type": row.node_type,
                "title": row.title,
                "config": loads(row.config_json, {}),
                "position_x": row.position_x,
                "position_y": row.position_y,
            }
            for row in nodes
        ],
        edges=[
            {
                "id": row.id,
                "source_node_key": row.source_node_key,
                "target_node_key": row.target_node_key,
                "route": row.route,
            }
            for row in edges
        ],
    )


def run_read(db: Session, row: AutomationRun) -> RunRead:
    node_runs = db.scalars(
        select(AutomationNodeRun)
        .where(AutomationNodeRun.run_id == row.id, AutomationNodeRun.tenant_id == row.tenant_id)
        .order_by(AutomationNodeRun.started_at.asc().nullslast(), AutomationNodeRun.id.asc())
    ).all()
    approvals = db.scalars(
        select(AutomationApproval)
        .where(AutomationApproval.run_id == row.id, AutomationApproval.tenant_id == row.tenant_id)
        .order_by(AutomationApproval.created_at.asc())
    ).all()
    return RunRead(
        id=row.id,
        workflow_id=row.workflow_id,
        status=row.status,
        trigger_type=row.trigger_type,
        input=loads(row.input_json, {}),
        output=loads(row.output_json, {}),
        error=row.error,
        started_at=row.started_at,
        finished_at=row.finished_at,
        created_at=row.created_at,
        node_runs=[
            {
                "id": item.id,
                "node_id": item.node_id,
                "node_key": item.node_key,
                "status": item.status.value,
                "input": loads(item.input_json, {}),
                "output": loads(item.output_json, {}),
                "error": item.error,
                "started_at": item.started_at,
                "finished_at": item.finished_at,
            }
            for item in node_runs
        ],
        approvals=[
            {
                "id": item.id,
                "node_id": item.node_id,
                "status": item.status.value,
                "prompt": item.prompt,
                "reviewed_by_user_id": item.reviewed_by_user_id,
                "reviewed_at": item.reviewed_at,
                "created_at": item.created_at,
            }
            for item in approvals
        ],
    )


def validate_graph(payload: GraphInput) -> list[str]:
    keys = [node.node_key for node in payload.nodes]
    if len(set(keys)) != len(keys):
        raise HTTPException(status_code=422, detail="Node keys must be unique")
    unknown_types = sorted({node.node_type for node in payload.nodes if node.node_type not in ALLOWED_NODE_TYPES})
    if unknown_types:
        raise HTTPException(status_code=422, detail=f"Unsupported node types: {', '.join(unknown_types)}")
    key_set = set(keys)
    for edge in payload.edges:
        if edge.source_node_key not in key_set or edge.target_node_key not in key_set:
            raise HTTPException(status_code=422, detail="Every edge must reference nodes in this workflow")
        if edge.source_node_key == edge.target_node_key:
            raise HTTPException(status_code=422, detail="A node cannot connect to itself")

    outgoing: dict[str, list[str]] = {key: [] for key in keys}
    indegree: dict[str, int] = {key: 0 for key in keys}
    for edge in payload.edges:
        outgoing[edge.source_node_key].append(edge.target_node_key)
        indegree[edge.target_node_key] += 1

    queue = [key for key in keys if indegree[key] == 0]
    ordered: list[str] = []
    while queue:
        current = queue.pop(0)
        ordered.append(current)
        for target in outgoing[current]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(ordered) != len(keys):
        raise HTTPException(status_code=422, detail="Workflow graph must be acyclic")
    return ordered


def path_get(context: dict[str, Any], path: str, default: Any = None) -> Any:
    if not path:
        return default
    current: Any = context
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


_TEMPLATE = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")


def render_template(template: str, context: dict[str, Any]) -> str:
    return _TEMPLATE.sub(lambda match: str(path_get(context, match.group(1), "")), template)


def topological_order(nodes: list[AutomationNode], edges: list[AutomationEdge]) -> list[str]:
    keys = [item.node_key for item in nodes]
    outgoing: dict[str, list[str]] = {key: [] for key in keys}
    indegree: dict[str, int] = {key: 0 for key in keys}
    for edge in edges:
        outgoing.setdefault(edge.source_node_key, []).append(edge.target_node_key)
        indegree[edge.target_node_key] = indegree.get(edge.target_node_key, 0) + 1
    queue = [key for key in keys if indegree.get(key, 0) == 0]
    ordered: list[str] = []
    while queue:
        current = queue.pop(0)
        ordered.append(current)
        for target in outgoing.get(current, []):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return ordered


def available_units(db: Session, tenant_id: str, config: dict[str, Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    city = str(config.get("city") or path_get(context, "input.city", "") or "").strip()
    unit_type = str(config.get("unit_type") or path_get(context, "input.unit_type", "") or "").strip()
    bedrooms = config.get("bedrooms")
    if bedrooms is None:
        bedrooms = path_get(context, "input.bedrooms")
    max_price = config.get("max_price")
    if max_price is None:
        max_price = path_get(context, "input.max_price")
    limit = max(1, min(int(config.get("limit") or 10), 50))

    query = (
        select(Unit, Project)
        .join(Project, Project.id == Unit.project_id)
        .where(
            Unit.tenant_id == tenant_id,
            Project.tenant_id == tenant_id,
            Unit.status == UnitStatus.available,
        )
    )
    if city:
        query = query.where(Project.city.ilike(f"%{city}%"))
    if unit_type:
        query = query.where(Unit.unit_type.ilike(f"%{unit_type}%"))
    if bedrooms not in (None, ""):
        query = query.where(Unit.bedrooms == int(bedrooms))
    if max_price not in (None, ""):
        query = query.where(Unit.price <= Decimal(str(max_price)))
    rows = db.execute(query.order_by(Unit.price.asc()).limit(limit)).all()
    return [
        {
            "id": unit.id,
            "code": unit.code,
            "unit_type": unit.unit_type,
            "bedrooms": unit.bedrooms,
            "area_sqm": str(unit.area_sqm),
            "price": str(unit.price),
            "currency": unit.currency,
            "status": unit.status.value,
            "project_id": project.id,
            "project_name": project.name,
            "city": project.city,
        }
        for unit, project in rows
    ]


def execute_node(
    db: Session,
    ctx: RequestContext,
    node: AutomationNode,
    config: dict[str, Any],
    context: dict[str, Any],
) -> tuple[dict[str, Any], str, bool]:
    node_type = node.node_type
    if node_type.startswith("trigger."):
        return {"trigger": node_type}, "success", False

    if node_type == "data.lead_lookup":
        lead_id = str(config.get("lead_id") or path_get(context, "input.lead_id", "") or "").strip()
        if not lead_id:
            raise ValueError("lead_id is required")
        lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.tenant_id == ctx.tenant_id))
        if lead is None:
            raise ValueError("Lead not found")
        return {
            "lead": {
                "id": lead.id,
                "full_name": lead.full_name,
                "phone": lead.phone,
                "email": lead.email,
                "source": lead.source,
                "status": lead.status.value,
                "score": lead.score,
                "preferred_city": lead.preferred_city,
                "budget": str(lead.budget) if lead.budget is not None else None,
                "bedrooms": lead.bedrooms,
            }
        }, "success", False

    if node_type == "data.inventory_search":
        units = available_units(db, ctx.tenant_id, config, context)
        return {"units": units, "inventory_count": len(units)}, "success", False

    if node_type == "condition.field_equals":
        field = str(config.get("field") or "").strip()
        expected = config.get("value")
        actual = path_get(context, field)
        matched = str(actual).casefold() == str(expected).casefold()
        return {"condition": matched, "field": field, "actual": json_value(actual), "expected": json_value(expected)}, "true" if matched else "false", False

    if node_type == "action.create_task":
        title = render_template(str(config.get("title") or "Automation follow-up"), context)
        notes = render_template(str(config.get("notes") or ""), context) or None
        lead_id = str(config.get("lead_id") or path_get(context, "input.lead_id", "") or "").strip() or None
        if lead_id:
            lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.tenant_id == ctx.tenant_id))
            if lead is None:
                raise ValueError("Lead not found for task")
        due_hours = max(0, min(int(config.get("due_hours") or 24), 24 * 365))
        task = FollowUpTask(
            tenant_id=ctx.tenant_id,
            lead_id=lead_id,
            assigned_user_id=ctx.user_id,
            title=title[:220],
            notes=notes,
            due_at=utcnow() + timedelta(hours=due_hours),
        )
        db.add(task)
        db.flush()
        return {"task": {"id": task.id, "title": task.title, "due_at": task.due_at}}, "success", False

    if node_type == "action.prepare_message":
        template = str(config.get("template") or "")
        if not template:
            raise ValueError("Message template is required")
        body = render_template(template, context)
        return {"prepared_message": body}, "success", False

    if node_type == "action.internal_note":
        conversation_id = str(config.get("conversation_id") or path_get(context, "input.conversation_id", "") or "").strip()
        if not conversation_id:
            raise ValueError("conversation_id is required")
        body = render_template(str(config.get("body") or "Automation note"), context)
        message = InboxMessage(
            tenant_id=ctx.tenant_id,
            conversation_id=conversation_id,
            direction=MessageDirection.internal,
            sender=ctx.actor,
            body=body,
        )
        db.add(message)
        db.flush()
        return {"internal_note": {"id": message.id, "conversation_id": conversation_id, "body": body}}, "success", False

    if node_type == "action.seo_sync_project":
        project_id = str(config.get("project_id") or path_get(context, "input.project_id", "") or "").strip()
        seo_project_id = str(config.get("seo_project_id") or path_get(context, "input.seo_project_id", "") or "").strip()
        if not project_id or not seo_project_id:
            raise ValueError("project_id and seo_project_id are required")
        project = db.scalar(select(Project).where(Project.id == project_id, Project.tenant_id == ctx.tenant_id))
        seo_project = db.scalar(select(SEOProject).where(SEOProject.id == seo_project_id, SEOProject.tenant_id == ctx.tenant_id))
        if project is None or seo_project is None:
            raise ValueError("Project or SEO project not found")
        project_page = _project_page(db, ctx, seo_project, project)
        units = db.scalars(select(Unit).where(Unit.tenant_id == ctx.tenant_id, Unit.project_id == project.id)).all()
        for unit in units:
            _unit_page(db, ctx, seo_project, unit)
        return {
            "seo_sync": {
                "project_id": project.id,
                "project_page_id": project_page.id,
                "unit_pages": len(units),
                "source": "transactional_database",
            }
        }, "success", False

    if node_type == "approval.human":
        return {
            "approval_prompt": render_template(
                str(config.get("prompt") or "Approve this workflow step?"),
                context,
            )
        }, "approval", True

    if node_type == "output.summary":
        fields = config.get("fields")
        if isinstance(fields, list) and fields:
            summary = {str(field): path_get(context, str(field)) for field in fields}
        else:
            summary = context
        return {"result": json_value(summary)}, "success", False

    raise ValueError(f"Unsupported node type: {node_type}")


def continue_run(
    db: Session,
    ctx: RequestContext,
    run: AutomationRun,
    *,
    resume_node_key: str | None = None,
    resume_route: str = "success",
) -> AutomationRun:
    workflow = workflow_for_tenant(db, run.workflow_id, ctx.tenant_id)
    nodes = list(
        db.scalars(
            select(AutomationNode).where(
                AutomationNode.workflow_id == workflow.id,
                AutomationNode.tenant_id == ctx.tenant_id,
            )
        ).all()
    )
    edges = list(
        db.scalars(
            select(AutomationEdge).where(
                AutomationEdge.workflow_id == workflow.id,
                AutomationEdge.tenant_id == ctx.tenant_id,
            )
        ).all()
    )
    if not nodes:
        raise HTTPException(status_code=409, detail="Workflow has no nodes")

    node_map = {node.node_key: node for node in nodes}
    order = topological_order(nodes, edges)
    incoming_count = {key: 0 for key in node_map}
    outgoing: dict[str, list[AutomationEdge]] = {key: [] for key in node_map}
    for edge in edges:
        incoming_count[edge.target_node_key] = incoming_count.get(edge.target_node_key, 0) + 1
        outgoing.setdefault(edge.source_node_key, []).append(edge)

    context = loads(run.output_json, {})
    if not context:
        context = {"input": loads(run.input_json, {}), "nodes": {}}
    context.setdefault("input", loads(run.input_json, {}))
    context.setdefault("nodes", {})

    completed = {
        item.node_key: item
        for item in db.scalars(
            select(AutomationNodeRun).where(
                AutomationNodeRun.run_id == run.id,
                AutomationNodeRun.tenant_id == ctx.tenant_id,
            )
        ).all()
        if item.status in {
            AutomationNodeRunStatus.succeeded,
            AutomationNodeRunStatus.skipped,
        }
    }

    eligible: set[str] = {key for key, count in incoming_count.items() if count == 0}
    if resume_node_key:
        eligible = set()
        for edge in outgoing.get(resume_node_key, []):
            if edge.route in {"success", resume_route}:
                eligible.add(edge.target_node_key)
        completed[resume_node_key] = completed.get(resume_node_key) or None

    for item in db.scalars(
        select(AutomationNodeRun).where(
            AutomationNodeRun.run_id == run.id,
            AutomationNodeRun.tenant_id == ctx.tenant_id,
            AutomationNodeRun.status == AutomationNodeRunStatus.succeeded,
        )
    ).all():
        for edge in outgoing.get(item.node_key, []):
            route = loads(item.output_json, {}).get("_route", "success")
            if edge.route in {"success", route}:
                eligible.add(edge.target_node_key)

    run.status = AutomationRunStatus.running
    if run.started_at is None:
        run.started_at = utcnow()
    run.error = None
    db.flush()

    try:
        for key in order:
            if key in completed or key not in eligible:
                continue
            node = node_map[key]
            node_input = {"context": json_value(context)}
            node_run = db.scalar(
                select(AutomationNodeRun).where(
                    AutomationNodeRun.run_id == run.id,
                    AutomationNodeRun.node_id == node.id,
                )
            )
            if node_run is None:
                node_run = AutomationNodeRun(
                    tenant_id=ctx.tenant_id,
                    run_id=run.id,
                    node_id=node.id,
                    node_key=node.node_key,
                )
                db.add(node_run)
                db.flush()
            node_run.status = AutomationNodeRunStatus.running
            node_run.input_json = dumps(node_input)
            node_run.started_at = utcnow()
            db.flush()

            config = loads(node.config_json, {})
            output, route, waits = execute_node(db, ctx, node, config, context)
            output["_route"] = route
            node_run.output_json = dumps(output)
            context["nodes"][node.node_key] = output
            for name, value in output.items():
                if not name.startswith("_"):
                    context[name] = value

            if waits:
                node_run.status = AutomationNodeRunStatus.waiting_approval
                node_run.finished_at = None
                approval = AutomationApproval(
                    tenant_id=ctx.tenant_id,
                    run_id=run.id,
                    node_id=node.id,
                    prompt=str(output.get("approval_prompt") or "Approval required"),
                )
                db.add(approval)
                run.status = AutomationRunStatus.waiting_approval
                run.output_json = dumps(context)
                db.commit()
                db.refresh(run)
                return run

            node_run.status = AutomationNodeRunStatus.succeeded
            node_run.finished_at = utcnow()
            for edge in outgoing.get(node.node_key, []):
                if edge.route in {"success", route}:
                    eligible.add(edge.target_node_key)
            db.flush()

        run.status = AutomationRunStatus.succeeded
        run.output_json = dumps(context)
        run.finished_at = utcnow()
        db.add(
            AuditEvent(
                tenant_id=ctx.tenant_id,
                actor=ctx.actor,
                action="automation.run.succeeded",
                entity_type="automation_workflow",
                entity_id=workflow.id,
                details=f"run={run.id}",
            )
        )
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        run.status = AutomationRunStatus.failed
        run.error = str(exc)[:2000]
        run.output_json = dumps(context)
        run.finished_at = utcnow()
        db.commit()
        db.refresh(run)
        return run


@router.get("/catalog")
def catalog(_: RequestContext = Depends(get_request_context)) -> dict[str, Any]:
    return {
        "nodes": NODE_CATALOG,
        "execution": "internal-safe-actions",
        "shell_execution": False,
        "external_delivery_implicit": False,
    }


@router.post("", response_model=WorkflowRead, status_code=201)
def create_workflow(
    payload: WorkflowCreate,
    ctx: RequestContext = Depends(automation_editor),
    db: Session = Depends(get_db),
) -> WorkflowRead:
    row = AutomationWorkflow(
        tenant_id=ctx.tenant_id,
        name=payload.name.strip(),
        description=payload.description,
        created_by_user_id=ctx.user_id,
        updated_by_user_id=ctx.user_id,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Workflow name already exists") from exc
    db.refresh(row)
    return workflow_read(db, row)


@router.get("", response_model=list[WorkflowRead])
def list_workflows(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[WorkflowRead]:
    rows = db.scalars(
        select(AutomationWorkflow)
        .where(AutomationWorkflow.tenant_id == ctx.tenant_id)
        .order_by(AutomationWorkflow.updated_at.desc())
    ).all()
    return [workflow_read(db, row) for row in rows]


@router.get("/{workflow_id}", response_model=GraphRead)
def get_workflow(
    workflow_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> GraphRead:
    return graph_read(db, workflow_for_tenant(db, workflow_id, ctx.tenant_id))


@router.patch("/{workflow_id}", response_model=WorkflowRead)
def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    ctx: RequestContext = Depends(automation_editor),
    db: Session = Depends(get_db),
) -> WorkflowRead:
    row = workflow_for_tenant(db, workflow_id, ctx.tenant_id)
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(row, key, value)
    row.updated_by_user_id = ctx.user_id
    db.commit()
    db.refresh(row)
    return workflow_read(db, row)


@router.put("/{workflow_id}/graph", response_model=GraphRead)
def replace_graph(
    workflow_id: str,
    payload: GraphInput,
    ctx: RequestContext = Depends(automation_editor),
    db: Session = Depends(get_db),
) -> GraphRead:
    workflow = workflow_for_tenant(db, workflow_id, ctx.tenant_id)
    existing_runs = int(
        db.scalar(select(func.count()).select_from(AutomationRun).where(AutomationRun.workflow_id == workflow.id))
        or 0
    )
    if existing_runs:
        raise HTTPException(status_code=409, detail="Duplicate this workflow before editing a graph that already has run history")
    validate_graph(payload)

    db.execute(delete(AutomationEdge).where(AutomationEdge.workflow_id == workflow.id))
    db.execute(delete(AutomationNode).where(AutomationNode.workflow_id == workflow.id))
    db.flush()

    for node in payload.nodes:
        db.add(
            AutomationNode(
                tenant_id=ctx.tenant_id,
                workflow_id=workflow.id,
                node_key=node.node_key,
                node_type=node.node_type,
                title=node.title,
                config_json=dumps(node.config),
                position_x=node.position_x,
                position_y=node.position_y,
            )
        )
    for edge in payload.edges:
        db.add(
            AutomationEdge(
                tenant_id=ctx.tenant_id,
                workflow_id=workflow.id,
                source_node_key=edge.source_node_key,
                target_node_key=edge.target_node_key,
                route=edge.route,
            )
        )
    workflow.version += 1
    workflow.updated_by_user_id = ctx.user_id
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="automation.graph.update",
            entity_type="automation_workflow",
            entity_id=workflow.id,
            details=f"nodes={len(payload.nodes)};edges={len(payload.edges)}",
        )
    )
    db.commit()
    db.refresh(workflow)
    return graph_read(db, workflow)


@router.post("/{workflow_id}/duplicate", response_model=GraphRead, status_code=201)
def duplicate_workflow(
    workflow_id: str,
    ctx: RequestContext = Depends(automation_editor),
    db: Session = Depends(get_db),
) -> GraphRead:
    source = workflow_for_tenant(db, workflow_id, ctx.tenant_id)
    graph = graph_read(db, source)
    suffix = utcnow().strftime("%H%M%S")
    target = AutomationWorkflow(
        tenant_id=ctx.tenant_id,
        name=f"{source.name} Copy {suffix}",
        description=source.description,
        status=AutomationWorkflowStatus.draft,
        created_by_user_id=ctx.user_id,
        updated_by_user_id=ctx.user_id,
    )
    db.add(target)
    db.flush()
    for node in graph.nodes:
        db.add(
            AutomationNode(
                tenant_id=ctx.tenant_id,
                workflow_id=target.id,
                node_key=node["node_key"],
                node_type=node["node_type"],
                title=node["title"],
                config_json=dumps(node["config"]),
                position_x=node["position_x"],
                position_y=node["position_y"],
            )
        )
    for edge in graph.edges:
        db.add(
            AutomationEdge(
                tenant_id=ctx.tenant_id,
                workflow_id=target.id,
                source_node_key=edge["source_node_key"],
                target_node_key=edge["target_node_key"],
                route=edge["route"],
            )
        )
    db.commit()
    db.refresh(target)
    return graph_read(db, target)


@router.post("/{workflow_id}/run", response_model=RunRead, status_code=201)
def run_workflow(
    workflow_id: str,
    payload: RunRequest,
    ctx: RequestContext = Depends(automation_editor),
    db: Session = Depends(get_db),
) -> RunRead:
    workflow = workflow_for_tenant(db, workflow_id, ctx.tenant_id)
    if workflow.status == AutomationWorkflowStatus.disabled:
        raise HTTPException(status_code=409, detail="Workflow is disabled")
    node_count = int(
        db.scalar(select(func.count()).select_from(AutomationNode).where(AutomationNode.workflow_id == workflow.id))
        or 0
    )
    if not node_count:
        raise HTTPException(status_code=409, detail="Workflow has no graph")
    run = AutomationRun(
        tenant_id=ctx.tenant_id,
        workflow_id=workflow.id,
        status=AutomationRunStatus.queued,
        trigger_type=payload.trigger_type,
        input_json=dumps(payload.input),
        output_json=dumps({"input": payload.input, "nodes": {}}),
        created_by_user_id=ctx.user_id,
    )
    db.add(run)
    db.flush()
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="automation.run.start",
            entity_type="automation_workflow",
            entity_id=workflow.id,
            details=f"run={run.id};trigger={payload.trigger_type}",
        )
    )
    db.commit()
    db.refresh(run)
    continue_run(db, ctx, run)
    return run_read(db, run)


@router.get("/{workflow_id}/runs", response_model=list[RunRead])
def workflow_runs(
    workflow_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[RunRead]:
    workflow_for_tenant(db, workflow_id, ctx.tenant_id)
    rows = db.scalars(
        select(AutomationRun)
        .where(AutomationRun.workflow_id == workflow_id, AutomationRun.tenant_id == ctx.tenant_id)
        .order_by(AutomationRun.created_at.desc())
        .limit(100)
    ).all()
    return [run_read(db, row) for row in rows]


@router.get("/runs/{run_id}/detail", response_model=RunRead)
def run_detail(
    run_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> RunRead:
    return run_read(db, run_for_tenant(db, run_id, ctx.tenant_id))


@router.post("/approvals/{approval_id}/decision", response_model=RunRead)
def decide_approval(
    approval_id: str,
    payload: ApprovalDecision,
    ctx: RequestContext = Depends(automation_editor),
    db: Session = Depends(get_db),
) -> RunRead:
    if payload.decision not in {AutomationApprovalStatus.approved, AutomationApprovalStatus.rejected}:
        raise HTTPException(status_code=422, detail="Decision must be approved or rejected")
    approval = db.scalar(
        select(AutomationApproval).where(
            AutomationApproval.id == approval_id,
            AutomationApproval.tenant_id == ctx.tenant_id,
        )
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != AutomationApprovalStatus.pending:
        raise HTTPException(status_code=409, detail="Approval has already been decided")
    run = run_for_tenant(db, approval.run_id, ctx.tenant_id)
    node_run = db.scalar(
        select(AutomationNodeRun).where(
            AutomationNodeRun.run_id == run.id,
            AutomationNodeRun.node_id == approval.node_id,
        )
    )
    node = db.scalar(select(AutomationNode).where(AutomationNode.id == approval.node_id))
    if node_run is None or node is None:
        raise HTTPException(status_code=409, detail="Approval node state is missing")

    approval.status = payload.decision
    approval.reviewed_by_user_id = ctx.user_id
    approval.reviewed_at = utcnow()
    previous_output = loads(node_run.output_json, {})
    previous_output["approved"] = payload.decision == AutomationApprovalStatus.approved
    previous_output["review_note"] = payload.note
    previous_output["_route"] = "approved" if payload.decision == AutomationApprovalStatus.approved else "rejected"
    node_run.output_json = dumps(previous_output)
    node_run.status = AutomationNodeRunStatus.succeeded
    node_run.finished_at = utcnow()
    run.output_json = dumps({
        **loads(run.output_json, {}),
        "approval": {
            "status": payload.decision.value,
            "note": payload.note,
        },
    })
    db.commit()

    continue_run(
        db,
        ctx,
        run,
        resume_node_key=node.node_key,
        resume_route="approved" if payload.decision == AutomationApprovalStatus.approved else "rejected",
    )
    return run_read(db, run)
