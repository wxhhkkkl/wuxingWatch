"""T018/T053 — POST /api/charts/predict and /api/charts/image contracts."""


def test_predict_solar(client):
    resp = client.post(
        "/api/charts/predict",
        json={
            "name": "张三",
            "gender": "M",
            "calendar": "solar",
            "birth_date": "1990-05-20",
            "birth_time": "10:30",
            "birth_place": "北京市",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pillars"]["year"]["ganzhi"] == "庚午"
    assert data["day_master"] == "乙"
    assert data["missing_parts"] == []


def test_predict_lunar(client):
    resp = client.post(
        "/api/charts/predict",
        json={
            "gender": "F",
            "calendar": "lunar",
            "birth_date": "1990-04-26",
            "birth_time": "12:00",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["lunar_birth"]
    assert data["solar_birth"].startswith("1990-05-20")  # 农历 1990-04-26 = 公历 1990-05-20


def test_predict_shichen_input(client):
    resp = client.post(
        "/api/charts/predict",
        json={"gender": "M", "calendar": "solar", "birth_date": "1990-05-20", "birth_time": "午时"},
    )
    assert resp.status_code == 200
    assert resp.json()["pillars"]["time"]["ganzhi"]  # 时辰解析为 11:30 → 有干支


def test_predict_no_hour_marks_missing(client):
    resp = client.post(
        "/api/charts/predict",
        json={"gender": "M", "calendar": "solar", "birth_date": "1990-05-20"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pillars"]["time"] is None
    assert data["missing_parts"] == ["hour_pillar", "ming_gong", "shen_gong"]


def test_predict_invalid_date(client):
    resp = client.post(
        "/api/charts/predict",
        json={"gender": "M", "calendar": "solar", "birth_date": "1990-13-40"},
    )
    assert resp.status_code == 422


def test_image_returns_png(client):
    resp = client.post(
        "/api/charts/image",
        json={
            "gender": "M",
            "calendar": "solar",
            "birth_date": "1990-05-20",
            "birth_time": "10:30",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_image_privacy_header_when_name(client):
    resp = client.post(
        "/api/charts/image",
        json={
            "name": "张三",
            "gender": "M",
            "calendar": "solar",
            "birth_date": "1990-05-20",
            "birth_time": "10:30",
        },
    )
    assert resp.headers.get("x-privacy-notice") == "image-contains-personal-info"
