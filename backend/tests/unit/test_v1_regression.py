"""T009 · 旧引擎零回归锁（012 期 FR-046 / SC-003）。

**目的**：012 期新建 v2 引擎，但 `wangdu.py` / `xiyong.py` 必须**一行不改**且对同一
输入输出**逐位一致**（spec FR-046、SC-003）。本测试把一批固定命例的旧引擎结论
快照硬编码在此；任何对旧引擎的无意改动都会让本测试变红。

**快照生成时间**：2026-09-10，012 期动工前（旧引擎处于 011 期 b3ade26 状态）。
**快照内容**：level / ge_ju.type / static_scores / final_scores / yong_shen /
xi_shen / ji_shen / steps 键序列。

> 若因**有意**变更旧引擎导致本测试失败，说明违反了 FR-046——应先停止并确认，
> 而不是更新快照。
"""

import json

from services.bazi import wangdu
from services.bazi.constants import GAN_WUXING, ZHI_WUXING

# 基准快照（012 动工前，旧引擎 b3ade26）
FINGERPRINT = json.loads(r"""{
  "zheng_strong": {
    "level": "偏旺",
    "ge_ju": "zheng",
    "static_scores": {
      "木": 2.1,
      "火": 13.5,
      "土": 8.0,
      "金": 1.62,
      "水": 0.0
    },
    "final_scores": {
      "木": 2.1,
      "火": 13.08,
      "土": 8.4,
      "金": 1.12,
      "水": 0.0
    },
    "yong_shen": "土",
    "xi_shen": [
      "水",
      "金"
    ],
    "ji_shen": [
      "木",
      "火"
    ],
    "steps_keys": [
      "month_hua",
      "month_state",
      "branch_rel",
      "branch_root",
      "stem_hua",
      "base_score",
      "branch_effects",
      "tonggen",
      "month_coef",
      "stem_shengke",
      "total",
      "geju",
      "dayun",
      "yongshen"
    ]
  },
  "zheng_weak": {
    "level": "偏弱",
    "ge_ju": "zheng",
    "static_scores": {
      "木": 0.0,
      "火": 5.6,
      "土": 7.2,
      "金": 14.0,
      "水": 6.0
    },
    "final_scores": {
      "木": 0.0,
      "火": 5.6,
      "土": 6.72,
      "金": 15.38,
      "水": 6.0
    },
    "yong_shen": "土",
    "xi_shen": [
      "火"
    ],
    "ji_shen": [
      "木",
      "金",
      "水"
    ],
    "steps_keys": [
      "month_hua",
      "month_state",
      "branch_rel",
      "branch_root",
      "stem_hua",
      "base_score",
      "branch_effects",
      "tonggen",
      "month_coef",
      "stem_shengke",
      "total",
      "geju",
      "dayun",
      "yongshen"
    ]
  },
  "cong_qiang": {
    "level": "旺极",
    "ge_ju": "zheng",
    "static_scores": {
      "木": 0.0,
      "火": 0.0,
      "土": 42.0,
      "金": 0.0,
      "水": 0.5
    },
    "final_scores": {
      "木": 0.0,
      "火": 0.0,
      "土": 41.8,
      "金": 0.0,
      "水": 0.0
    },
    "yong_shen": "水",
    "xi_shen": [
      "木",
      "金"
    ],
    "ji_shen": [
      "火",
      "土"
    ],
    "steps_keys": [
      "month_hua",
      "month_state",
      "branch_rel",
      "branch_root",
      "stem_hua",
      "base_score",
      "branch_effects",
      "tonggen",
      "month_coef",
      "stem_shengke",
      "total",
      "geju",
      "dayun",
      "yongshen"
    ]
  },
  "cong_ruo": {
    "level": "太弱",
    "ge_ju": "zheng",
    "static_scores": {
      "木": 56.0,
      "火": 3.0,
      "土": 0.5,
      "金": 0.0,
      "水": 1.6
    },
    "final_scores": {
      "木": 55.8,
      "火": 3.0,
      "土": 0.0,
      "金": 0.0,
      "水": 1.6
    },
    "yong_shen": "金",
    "xi_shen": [
      "水"
    ],
    "ji_shen": [
      "土",
      "木",
      "火"
    ],
    "steps_keys": [
      "month_hua",
      "month_state",
      "branch_rel",
      "branch_root",
      "stem_hua",
      "base_score",
      "branch_effects",
      "tonggen",
      "month_coef",
      "stem_shengke",
      "total",
      "geju",
      "dayun",
      "yongshen"
    ]
  },
  "hua_ge": {
    "level": "太弱",
    "ge_ju": "hua",
    "static_scores": {
      "木": 2.1,
      "火": 12.8,
      "土": 18.0,
      "金": 0.5,
      "水": 3.0
    },
    "final_scores": {
      "木": 2.1,
      "火": 12.8,
      "土": 17.8,
      "金": 0.5,
      "水": 2.5
    },
    "yong_shen": "土",
    "xi_shen": [
      "火"
    ],
    "ji_shen": [
      "木"
    ],
    "steps_keys": [
      "month_hua",
      "month_state",
      "branch_rel",
      "branch_root",
      "stem_hua",
      "base_score",
      "branch_effects",
      "tonggen",
      "month_coef",
      "stem_shengke",
      "total",
      "geju",
      "dayun",
      "yongshen"
    ]
  },
  "relation_rich": {
    "level": "偏弱",
    "ge_ju": "zheng",
    "static_scores": {
      "木": 0.0,
      "火": 1.6,
      "土": 26.0,
      "金": 7.5,
      "水": 1.5
    },
    "final_scores": {
      "木": 0.0,
      "火": 1.6,
      "土": 25.28,
      "金": 8.1,
      "水": 1.5
    },
    "yong_shen": "金",
    "xi_shen": [
      "土"
    ],
    "ji_shen": [
      "火",
      "水",
      "木"
    ],
    "steps_keys": [
      "month_hua",
      "month_state",
      "branch_rel",
      "branch_root",
      "stem_hua",
      "base_score",
      "branch_effects",
      "tonggen",
      "month_coef",
      "stem_shengke",
      "total",
      "geju",
      "dayun",
      "yongshen"
    ]
  },
  "three_pillar": {
    "level": "太弱",
    "ge_ju": "zheng",
    "static_scores": {
      "木": 0.7,
      "火": 10.5,
      "土": 14.0,
      "金": 2.5,
      "水": 0.5
    },
    "final_scores": {
      "木": 0.7,
      "火": 10.2,
      "土": 14.0,
      "金": 2.25,
      "水": 0.5
    },
    "yong_shen": "金",
    "xi_shen": [
      "土"
    ],
    "ji_shen": [
      "火",
      "水",
      "木"
    ],
    "steps_keys": [
      "month_hua",
      "month_state",
      "branch_rel",
      "branch_root",
      "stem_hua",
      "base_score",
      "branch_effects",
      "tonggen",
      "month_coef",
      "stem_shengke",
      "total",
      "geju",
      "dayun",
      "yongshen"
    ]
  }
}""")

CASES = [
    ("zheng_strong", "辛酉", "戊戌", "丁卯", "庚戌", "丁"),
    ("zheng_weak", "戊申", "庚申", "戊午", "戊午", "戊"),
    ("cong_qiang", "己丑", "甲戌", "戊戌", "壬戌", "戊"),
    ("cong_ruo", "乙卯", "戊寅", "壬辰", "壬寅", "壬"),
    ("hua_ge", "癸亥", "己未", "甲辰", "辛未", "甲"),
    ("relation_rich", "庚申", "己丑", "庚戌", "壬午", "庚"),
    ("three_pillar", "乙丑", "丙戌", "辛巳", None, "辛"),
]


def _p(gz):
    return {"gan": gz[0], "zhi": gz[1],
            "gan_wuxing": GAN_WUXING[gz[0]], "zhi_wuxing": ZHI_WUXING[gz[1]]}


def _chart(year, month, day, time):
    return {"year": _p(year), "month": _p(month), "day": _p(day),
            "time": _p(time) if time else None}


def _actual(name, year, month, day, time, dm):
    r = wangdu.compute_wangdu(_chart(year, month, day, time), dm)
    return {
        "level": r["level"],
        "ge_ju": r["ge_ju"]["type"],
        "static_scores": r["static_scores"],
        "final_scores": r["final_scores"],
        "yong_shen": r["yong_shen"],
        "xi_shen": r["xi_shen"],
        "ji_shen": r["ji_shen"],
        "steps_keys": [s["key"] for s in r["steps"]],
    }


def test_v1_engine_fingerprint_unchanged():
    """旧引擎对固定命例的结论必须与 012 动工前逐位一致（FR-046）。"""
    drifted = {}
    for name, y, m, d, t, dm in CASES:
        got = _actual(name, y, m, d, t, dm)
        want = FINGERPRINT[name]
        if got != want:
            diff = {k: (want.get(k), got.get(k)) for k in set(want) | set(got)
                    if want.get(k) != got.get(k)}
            drifted[name] = diff
    assert not drifted, f"旧引擎输出发生漂移（违反 FR-046）：{json.dumps(drifted, ensure_ascii=False)}"


def test_v1_steps_key_sequence_unchanged():
    """010 期的 14 键序列在旧引擎中保持不变。"""
    want = ["month_hua", "month_state", "branch_rel", "branch_root", "stem_hua",
            "base_score", "branch_effects", "tonggen", "month_coef", "stem_shengke",
            "total", "geju", "dayun", "yongshen"]
    for name, *_ in CASES:
        assert FINGERPRINT[name]["steps_keys"] == want, name


def test_v1_engine_still_callable_for_all_shapes():
    """旧引擎对新旧两类输入形状均可用，且返回键集稳定。"""
    r = wangdu.compute_wangdu(_chart("乙丑", "丙戌", "辛巳", None), "辛")
    for key in ("method", "level", "ge_ju", "static_scores", "final_scores",
                "yong_shen", "xi_shen", "ji_shen", "steps"):
        assert key in r, key
    assert r["method"] == "sizhu-jingsui"
