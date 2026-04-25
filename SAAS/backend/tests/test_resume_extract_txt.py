from fastapi.testclient import TestClient

from app.main import app


def test_extract_txt_ok():
    client = TestClient(app)
    payload = b"Python, FastAPI, SQL. Experiencia com AWS e Docker."
    files = {"file": ("cv.txt", payload, "text/plain")}
    r = client.post("/resume/extract", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "txt"
    assert body["chars"] > 10
    assert "Python" in body["preview"]


def test_recommendations_txt_ok():
    client = TestClient(app)
    payload = b"Python FastAPI SQL Postgres Docker AWS CI/CD"
    files = {"file": ("cv.txt", payload, "text/plain")}
    r = client.post("/recommendations?limit=5", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "txt"
    assert body["chars"] > 10
    assert isinstance(body["recommendations"], list)
    assert len(body["recommendations"]) >= 1

