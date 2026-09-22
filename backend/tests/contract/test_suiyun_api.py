"""岁运推导端点的契约（013 期 T031；FR-021a / FR-024 / FR-026 / SC-002 / SC-008）。

两个入口（FR-021a）：

- `POST /api/charts/suiyun` —— 新排盘路径（出生信息同 `BirthInput`）；
- `GET  /api/records/{id}/suiyun` —— 已保存记录路径，**当场重推**大运与流年（不读记录里
  可能存过的岁运结论）。

响应形状见 [contracts/suiyun-v2.md](../../../specs/013-dayun-liunian-judgment/contracts/suiyun-v2.md) §2。
**两条硬约束**：① 结论**不落库**（FR-026）；② 响应里**不得出现吉凶字段**（FR-016a）。
"""

import pytest

BIRTH = {
    "name": "岁运测试",
    "gender": "M",
    "calendar": "solar",
    "birth_date": "1990-05-20",
    "birth_time": "10:30",
    "birth_place": "北京市",
}


def _legal_dayun(client) -> str:
    """取该盘第一步大运的干支——避免把「合法步」写死在测试里。"""
    r = client.post("/api/charts/predict", json=BIRTH)
    steps = (r.json().get("da_yun") or {}).get("steps") or []
    assert steps, "该盘应排出大运步"
    return steps[0]["ganzhi"]


def _forbidden_verdict_fields(obj) -> list[str]:
    """递归找吉凶类字段名。"""
    bad: list[str] = []
    # 注：**不列 `verdict`** —— `layers.verdict` 是**格局层次**（贵气高低）的评定，
    # 不是吉凶结论，属契约内的正常字段（同 `tests/unit/test_v2_suiyun_pairs.py`）。
    KEYS = ("jixiong", "吉凶", "lucky", "unlucky", "score_ji", "score_xiong")
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in KEYS:
                bad.append(k)
            bad += _forbidden_verdict_fields(v)
    elif isinstance(obj, list):
        for v in obj:
            bad += _forbidden_verdict_fields(v)
    return bad


# ---------------------------------------------------------------
# 阶段 2
# ---------------------------------------------------------------

def test_suiyun_stage_two_without_liunian_year(client):
    """只给 `dayun_ganzhi` → **阶段 2**，`pairs` 为 null（契约 §2 R-1）。"""
    dy = _legal_dayun(client)
    r = client.post("/api/charts/suiyun", json={**BIRTH, "dayun_ganzhi": dy})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["stage"] == 2
    assert d["dayun"]["source"] == "dayun" and d["dayun"]["ganzhi"] == dy
    assert d["liunian"] is None and d["pairs"] is None
    assert d["dayun"]["tiaohou"] is not None, "阶段 2 须含调候（FR-021b）"
    assert d["dayun"]["layers"], "阶段 2 须含格局层次（FR-021b）"


def test_suiyun_stage_three_with_liunian_year(client):
    """给 `liunian_year` → **阶段 3**，并返回 7 类 `pairs`（契约 §2 R-6/R-7）。"""
    dy = _legal_dayun(client)
    r = client.post("/api/charts/suiyun",
                    json={**BIRTH, "dayun_ganzhi": dy, "liunian_year": 2024})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["stage"] == 3
    assert d["liunian"]["source"] == "liunian"
    assert d["liunian"]["liunian"], "阶段 3 须带上该流年干支"
    pairs = d["pairs"]
    assert len(pairs) == 7, "须覆盖 7 类同名判断"
    for p in pairs:
        assert p["dayun"]["source"] == "dayun" and p["liunian"]["source"] == "liunian"
        assert p["dayun"]["value"] is not None and p["liunian"]["value"] is not None, \
            "每对**两侧都必须在**（FR-016c）"


# ---------------------------------------------------------------
# 命盘快照里的岁运两列（013 补遗；FR-027）
# ---------------------------------------------------------------

def _chart_keys(step: dict) -> set[frozenset]:
    """该阶段**所有**快照图（段末 + 逐实例）的列 key 集合。"""
    return {frozenset(p["key"] for p in s["chart"]["pillars"])
            for s in step["steps"]} | {
        frozenset(p["key"] for p in cp["chart"]["pillars"])
        for s in step["steps"] for cp in (s.get("charts") or [])}


def test_suiyun_charts_carry_the_two_extra_columns(client):
    """两页的命盘要比原局页多出四个字 → 岁运端点的快照图**含大运/流年列**（FR-027）。

    阶段 2 只有大运（5 列，且**不得**出现流年列——那一列没有对应的判定）；
    阶段 3 两列俱在（6 列）。列在**尾部追加**、由前端重排到最左（见
    `tests/unit/test_v2_steps_suiyun_columns.py` 的口径说明）。
    """
    dy = _legal_dayun(client)
    natal = {"year", "month", "day", "time"}

    r2 = client.post("/api/charts/suiyun", json={**BIRTH, "dayun_ganzhi": dy})
    assert r2.status_code == 200, r2.text
    for keys in _chart_keys(r2.json()["dayun"]):
        assert keys == natal | {"_dayun"}, keys

    r3 = client.post("/api/charts/suiyun",
                     json={**BIRTH, "dayun_ganzhi": dy, "liunian_year": 2024})
    assert r3.status_code == 200, r3.text
    for keys in _chart_keys(r3.json()["liunian"]):
        assert keys == natal | {"_dayun", "_liunian"}, keys


# ---------------------------------------------------------------
# 硬约束
# ---------------------------------------------------------------

def test_suiyun_response_has_no_verdict(client):
    """**引擎不合成吉凶**（FR-016a）——响应里不得出现吉凶字段。"""
    dy = _legal_dayun(client)
    d = client.post("/api/charts/suiyun",
                    json={**BIRTH, "dayun_ganzhi": dy, "liunian_year": 2024}).json()
    assert _forbidden_verdict_fields(d) == []


def test_illegal_dayun_ganzhi_is_rejected(client):
    """选中的大运不在该盘的大运步内 → 422（不是静默算一个别的步）。"""
    r = client.post("/api/charts/suiyun", json={**BIRTH, "dayun_ganzhi": "辛丑"})
    assert r.status_code == 422
    assert "大运" in r.json()["detail"]


def test_suiyun_does_not_touch_records(client, login_user):
    """**结论不落库**（FR-026）——调岁运端点前后，记录内容不得变化。"""
    token = login_user("13900000313")
    h = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/records", json=BIRTH, headers=h)
    assert created.status_code == 201, created.text
    rid = created.json()["id"]

    before = client.get(f"/api/records/{rid}", headers=h).json()
    client.post("/api/charts/suiyun",
                json={**BIRTH, "dayun_ganzhi": _legal_dayun(client),
                      "liunian_year": 2024})
    after = client.get(f"/api/records/{rid}", headers=h).json()
    assert before == after, "岁运推导不得写回记录"


# ---------------------------------------------------------------
# 记录路径：当场重推（FR-021a）
# ---------------------------------------------------------------

def test_record_suiyun_recomputes_from_the_record(client, login_user):
    """从记录进岁运推导——按记录的输入**当场重推**，结论与直接排盘一致。"""
    token = login_user("13900000314")
    h = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/records", json=BIRTH, headers=h)
    rid = created.json()["id"]
    dy = _legal_dayun(client)

    r = client.get(f"/api/records/{rid}/suiyun",
                   params={"dayun_ganzhi": dy, "liunian_year": 2024}, headers=h)
    assert r.status_code == 200, r.text
    d = r.json()
    direct = client.post("/api/charts/suiyun",
                         json={**BIRTH, "dayun_ganzhi": dy, "liunian_year": 2024}).json()
    assert d["stage"] == direct["stage"] == 3
    assert d["dayun"]["ganzhi"] == direct["dayun"]["ganzhi"]
    assert d["liunian"]["scores_after"] == direct["liunian"]["scores_after"], \
        "从记录进入与直接排盘应给出同口径的结论（FR-021a）"
    assert len(d["pairs"]) == 7


def test_record_suiyun_requires_ownership(client, login_user):
    """记录路径须鉴权——拿不到别人的记录。"""
    owner = login_user("13900000315")
    other = login_user("13900000316")
    rid = client.post("/api/records", json=BIRTH,
                      headers={"Authorization": f"Bearer {owner}"}).json()["id"]
    r = client.get(f"/api/records/{rid}/suiyun",
                   params={"dayun_ganzhi": "甲子"},
                   headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 404
