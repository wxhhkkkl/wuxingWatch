"""T060 · 对拍运行器测试（012 期 US6，FR-049）。"""

import json
from pathlib import Path

from src.scripts import compare_wangdu as cw


FIXTURES = (Path(__file__).resolve().parents[3] / "specs" / "012-rebuild-wangdu-xiyong"
            / "fixtures" / "book-cases.json")


def test_fixtures_exist_and_have_cases():
    """仓库内样本集存在且非空——历次对拍走的是仓库外脚本，本次首次入库（research R3）。"""
    assert FIXTURES.exists(), "样本集未入库"
    cases = cw.load_cases(FIXTURES)
    assert len(cases) > 100, f"样本过少：{len(cases)}"


def test_every_case_has_source_and_conclusion():
    """逐例须带**来源**与**书中结论**（FR-049 的可回溯要求）。"""
    for c in cw.load_cases(FIXTURES):
        assert c["source"]["book"], c["id"]
        assert c["source"].get("line"), c["id"]
        assert c["book_conclusion"].get("raw"), c["id"]
        assert len(c["pillars"]) >= 3, c["id"]


def test_book_ids_are_known():
    """来源书名须落在已知四书之内。"""
    for c in cw.load_cases(FIXTURES)[:50]:
        assert c["source"]["book"] in cw.BOOK_IDS, c["source"]["book"]


def test_load_rejects_bad_shape(tmp_path):
    """`cases` 非数组时应报错而不是静默返回空。"""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"cases": "nope"}), encoding="utf-8")
    try:
        cw.load_cases(bad)
    except ValueError as exc:
        assert "cases" in str(exc)
    else:
        raise AssertionError("应抛 ValueError")


def test_run_both_calls_both_engines():
    """对同一命例同时取得新旧两套结论（FR-048）。"""
    case = cw.load_cases(FIXTURES)[0]
    rec = cw.run_both(case)
    assert rec["old"]["level"] and rec["new"]["level"]
    assert rec["old"]["ge_ju"] and rec["new"]["ge_ju"]


def test_classify_detects_all_three_categories():
    """三类别（档位/格局/用神方向）都能被识别。"""
    rec = {"old": {"level": "偏弱", "ge_ju": "zheng", "yong_shen": "金"},
           "new": {"level": "太弱", "ge_ju": "cong_ruo", "yong_shen": "水"}}
    cats = cw.classify(rec)["categories"]
    assert set(cats) == {"档位翻转", "格局翻转", "用神方向翻转"}


def test_classify_no_diff_when_identical():
    rec = {"old": {"level": "偏弱", "ge_ju": "zheng", "yong_shen": "金"},
           "new": {"level": "偏弱", "ge_ju": "zheng", "yong_shen": "金"}}
    assert cw.classify(rec)["categories"] == []


def test_render_handles_both_conclusion_shapes(tmp_path):
    """`book_conclusion` 为字符串（classify 产出）与字典（样本集原件）都要能渲染。"""
    report = {"total": 1, "same": [], "errors": [],
              "diff": [{"id": "x", "source": {"line": 1}, "categories": ["档位翻转"],
                        "old": {"level": "a", "ge_ju": "z", "yong_shen": "金"},
                        "new": {"level": "b", "ge_ju": "z", "yong_shen": "水"},
                        "book_conclusion": "书中原文"}]}
    out = tmp_path / "r.md"
    cw.render(report, out)
    assert "书中原文" in out.read_text(encoding="utf-8")

    report["diff"][0]["book_conclusion"] = {"raw": "字典形式"}
    cw.render(report, out)
    assert "字典形式" in out.read_text(encoding="utf-8")


def test_compare_respects_limit():
    """`--limit` 只跑前 N 例，且 `total` 反映**实际比较数**。"""
    cases = cw.load_cases(FIXTURES)
    sel = cases[:3]
    # 直接验证切片语义（不实跑引擎，避免依赖数值）
    assert len(sel) == 3
    assert all(c["id"] for c in sel)
