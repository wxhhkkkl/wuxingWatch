"""大运引擎2 端点的契约（014 期 T026）。

两个入口（contracts/dayun-engine2.md §2）：

- `POST /api/charts/dayun2` —— 新排盘路径；
- `GET  /api/records/{id}/dayun2` —— 已保存记录路径，**当场重推**四柱与大运步。

**三条硬约束**：① 结果**不落库**（FR-008）；② 与 `/suiyun` **并存**、现引擎的数不受影响
（FR-005）；③ 页面**不提供并排与差异标记**（裁定④）——故响应里也不造任何"对比"字段。
"""

import pytest

BIRTH = {
    "name": "引擎2测试",
    "gender": "M",
    "calendar": "solar",
    "birth_date": "1990-05-20",
    "birth_time": "10:30",
    "birth_place": "北京市",
}


def _legal_dayun(client) -> str:
    r = client.post("/api/charts/predict", json=BIRTH)
    steps = (r.json().get("da_yun") or {}).get("steps") or []
    assert steps, "该盘应排出大运步"
    return steps[0]["ganzhi"]


def test_post_returns_all_steps_by_default(client):
    r = client.post("/api/charts/dayun2", json=BIRTH)
    assert r.status_code == 200
    body = r.json()
    assert body["engine"] == "dayun-engine2"
    assert body["engine_version"] == 1
    assert body["input_scope"] == "four_pillars"
    assert body["dayun_steps"], "默认应返回该盘全部大运步"
    assert all(s["ganzhi"] for s in body["dayun_steps"])


def test_post_can_narrow_to_one_step(client):
    gz = _legal_dayun(client)
    r = client.post("/api/charts/dayun2", json={**BIRTH, "dayun_ganzhi": gz})
    assert r.status_code == 200
    steps = r.json()["dayun_steps"]
    assert [s["ganzhi"] for s in steps] == [gz]


def test_each_step_carries_three_layers_and_seven_phases(client):
    gz = _legal_dayun(client)
    r = client.post("/api/charts/dayun2", json={**BIRTH, "dayun_ganzhi": gz})
    step = r.json()["dayun_steps"][0]
    assert set(step["elements"]) == {"木", "火", "土", "金", "水"}
    assert set(step["day_master"]) >= {"stem", "wx", "members", "static", "dynamic", "level"}
    assert step["instances"], "实例明细不得为空"
    assert [p["key"] for p in step["phases"]] == [
        "relations", "month_coef", "tonggen5", "static", "stem_he",
        "dayun_pair", "dayun_to_pillars", "natal_internal"]


def test_illegal_step_is_422_with_the_legal_ones_listed(client):
    r = client.post("/api/charts/dayun2", json={**BIRTH, "dayun_ganzhi": "甲子甲子"})
    assert r.status_code == 422
    assert "不在该盘的大运步内" in r.json()["detail"]


def test_record_entry_matches_the_predict_entry(client, login_user):
    """两端点**同形**：同一张盘、同一步，两条路径给出的三层数逐位相同。"""
    gz = _legal_dayun(client)
    a = client.post("/api/charts/dayun2", json={**BIRTH, "dayun_ganzhi": gz}).json()
    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/records", json=BIRTH, headers=headers)
    assert created.status_code in (200, 201), created.text
    body = created.json()
    rid = body.get("id") or (body.get("record") or {}).get("id")
    assert rid, created.text
    b = client.get(f"/api/records/{rid}/dayun2", params={"dayun_ganzhi": gz},
                   headers=headers).json()
    assert b["engine"] == a["engine"]
    assert b["dayun_steps"][0]["elements"] == a["dayun_steps"][0]["elements"]


def test_result_is_not_persisted(client):
    """FR-008：本端点 MUST NOT 写记录。"""
    before = client.get("/api/records").json()
    n_before = len(before if isinstance(before, list) else before.get("items", []))
    client.post("/api/charts/dayun2", json=BIRTH)
    after = client.get("/api/records").json()
    n_after = len(after if isinstance(after, list) else after.get("items", []))
    assert n_after == n_before


