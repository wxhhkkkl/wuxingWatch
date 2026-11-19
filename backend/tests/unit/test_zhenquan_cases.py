"""016：100 例《子平真诠》文本判回测。"""
import json
from pathlib import Path

from services.bazi.v2 import wan_du_analysis
from services.bazi.zhenquan import judge_yuanju
from services.bazi.zhenquan.taxonomy import CLASS_GROUP

FIXTURE = (Path(__file__).resolve().parents[3]
           / "specs" / "016-ziping-zhenquan-geju" / "fixtures"
           / "cases-100-text.json")


def _pillars(raw: dict) -> dict:
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in raw.items()}


def test_fixture_has_100_cases():
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert len(doc["cases"]) == 100
    for c in doc["cases"]:
        assert c["text_expected"] in CLASS_GROUP, c["id"]
        assert c["confirmed_expected"] in CLASS_GROUP, c["id"]


def test_100_cases_match_confirmed_expected():
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bad = []
    for c in doc["cases"]:
        p = _pillars(c["pillars"])
        out = judge_yuanju(p, wan_du_analysis(p))
        name = out["main_ge"]["name"]
        if name != c["confirmed_expected"]:
            bad.append((c["id"], c["confirmed_expected"], name,
                        out["main_ge"]["reason"]))
    assert not bad, bad

