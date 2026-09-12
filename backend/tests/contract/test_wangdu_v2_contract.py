"""T077 · v2 结论契约测试（012 期，FR-053 / FR-054）。

契约以 `specs/012-rebuild-wangdu-xiyong/data-model.md` §1 与
`contracts/xiyong-wangdu-v2.md` 为准。要点：

- 预测走 **v2 契约**（`engine: "wangdu-v2"`），字段与旧契约**独立设计**（非超集）；
- **排盘字段一字不改**——`records.py` 的 `_summarize()` 直接读 `result["pillars"]`，
  一旦变动会破坏记录列表摘要；
- 缺时柱时 `degradations` 非空（FR-057）。
"""

import copy

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

BASE = {"gender": "M", "calendar": "sizhu",
        "birth_pillars": {"year": "戊申", "month": "庚申", "day": "戊午", "time": "戊午"}}


def _predict(payload: dict) -> dict:
    r = client.post("/api/charts/predict", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_v2_contract_shape():
    """v2 结论子树须含 data-model §1 的字段。"""
    body = _predict(BASE)
    s = body["xi_yong"]["strength"]
    assert s["engine"] == "wangdu-v2"
    assert s["contract_version"] == 2
    for k in ("day_master", "day_master_wuxing", "input_scope", "degradations",
              "relations", "degrees", "level", "ge_ju", "yong_shen", "steps", "dayun"):
        assert k in s, k


def test_relations_are_structured():
    """关系裁定须结构化（不再是散文 trace）——命盘图据此消费（方案 A）。"""
    s = _predict(BASE)["xi_yong"]["strength"]
    rel = s["relations"]
    assert set(rel) == {"established", "rejected"}
    for e in rel["established"]:
        for k in ("tier", "type", "members", "cols"):
            assert k in e, k
        assert 1 <= e["tier"] <= 18, e["tier"]


def test_degrees_contract_fields():
    """`degrees[wx]` 含 data-model §3 的各阶段字段。"""
    s = _predict(BASE)["xi_yong"]["strength"]
    for wx, d in s["degrees"].items():
        for k in ("base", "after_relations", "root", "static", "final", "coef", "state"):
            assert k in d, (wx, k)


def test_yong_shen_contract_r8_r9():
    """`yong_shen` 满足 R-8（判空时全空）与 R-9（反转须给理由）。"""
    from services.bazi.v2 import xiyong_v2
    s = _predict(BASE)["xi_yong"]["strength"]
    assert xiyong_v2.validate_contract(s["yong_shen"]) == []


def test_steps_carry_rulings():
    """依据条目引用口径裁定编号（FR-056）。"""
    s = _predict(BASE)["xi_yong"]["strength"]
    assert s["steps"]
    assert any(st.get("rulings") for st in s["steps"]), "至少一段应引用裁定编号"


def test_steps_cover_full_derivation():
    """推演链须从**关系判定**一路到**三因素取用**——喜忌结论可逐段追溯（FR-050/SC-004）。"""
    s = _predict(BASE)["xi_yong"]["strength"]
    keys = [st["key"] for st in s["steps"]]
    assert keys == ["relations", "stem_he", "effects", "month_coef", "tonggen", "static",
                    "stem_shengke", "total", "geju", "yongshen"], keys
    # 每一段都必须带规则说明，且取用段要给出结论
    for st in s["steps"]:
        assert st["rule"], st["key"]
    assert "用神" in s["steps"][-1]["result"]


def test_paipan_fields_unchanged():
    """**排盘字段一字不改**——`records._summarize()` 依赖 `result["pillars"]`。"""
    body = _predict(BASE)
    for k in ("pillars", "lunar_birth", "solar_birth", "true_solar_time",
              "da_yun", "liu_nian", "hidden_stems", "day_master"):
        assert k in body, k
    assert set(body["pillars"]) >= {"year", "month", "day", "time"}


def test_three_pillars_degrades():
    """缺时柱 → `input_scope=three_pillars` 且 `degradations` 非空（FR-057）。

    > 缺时柱走的是**公历/农历模式不带 `birth_time`**（接口注释：「缺省表示时辰不详」），
    > **不是** `calendar=sizhu` 少给一个干支——后者会被接口直接拒掉
    > （「请提供 year/month/day/time 四个干支」）。
    """
    r = client.post("/api/charts/predict",
                    json={"gender": "M", "calendar": "solar", "birth_date": "1990-05-20"})
    assert r.status_code == 200, r.text
    s = r.json()["xi_yong"]["strength"]
    assert s["input_scope"] == "three_pillars", "缺 birth_time 应产出三柱结论"
    assert s["degradations"], "缺时柱须给出降级说明"


def test_dayun_steps_present():
    """逐步大运的用神变化随预测返回（FR-042）。"""
    s = _predict(BASE)["xi_yong"]["strength"]
    assert isinstance(s["dayun"], list)


def test_wangdu_steps_carry_the_chart_snapshot_over_http():
    """逐段命盘快照须**过 HTTP 传到前端**（data-model §7a / contracts §2.2c）。

    引擎侧的形状已由 `tests/unit/test_v2_steps.py` 钉住；本条只验它没有被 API 层
    的序列化丢掉，且第 8/9 段不带。
    """
    s = _predict(BASE)["xi_yong"]["strength"]
    for st in s["steps"]:
        if st["key"] in ("geju", "yongshen"):
            assert "chart" not in st, st["key"]
            continue
        pillars = st["chart"]["pillars"]
        assert [p["key"] for p in pillars] == ["year", "month", "day", "time"], st["key"]
        for p in pillars:
            assert isinstance(p["gan_degree"], (int, float))
            assert p["hidden"], (st["key"], p["key"])
            for h in p["hidden"]:
                assert isinstance(h["degree"], (int, float))
                assert h["change"] in (None, "新增", "归零", "增力", "减力", "变纯")


def test_swap_follows_into_paipan_details():
    """日干被天干五合换字时，**排盘 detail 的十神**也须按新日主重算。

    `辛亥 癸巳 戊戌 丙辰`：戊癸化火成功 → 日主戊变丙（火），月干癸对照丙为「正官」；
    若排盘 detail 仍按戊算会是「正财」，页面上就会出现「日主属火、十神按土算」的矛盾。
    """
    body = _predict({"gender": "F", "calendar": "sizhu",
                     "birth_pillars": {"year": "辛亥", "month": "癸巳",
                                       "day": "戊戌", "time": "丙辰"}})
    s = body["xi_yong"]["strength"]
    assert s["day_master"] == "丙" and s["day_master_original"] == "戊"
    assert body["pillars"]["month"]["detail"]["gan_shishen"] == "正官"
    assert body["xi_yong"]["ten_gods"]["month"] == "正官"
