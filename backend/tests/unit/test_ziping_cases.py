"""015 T017：书例 runner 的一致/分歧/归因输出。"""
from services.bazi.ziping.cases import run_all


def _doc(book_ge="正官配印格"):
    return {"cases": [{
        "id": "zgpy-1",
        "source": {"chapter": "第一章", "section": "第二节", "page": "书 p.11"},
        "pillars": {"year": "己卯", "month": "辛未", "day": "壬寅", "time": "辛亥"},
        "book_ge": book_ge,
    }]}


def test_runner_matches_book_ge():
    out = run_all(_doc())
    row = out["cases"][0]
    assert row["engine_ge"] == "正官配印格"
    assert row["match"] is True
    assert out["summary"]["compared"] == 1
    assert out["summary"]["matched"] == 1


def test_runner_records_mismatch():
    out = run_all(_doc("七煞格"))
    assert out["cases"][0]["match"] is False
    assert out["summary"]["matched"] == 0


def test_runner_without_book_ge_is_not_compared():
    out = run_all(_doc(None))
    assert out["cases"][0]["match"] is None
    assert out["summary"]["compared"] == 0
