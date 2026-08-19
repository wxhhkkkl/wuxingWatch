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


CTX = {"day_ganzhi": "庚辰", "year_ganzhi": "丁卯", "month_zhi": "巳"}


def test_liushi_month_level(client):
    resp = client.post(
        "/api/charts/liushi",
        json={"level": "month", "year": 2026, "context": CTX},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["year_ganzhi"] == "丙午"
    assert len(data["months"]) == 12
    assert data["months"][0]["ganzhi"] == "庚寅"
    assert data["months"][0]["start"] == "2026-02-04T04:02:08"
    assert data["months"][11]["ganzhi"] == "辛丑"


def test_liushi_day_level(client):
    resp = client.post(
        "/api/charts/liushi",
        json={"level": "day", "year": 2026, "month_branch": "寅", "context": CTX},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["month_ganzhi"] == "庚寅"
    assert len(data["days"]) == 29
    assert data["days"][0]["date"] == "2026-02-04"
    assert data["days"][0]["ganzhi"] == "己酉"
    assert len(data["days"][0]["hours"]) == 12


def test_liushi_hour_level(client):
    resp = client.post(
        "/api/charts/liushi",
        json={
            "level": "hour",
            "year": 2026,
            "month_branch": "寅",
            "date": "2026-02-04",
            "context": CTX,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["day_ganzhi"] == "己酉"
    assert len(data["hours"]) == 12
    assert data["hours"][0]["ganzhi"] == "甲子"
    assert "na_yin" in data["hours"][0]["detail"]


def test_liushi_day_requires_month_branch(client):
    resp = client.post(
        "/api/charts/liushi",
        json={"level": "day", "year": 2026, "context": CTX},
    )
    assert resp.status_code == 422


def test_liushi_hour_requires_date(client):
    resp = client.post(
        "/api/charts/liushi",
        json={"level": "hour", "year": 2026, "month_branch": "寅", "context": CTX},
    )
    assert resp.status_code == 422


def test_liushi_invalid_branch(client):
    resp = client.post(
        "/api/charts/liushi",
        json={"level": "day", "year": 2026, "month_branch": "猫", "context": CTX},
    )
    assert resp.status_code == 422


def test_liushi_hour_date_out_of_month(client):
    resp = client.post(
        "/api/charts/liushi",
        json={
            "level": "hour",
            "year": 2026,
            "month_branch": "寅",
            "date": "2026-03-10",
            "context": CTX,
        },
    )
    assert resp.status_code == 422


def test_predict_xiyong_wangdu_contract(client):
    """T014 — xi_yong 新契约（008 旺度法）：双用神结论 + strength 新形状 + 步骤顺序 + 大运修正对齐。"""
    resp = client.post(
        "/api/charts/predict",
        json={"gender": "M", "calendar": "solar", "birth_date": "1990-05-20", "birth_time": "10:30"},
    )
    assert resp.status_code == 200
    xi = resp.json()["xi_yong"]
    c = xi["conclusion"]
    assert c["yong_shen"] in ("木", "火", "土", "金", "水")
    assert "tiaohou_yong_shen" in c and "element" in c["tiaohou_yong_shen"]
    assert "basis" in c and "yong_shen" in c["basis"] and "tiaohou" in c["basis"]
    s = xi["strength"]
    assert s["method"] == "sizhu-jingsui"
    assert set(s["static_scores"]) == {"木", "火", "土", "金", "水"}
    assert set(s["final_scores"]) == {"木", "火", "土", "金", "水"}
    assert all(v >= 0 for v in s["final_scores"].values())
    assert s["ge_ju"]["type"] in ("zheng", "cong_ruo", "cong_qiang", "cong_yin", "cong_sha", "cong_cai", "hua")
    assert [st["key"] for st in s["steps"]] == [
        "static", "shengke", "zhichong", "final", "geju", "dayun", "yongshen"]
    da_yun_gz = [d["ganzhi"] for d in resp.json()["da_yun"]["steps"]]
    assert [a["ganzhi"] for a in s["dayun_adjustments"]] == da_yun_gz
