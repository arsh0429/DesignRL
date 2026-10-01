from fastapi.testclient import TestClient
import json

from server.app import app


client = TestClient(app)


def test_root_serves_interactive_demo():
    response = client.get("/")

    assert response.status_code == 200
    assert "DesignRL Interactive Demo" in response.text
    assert "Site Grid" in response.text
    assert 'id="gridSvg"' in response.text


def test_demo_alias_serves_interactive_demo():
    response = client.get("/demo")

    assert response.status_code == 200
    assert "Element Inspector" in response.text
    assert "Live Results" in response.text
    assert "data-start-episode" in response.text


def test_tasks_endpoint_still_lists_registry():
    response = client.get("/tasks")

    assert response.status_code == 200
    payload = response.json()
    task_ids = {task["id"] for task in payload["tasks"]}
    assert {"task1_warehouse", "task2_office", "task3_hospital"} <= task_ids


def test_reset_accepts_empty_body():
    response = client.post("/reset")

    assert response.status_code == 200
    payload = response.json()
    assert "session_id" in payload
    assert "observation" in payload


def test_step_requires_existing_session():
    assert client.post("/step", json={"action": {"action_type": "done"}}).status_code == 400
    assert client.post("/step", json={"session_id": "missing", "action": {"action_type": "done"}}).status_code == 404
    session_id = client.post("/reset").json()["session_id"]
    assert client.post("/step", json={"session_id": session_id}).status_code == 400


def test_grade_rejects_mismatched_session_task():
    session_id = client.post("/reset", json={"task_id": "task1_warehouse"}).json()["session_id"]
    response = client.post("/grade", json={"task_id": "task3_hospital", "session_id": session_id})
    assert response.status_code == 400


def test_reset_step_and_grade_round_trip():
    session_id = client.post("/reset", json={"task_id": "task1_warehouse"}).json()["session_id"]
    placed = client.post("/step", json={
        "session_id": session_id,
        "action": {"action_type": "place_column", "grid_x": 0, "grid_y": 0,
                   "floor": 0, "section": "HEB200"},
    })
    assert placed.status_code == 200
    assert placed.json()["observation"]["n_elements_placed"] == 1
    graded = client.post("/grade", json={"task_id": "task1_warehouse", "session_id": session_id})
    assert graded.status_code == 200
    finished = client.post("/step", json={"session_id": session_id, "message": json.dumps({"action_type": "done"})})
    assert finished.status_code == 200
    assert finished.json()["done"] is True
    assert finished.json()["score"] == graded.json()["score"]
