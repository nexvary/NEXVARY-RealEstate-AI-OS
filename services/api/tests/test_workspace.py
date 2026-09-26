from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_setup_status_reports_existing_tenants():
    response = client.get("/api/v1/setup/status")
    assert response.status_code == 200
    data = response.json()
    assert data["needs_setup"] is False
    assert data["tenant_count"] == 2


def test_knowledge_documents_are_tenant_scoped_and_queryable(admin_headers, other_tenant_headers):
    created = client.post(
        "/api/v1/knowledge/documents",
        headers=admin_headers,
        json={
            "title": "Project Atlas brochure",
            "category": "brochure",
            "source_name": "atlas.pdf",
            "content": "Project Atlas is located in New Cairo. The project offers apartments with landscaped courtyards and a clubhouse. Payment plans vary by unit.",
        },
    )
    assert created.status_code == 201
    assert created.json()["chunk_count"] >= 1

    query = client.post(
        "/api/v1/knowledge/query",
        headers=admin_headers,
        json={"question": "Where is Project Atlas located?", "limit": 5},
    )
    assert query.status_code == 200
    data = query.json()
    assert data["mode"] == "local-grounded-retrieval"
    assert data["hits"]
    assert data["hits"][0]["document_title"] == "Project Atlas brochure"

    isolated = client.post(
        "/api/v1/knowledge/query",
        headers=other_tenant_headers,
        json={"question": "Project Atlas"},
    )
    assert isolated.status_code == 200
    assert isolated.json()["hits"] == []


def test_inbox_and_messages_flow(admin_headers, sales_headers):
    lead = client.post(
        "/api/v1/leads",
        headers=sales_headers,
        json={"full_name": "WhatsApp Lead", "phone": "01012345678", "source": "whatsapp"},
    )
    assert lead.status_code == 201

    conversation = client.post(
        "/api/v1/inbox/conversations",
        headers=sales_headers,
        json={
            "lead_id": lead.json()["id"],
            "channel": "whatsapp",
            "external_contact": "+201012345678",
            "display_name": "WhatsApp Lead",
        },
    )
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]

    incoming = client.post(
        f"/api/v1/inbox/conversations/{conversation_id}/messages",
        headers=sales_headers,
        json={
            "direction": "inbound",
            "sender": "+201012345678",
            "body": "I need a three-bedroom apartment in New Cairo.",
        },
    )
    assert incoming.status_code == 201

    outgoing = client.post(
        f"/api/v1/inbox/conversations/{conversation_id}/messages",
        headers=sales_headers,
        json={
            "direction": "outbound",
            "sender": "sales@example.com",
            "body": "I will check the currently available inventory.",
        },
    )
    assert outgoing.status_code == 201

    messages = client.get(
        f"/api/v1/inbox/conversations/{conversation_id}/messages",
        headers=admin_headers,
    )
    assert messages.status_code == 200
    assert [item["direction"] for item in messages.json()] == ["inbound", "outbound"]


def test_followup_task_lifecycle(sales_headers):
    due_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    task = client.post(
        "/api/v1/tasks",
        headers=sales_headers,
        json={"title": "Call qualified lead", "due_at": due_at},
    )
    assert task.status_code == 201
    assert task.json()["status"] == "open"

    listed = client.get("/api/v1/tasks?status=open", headers=sales_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    completed = client.post(
        f"/api/v1/tasks/{task.json()['id']}/complete",
        headers=sales_headers,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "done"
