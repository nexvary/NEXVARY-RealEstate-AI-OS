from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.main import app
from app.workspace_models import FollowUpTask, InboxConversation, InboxMessage


client = TestClient(app)


def create_workflow(headers, name: str):
    response = client.post(
        "/api/v1/automations",
        headers=headers,
        json={"name": name, "description": "Automation release test"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def save_graph(headers, workflow_id: str, nodes: list[dict], edges: list[dict]):
    response = client.put(
        f"/api/v1/automations/{workflow_id}/graph",
        headers=headers,
        json={"nodes": nodes, "edges": edges},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_catalog_explicitly_disables_shell_and_implicit_external_delivery(admin_headers):
    response = client.get("/api/v1/automations/catalog", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["shell_execution"] is False
    assert body["external_delivery_implicit"] is False
    node_types = {item["type"] for item in body["nodes"]}
    assert "action.prepare_message" in node_types
    assert "approval.human" in node_types
    assert all("powershell" not in item.lower() for item in node_types)


def test_graph_rejects_cycles(admin_headers):
    workflow = create_workflow(admin_headers, "Cycle Guard")
    response = client.put(
        f"/api/v1/automations/{workflow['id']}/graph",
        headers=admin_headers,
        json={
            "nodes": [
                {"node_key": "a", "node_type": "trigger.manual", "title": "A", "config": {}},
                {"node_key": "b", "node_type": "output.summary", "title": "B", "config": {}},
            ],
            "edges": [
                {"source_node_key": "a", "target_node_key": "b", "route": "success"},
                {"source_node_key": "b", "target_node_key": "a", "route": "success"},
            ],
        },
    )
    assert response.status_code == 422
    assert "acyclic" in response.json()["detail"]


def test_manual_workflow_runs_safe_internal_actions(admin_headers):
    workflow = create_workflow(admin_headers, "Safe Manual Automation")
    save_graph(
        admin_headers,
        workflow["id"],
        [
            {"node_key": "start", "node_type": "trigger.manual", "title": "Start", "config": {}, "position_x": 80, "position_y": 80},
            {
                "node_key": "task",
                "node_type": "action.create_task",
                "title": "Create task",
                "config": {
                    "title": "Follow {{input.customer}}",
                    "notes": "Created by Automation Studio",
                    "due_hours": 2,
                },
                "position_x": 320,
                "position_y": 80,
            },
            {
                "node_key": "message",
                "node_type": "action.prepare_message",
                "title": "Prepare message",
                "config": {"template": "Hello {{input.customer}}"},
                "position_x": 560,
                "position_y": 80,
            },
            {
                "node_key": "result",
                "node_type": "output.summary",
                "title": "Return",
                "config": {"fields": ["prepared_message", "task"]},
                "position_x": 800,
                "position_y": 80,
            },
        ],
        [
            {"source_node_key": "start", "target_node_key": "task", "route": "success"},
            {"source_node_key": "task", "target_node_key": "message", "route": "success"},
            {"source_node_key": "message", "target_node_key": "result", "route": "success"},
        ],
    )

    response = client.post(
        f"/api/v1/automations/{workflow['id']}/run",
        headers=admin_headers,
        json={"trigger_type": "manual", "input": {"customer": "Sara"}},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "succeeded"
    assert len(body["node_runs"]) == 4
    assert body["output"]["prepared_message"] == "Hello Sara"
    assert body["output"]["result"]["prepared_message"] == "Hello Sara"

    db = SessionLocal()
    try:
        task = db.scalar(
            select(FollowUpTask).where(
                FollowUpTask.tenant_id == "tenant-a",
                FollowUpTask.title == "Follow Sara",
            )
        )
        assert task is not None
        assert task.notes == "Created by Automation Studio"
    finally:
        db.close()


def test_condition_executes_only_matching_route(admin_headers):
    workflow = create_workflow(admin_headers, "Condition Routing")
    save_graph(
        admin_headers,
        workflow["id"],
        [
            {"node_key": "start", "node_type": "trigger.manual", "title": "Start", "config": {}},
            {
                "node_key": "condition",
                "node_type": "condition.field_equals",
                "title": "Interested?",
                "config": {"field": "input.intent", "value": "interested"},
            },
            {
                "node_key": "true_task",
                "node_type": "action.create_task",
                "title": "Qualified follow-up",
                "config": {"title": "Interested customer", "due_hours": 1},
            },
            {
                "node_key": "false_task",
                "node_type": "action.create_task",
                "title": "Cold follow-up",
                "config": {"title": "Not interested customer", "due_hours": 48},
            },
        ],
        [
            {"source_node_key": "start", "target_node_key": "condition", "route": "success"},
            {"source_node_key": "condition", "target_node_key": "true_task", "route": "true"},
            {"source_node_key": "condition", "target_node_key": "false_task", "route": "false"},
        ],
    )

    response = client.post(
        f"/api/v1/automations/{workflow['id']}/run",
        headers=admin_headers,
        json={"input": {"intent": "interested"}},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "succeeded"
    node_keys = {item["node_key"] for item in body["node_runs"]}
    assert "true_task" in node_keys
    assert "false_task" not in node_keys

    db = SessionLocal()
    try:
        titles = set(
            db.scalars(
                select(FollowUpTask.title).where(FollowUpTask.tenant_id == "tenant-a")
            ).all()
        )
        assert "Interested customer" in titles
        assert "Not interested customer" not in titles
    finally:
        db.close()


def test_human_approval_pauses_and_resumes_approved_route(admin_headers):
    workflow = create_workflow(admin_headers, "Approval Workflow")
    save_graph(
        admin_headers,
        workflow["id"],
        [
            {"node_key": "start", "node_type": "trigger.manual", "title": "Start", "config": {}},
            {
                "node_key": "approval",
                "node_type": "approval.human",
                "title": "Human approval",
                "config": {"prompt": "Approve creating the follow-up task?"},
            },
            {
                "node_key": "approved_task",
                "node_type": "action.create_task",
                "title": "Approved task",
                "config": {"title": "Approved automation task", "due_hours": 1},
            },
            {
                "node_key": "rejected_result",
                "node_type": "output.summary",
                "title": "Rejected result",
                "config": {"fields": ["approval"]},
            },
        ],
        [
            {"source_node_key": "start", "target_node_key": "approval", "route": "success"},
            {"source_node_key": "approval", "target_node_key": "approved_task", "route": "approved"},
            {"source_node_key": "approval", "target_node_key": "rejected_result", "route": "rejected"},
        ],
    )

    started = client.post(
        f"/api/v1/automations/{workflow['id']}/run",
        headers=admin_headers,
        json={"input": {}},
    )
    assert started.status_code == 201
    body = started.json()
    assert body["status"] == "waiting_approval"
    pending = [item for item in body["approvals"] if item["status"] == "pending"]
    assert len(pending) == 1
    assert pending[0]["prompt"] == "Approve creating the follow-up task?"

    decided = client.post(
        f"/api/v1/automations/approvals/{pending[0]['id']}/decision",
        headers=admin_headers,
        json={"decision": "approved", "note": "Approved in test"},
    )
    assert decided.status_code == 200, decided.text
    final = decided.json()
    assert final["status"] == "succeeded"
    assert any(item["node_key"] == "approved_task" for item in final["node_runs"])
    assert not any(item["node_key"] == "rejected_result" for item in final["node_runs"])

    db = SessionLocal()
    try:
        task = db.scalar(
            select(FollowUpTask).where(
                FollowUpTask.tenant_id == "tenant-a",
                FollowUpTask.title == "Approved automation task",
            )
        )
        assert task is not None
    finally:
        db.close()


def test_run_history_locks_graph_but_duplicate_is_editable(admin_headers):
    workflow = create_workflow(admin_headers, "Immutable History")
    graph = save_graph(
        admin_headers,
        workflow["id"],
        [{"node_key": "start", "node_type": "trigger.manual", "title": "Start", "config": {}}],
        [],
    )
    assert graph["workflow"]["nodes_count"] == 1

    run = client.post(
        f"/api/v1/automations/{workflow['id']}/run",
        headers=admin_headers,
        json={"input": {}},
    )
    assert run.status_code == 201
    assert run.json()["status"] == "succeeded"

    edit = client.put(
        f"/api/v1/automations/{workflow['id']}/graph",
        headers=admin_headers,
        json={
            "nodes": [
                {"node_key": "start", "node_type": "trigger.manual", "title": "Changed", "config": {}}
            ],
            "edges": [],
        },
    )
    assert edit.status_code == 409
    assert "Duplicate" in edit.json()["detail"]

    duplicate = client.post(
        f"/api/v1/automations/{workflow['id']}/duplicate",
        headers=admin_headers,
    )
    assert duplicate.status_code == 201
    copy_id = duplicate.json()["workflow"]["id"]
    changed = client.put(
        f"/api/v1/automations/{copy_id}/graph",
        headers=admin_headers,
        json={
            "nodes": [
                {"node_key": "start", "node_type": "trigger.manual", "title": "Changed", "config": {}}
            ],
            "edges": [],
        },
    )
    assert changed.status_code == 200


def test_workflow_and_runs_are_tenant_isolated(admin_headers, other_tenant_headers):
    workflow = create_workflow(admin_headers, "Tenant Isolation Workflow")
    save_graph(
        admin_headers,
        workflow["id"],
        [{"node_key": "start", "node_type": "trigger.manual", "title": "Start", "config": {}}],
        [],
    )
    denied = client.get(f"/api/v1/automations/{workflow['id']}", headers=other_tenant_headers)
    assert denied.status_code == 404

    denied_runs = client.get(
        f"/api/v1/automations/{workflow['id']}/runs",
        headers=other_tenant_headers,
    )
    assert denied_runs.status_code == 404


def test_internal_note_cannot_target_other_tenant_conversation(admin_headers):
    db = SessionLocal()
    try:
        conversation = InboxConversation(
            tenant_id="tenant-b",
            channel="manual",
            external_contact="other-tenant-contact",
            display_name="Other Tenant",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    finally:
        db.close()

    workflow = create_workflow(admin_headers, "Cross Tenant Note Guard")
    save_graph(
        admin_headers,
        workflow["id"],
        [
            {"node_key": "start", "node_type": "trigger.manual", "title": "Start", "config": {}},
            {
                "node_key": "note",
                "node_type": "action.internal_note",
                "title": "Internal note",
                "config": {"conversation_id": conversation_id, "body": "Must not cross tenant"},
            },
        ],
        [{"source_node_key": "start", "target_node_key": "note", "route": "success"}],
    )

    response = client.post(
        f"/api/v1/automations/{workflow['id']}/run",
        headers=admin_headers,
        json={"input": {}},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert "Conversation not found" in response.json()["error"]

    db = SessionLocal()
    try:
        leaked = db.scalar(
            select(InboxMessage).where(
                InboxMessage.conversation_id == conversation_id,
                InboxMessage.tenant_id == "tenant-a",
            )
        )
        assert leaked is None
    finally:
        db.close()
