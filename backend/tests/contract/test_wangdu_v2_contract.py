"""原局旺度契约测试（012 期 v2；2026-10-28 起只保留旺度）。

要点：

- 预测结果里的原局结论走 `wan_du`（`engine: "wangdu-v2"`），**不再**嵌在 `xi_yong` 下；
- 只含旺度：静态/动态五行合计、十一档等级、实例明细、关系判定与逐步依据；
- **不含**格局、用神、喜忌、调候、岁运推导；
- 排盘字段一字不改；缺时柱时 `degradations` 非空。
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

BASE = {"gender": "M", "calendar": "sizhu",
        "birth_pillars": {"year": "戊申", "month": "庚申", "day": "戊午", "time": "戊午"}}


def _predict(payload: dict) -> dict:
    r = client.post("/api/charts/predict", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_wandu_contract_shape():
    """原局结论须含旺度契约的全部字段。"""
    wd = _predict(BASE)["wan_du"]
    assert wd["engine"] == "wangdu-v2"
    assert wd["contract_version"] == 2
    for k in ("day_master", "day_master_original", "day_master_wuxing",
              "input_scope", "degradations", "relations", "degrees",
              "static_scores", "final_scores", "level", "stem_groups",
              "day_master_group", "benqi_instances", "steps"):
        assert k in wd, k
    for k in ("ge_ju", "yong_shen", "layers", "dayun", "xi_yong"):
        assert k not in wd, k


def test_relations_are_structured():
    """关系裁定须结构化（不再是散文 trace）——命盘图据此消费。"""
    rel = _predict(BASE)["wan_du"]["relations"]
    assert set(rel) == {"established", "rejected"}
    for e in rel["established"]:
        for k in ("tier", "type", "members", "cols"):
            assert k in e, k
        assert 1 <= e["tier"] <= 18, e["tier"]


def test_degrees_contract_fields():
    """`degrees[wx]` 含各阶段字段。"""
    for wx, d in _predict(BASE)["wan_du"]["degrees"].items():
        for k in ("base", "after_relations", "root", "static", "final", "coef", "state"):
            assert k in d, (wx, k)


def test_steps_carry_rulings():
    """依据条目引用口径裁定编号（FR-056）。"""
    steps = _predict(BASE)["wan_du"]["steps"]
    assert steps
    assert any(st.get("rulings") for st in steps), "至少一段应引用裁定编号"


def test_steps_cover_full_derivation():
    """推演链从关系判定到动态旺度，止于定级。"""
    steps = _predict(BASE)["wan_du"]["steps"]
    keys = [st["key"] for st in steps]
    assert keys == ["relations", "effects", "month_coef", "tonggen", "static",
                    "stem_he", "stem_shengke", "total"], keys
    for st in steps:
        assert st["rule"], st["key"]


def test_paipan_fields_unchanged():
    """**排盘字段一字不改**——`records._summarize()` 依赖 `result["pillars"]`。"""
    body = _predict(BASE)
    for k in ("pillars", "lunar_birth", "solar_birth", "true_solar_time",
              "da_yun", "liu_nian", "hidden_stems", "day_master"):
        assert k in body, k
    assert set(body["pillars"]) >= {"year", "month", "day", "time"}


def test_three_pillars_degrades():
    """缺时柱 → `input_scope=three_pillars` 且 `degradations` 非空。"""
    r = client.post("/api/charts/predict",
                    json={"gender": "M", "calendar": "solar", "birth_date": "1990-05-20"})
    assert r.status_code == 200, r.text
    wd = r.json()["wan_du"]
    assert wd["input_scope"] == "three_pillars", "缺 birth_time 应产出三柱结论"
    assert wd["degradations"], "缺时柱须给出降级说明"


def test_wangdu_steps_carry_the_chart_snapshot_over_http():
    """逐段命盘快照须**过 HTTP 传到前端**。"""
    steps = _predict(BASE)["wan_du"]["steps"]
    for st in steps:
        pillars = st["chart"]["pillars"]
        assert [p["key"] for p in pillars] == ["year", "month", "day", "time"], st["key"]
        for p in pillars:
            assert isinstance(p["gan_degree"], (int, float))
            assert p["hidden"], (st["key"], p["key"])
            for h in p["hidden"]:
                assert isinstance(h["degree"], (int, float))
                assert h["change"] in (None, "新增", "归零", "增力", "减力", "变纯")


def test_swap_follows_into_paipan_details():
    """日干被天干五合换字时，排盘 detail 的十神也须按新日主重算。"""
    body = _predict({"gender": "F", "calendar": "sizhu",
                     "birth_pillars": {"year": "辛亥", "month": "癸巳",
                                       "day": "戊戌", "time": "丙辰"}})
    wd = body["wan_du"]
    assert wd["day_master"] == "丙" and wd["day_master_original"] == "戊"
    assert body["pillars"]["month"]["detail"]["gan_shishen"] == "正官"
