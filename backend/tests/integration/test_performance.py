"""T059 — predict latency gate (SC-007: server-side < 2s)."""

import time

from fastapi.testclient import TestClient

from main import app

PAYLOAD = {
    "gender": "M",
    "calendar": "solar",
    "birth_date": "1990-05-20",
    "birth_time": "10:30",
    "birth_place": "北京市",
}


def test_predict_within_2s():
    client = TestClient(app)
    start = time.perf_counter()
    resp = client.post("/api/charts/predict", json=PAYLOAD)
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200
    assert elapsed < 2.0, f"predict took {elapsed:.2f}s"
