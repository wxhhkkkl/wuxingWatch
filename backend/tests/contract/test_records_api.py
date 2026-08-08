"""T043/T047 — records endpoint contracts (save / list / detail / delete, owner-only)."""


def _record_payload(**over):
    payload = {
        "gender": "M",
        "calendar": "solar",
        "birth_date": "1990-05-20",
        "birth_time": "10:30",
        "birth_place": "北京市",
        "person_name": "儿子",
        "relationship": "CHILD",
        "notes": "测试记录",
    }
    payload.update(over)
    return payload


def test_save_requires_auth(client):
    assert client.post("/api/records", json=_record_payload()).status_code == 401


def test_save_list_detail_delete(client, login_user):
    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/records", json=_record_payload(), headers=headers)
    assert resp.status_code == 201
    rid = resp.json()["id"]
    assert resp.json()["relationship"] == "CHILD"
    assert resp.json()["chart_result"]["day_master"]

    listing = client.get("/api/records", headers=headers)
    assert listing.status_code == 200
    assert any(r["id"] == rid for r in listing.json())

    detail = client.get(f"/api/records/{rid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["chart_result"]["pillars"]["year"]["ganzhi"] == "庚午"

    assert client.delete(f"/api/records/{rid}", headers=headers).status_code == 204
    assert client.get(f"/api/records/{rid}", headers=headers).status_code == 404


def test_owner_isolation(client, login_user):
    token_a = login_user("13800138000")
    resp = client.post(
        "/api/records", json=_record_payload(), headers={"Authorization": f"Bearer {token_a}"}
    )
    rid = resp.json()["id"]

    token_b = login_user("13900139000")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    assert client.get(f"/api/records/{rid}", headers=headers_b).status_code == 404
    assert client.delete(f"/api/records/{rid}", headers=headers_b).status_code == 404


def test_relationship_defaults_to_self(client, login_user):
    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    payload = _record_payload()
    payload.pop("relationship")
    resp = client.post("/api/records", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["relationship"] == "SELF"
