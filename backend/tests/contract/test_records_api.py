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


def test_detail_returns_birth_input(client, login_user):
    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    rid = client.post("/api/records", json=_record_payload(), headers=headers).json()["id"]

    detail = client.get(f"/api/records/{rid}", headers=headers).json()
    bi = detail["birth_input"]
    assert bi["calendar"] == "solar"
    assert bi["birth_date"] == "1990-05-20"
    assert bi["birth_time"] == "10:30"
    assert bi["gender"] == "M"
    assert bi["birth_place"] == "北京市"


def test_update_record_recomputes_chart(client, login_user):
    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/records", json=_record_payload(), headers=headers).json()
    rid = created["id"]

    new_payload = _record_payload(birth_time="23:30")
    resp = client.put(f"/api/records/{rid}", json=new_payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == rid
    assert body["created_at"] == created["created_at"]
    assert body["person_name"] == "儿子"  # 元信息透传保留
    old_time = created["chart_result"]["pillars"]["time"]["ganzhi"]
    new_time = body["chart_result"]["pillars"]["time"]["ganzhi"]
    assert new_time != old_time

    # 更新已持久化，且未产生新记录
    detail = client.get(f"/api/records/{rid}", headers=headers).json()
    assert detail["chart_result"]["pillars"]["time"]["ganzhi"] == new_time
    listing = client.get("/api/records", headers=headers).json()
    assert len([r for r in listing if r["id"] == rid]) == 1


def test_update_requires_auth_and_ownership(client, login_user):
    assert client.put("/api/records/1", json=_record_payload()).status_code == 401

    token_a = login_user("13800138000")
    rid = client.post(
        "/api/records",
        json=_record_payload(),
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()["id"]
    token_b = login_user("13900139000")
    resp = client.put(
        f"/api/records/{rid}",
        json=_record_payload(),
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------
# 记录与**引擎口径版本**绑定（2026-09-16）
#
# 记录里另存 `_engine_version`（引擎核心模块源码哈希）与 `_input`（当时的完整入参）。
# 读取时版本不符就**重算并回写**——否则打开老记录会看到保存那一刻的旧段序/旧口径
# （如「第 2 段 · 天干五合」，而五合现已挪到静态旺度之后）。
# ---------------------------------------------------------------

def _saved(client, headers):
    resp = client.post("/api/records", json=_record_payload(), headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def test_result_carries_no_private_keys(client, login_user):
    """`_engine_version` / `_input` 是**存储专用**，不下发给前端。"""
    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    rid = _saved(client, headers)

    detail = client.get(f"/api/records/{rid}", headers=headers).json()
    assert not [k for k in detail["chart_result"] if k.startswith("_")], \
        detail["chart_result"].keys()
    listed = client.get("/api/records", headers=headers).json()
    assert listed, "列表应有记录"


def test_birth_input_is_stored_in_full(client, login_user):
    """保存时的**完整入参**要能原样取回（旧实现丢 timezone / birth_pillars / precise_shichen）。"""
    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    payload = _record_payload(timezone="Asia/Shanghai", precise_shichen=True)
    rid = client.post("/api/records", json=payload, headers=headers).json()["id"]

    birth_input = client.get(f"/api/records/{rid}", headers=headers).json()["birth_input"]
    assert birth_input["timezone"] == "Asia/Shanghai"
    assert birth_input["precise_shichen"] is True


def test_stale_engine_version_triggers_recompute(client, login_user, db_session=None):
    """把记录里的版本号改成过时的 → 读时**重算**，段序回到当前口径。

    这条锁的就是「打开老记录看到『第 2 段 · 天干五合』」那个问题：只要记录还带着
    `_input`，版本不符就会被重算，界面永远是当前口径。
    """
    import json

    from models.bazi_chart import BaziChart
    from services.bazi.v2 import engine_version

    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    rid = _saved(client, headers)

    # 直接改库：把版本号换成过时的
    from db.session import get_db
    from main import app
    gen = app.dependency_overrides[get_db]()
    db = next(gen)
    try:
        rec = db.get(BaziChart, rid)
        stored = json.loads(rec.chart_result)
        assert stored["_engine_version"] == engine_version()
        assert stored["_input"], "应存了完整入参"
        stored["_engine_version"] = "stale0000000"
        # 把结果也**改坏**——只改版本号的话「不重算」也能过，测试就成了空的。
        # 换掉段序（模拟旧口径：五合曾排第 2 段），重算后应恢复当前段序。
        stored["xi_yong"]["strength"]["steps"] = [
            {"key": "relations", "title": "第 1 段 · 关系判定", "rule": "x", "traces": [],
             "result": ""},
            {"key": "stem_he", "title": "第 2 段 · 天干五合", "rule": "x", "traces": [],
             "result": ""},
        ]
        stored["_marker"] = "STALE"
        rec.chart_result = json.dumps(stored, ensure_ascii=False)
        db.commit()
    finally:
        gen.close()

    detail = client.get(f"/api/records/{rid}", headers=headers).json()
    steps = detail["chart_result"]["xi_yong"]["strength"]["steps"]
    keys = [s["key"] for s in steps]
    assert len(keys) >= 8, f"应已重算（旧的那份只有 2 段）：{keys}"
    assert keys[:6] == ["relations", "effects", "month_coef", "tonggen", "static",
                        "stem_he"], keys
    assert not [s for s in steps if "天干五合" in s["title"] and "第 2 段" in s["title"]],         "不该再有「第 2 段 · 天干五合」（五合现已挪到静态旺度之后）"
    titles = [s["title"] for s in steps]
    assert "第 6 段 · 天干五合（换字 + 合绊减力）" in titles, titles
    # 且已回写为新版本
    gen = app.dependency_overrides[get_db]()
    db = next(gen)
    try:
        rec = db.get(BaziChart, rid)
        assert json.loads(rec.chart_result)["_engine_version"] == engine_version()
    finally:
        gen.close()


def test_legacy_record_without_input_is_served_as_is(client, login_user):
    """老记录（没有 `_input`）不重算，原样返回存的那份——不能因为改口径就打不开。"""
    import json

    from models.bazi_chart import BaziChart
    from db.session import get_db
    from main import app

    token = login_user("13800138000")
    headers = {"Authorization": f"Bearer {token}"}
    rid = _saved(client, headers)

    gen = app.dependency_overrides[get_db]()
    db = next(gen)
    try:
        rec = db.get(BaziChart, rid)
        stored = json.loads(rec.chart_result)
        stored.pop("_input", None)          # 模拟本次改动之前的记录
        stored.pop("_engine_version", None)
        rec.chart_result = json.dumps(stored, ensure_ascii=False)
        db.commit()
    finally:
        gen.close()

    detail = client.get(f"/api/records/{rid}", headers=headers).json()
    assert detail["chart_result"]["xi_yong"]["strength"]["steps"], "仍能正常返回"
