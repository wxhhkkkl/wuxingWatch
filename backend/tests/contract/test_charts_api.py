"""T018/T053 — POST /api/charts/predict and /api/charts/image contracts."""

import json
from pathlib import Path



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


def test_predict_wandu_contract(client):
    """原局旺度契约：`wan_du` 直接挂在排盘结果上，只含旺度相关字段。"""
    resp = client.post(
        "/api/charts/predict",
        json={"gender": "M", "calendar": "solar", "birth_date": "1990-05-20", "birth_time": "10:30"},
    )
    assert resp.status_code == 200
    wd = resp.json()["wan_du"]
    assert wd["engine"] == "wangdu-v2"
    assert wd["contract_version"] == 2
    assert set(wd["final_scores"]) == {"木", "火", "土", "金", "水"}
    assert all(v >= 0 for v in wd["final_scores"].values())
    assert wd["input_scope"] in ("four_pillars", "three_pillars")
    for k in ("ge_ju", "yong_shen", "layers", "dayun", "xi_yong"):
        assert k not in wd, k


# ---------------------------------------------------------------
# T046 —— **既有记录打开路径**的原局零回归（013 期；FR-023 / SC-003）
# ---------------------------------------------------------------

BOOK_CHART = "己酉 乙亥 辛丑 壬辰"          # 基准 fixture 里的一例（书例）
BASELINE = Path(__file__).resolve().parents[1] / "fixtures" / "yuanju_baseline.json"

# 原局部分里**承诺一字不变**的字段（FR-023）。`dayun[]` 与调候/层次的岁运重判
# 不在其中——那属岁运结论、允许变（FR-022a）。
YUANJU_KEYS = ("level", "static_scores", "final_scores", "degrees", "relations")


def _sizhu_payload(pz: str) -> dict:
    y, m, d, t = pz.split()
    return {
        "gender": "M", "calendar": "sizhu",
        "birth_pillars": {"year": y, "month": m, "day": d, "time": t},
        "person_name": "旧记录",
    }


def test_existing_record_keeps_its_yuanju_part(client, login_user, monkeypatch):
    """T046 —— 走**记录详情端点**读一条既有记录，其原局部分与保存时**逐项一致**。

    与 `tests/unit/test_v2_yuanju_zero_regression.py` 的分工：那是**引擎层**的 667 盘逐项
    比对，这是**端点层**的——经过「落库 → 读取 →（版本不符则）重算 → 回写 → 返回」这条链
    之后原局部分仍须一字不差。链上任何一处（序列化、重算、剥壳）出问题都会在这里现形，
    而引擎层的比对看不到这些。
    """
    token = login_user("13900000401")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/records", json=_sizhu_payload(BOOK_CHART), headers=headers)
    assert created.status_code == 201, created.text
    rid = created.json()["id"]

    def _strength() -> dict:
        resp = client.get(f"/api/records/{rid}", headers=headers)
        assert resp.status_code == 200, resp.text
        return resp.json()["chart_result"]["wan_du"]

    saved = _strength()
    assert saved["engine"] == "wangdu-v2"

    # 模拟「改动前落库」：让版本号对不上，逼 `_load_result` 走**重算并回写**那条路。
    # 正控制：数一数 `chart_service.compute` 真的被调了几次——否则「重算后仍一致」
    # 可能只是**根本没重算**（那就测了个寂寞）。
    from services import chart_service

    calls: list[int] = []
    real_compute = chart_service.compute
    monkeypatch.setattr("api.routers.records.chart_service.compute",
                        lambda payload: (calls.append(1), real_compute(payload))[1])
    monkeypatch.setattr("api.routers.records.engine_version", lambda: "stale-for-test")
    reopened = _strength()
    assert calls, "版本不符却没有重算——本条没有走到要测的那条路径"

    for k in YUANJU_KEYS:
        assert reopened[k] == saved[k], \
            "记录打开路径改变了原局部分的 `%s`（FR-023 / SC-003）" % k

    # 且与**改动前**留下的基准逐项相同（SC-003）
    base = json.loads(BASELINE.read_text(encoding="utf-8"))["cases"][BOOK_CHART]
    assert reopened["level"] == base["level"]
    assert {k: round(v, 6) for k, v in reopened["final_scores"].items()} == base["final"]
    assert {k: round(v, 6) for k, v in reopened["static_scores"].items()} == base["static"]
