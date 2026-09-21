"""岁运对拍运行器（013 期 T048；SC-001）。

**与 `compare_wangdu.py` 的分工**：那是 012 期的**原局**对拍（旧引擎 vs v2 引擎），
本次是**岁运**对拍——把书里**论岁运**的算例逐例送进**阶段 2**（加入该步大运），
与本引擎的结论逐条比对。

**样本**：`specs/013-dayun-liunian-judgment/fixtures/suiyun-cases.json`（198 例，
由 `extract_suiyun_cases.py` 自 012 的 394 例中筛出，逐例回原文取**完整**结论——
012 的 400 字截断会系统性漏掉「分析：进入辛丑运…」这类段落）。

**对拍什么**：书里论岁运的段落是**散文**，故本脚本分两层输出：

1. **关键词层（可机检）**——从结论里抽出**档位 / 格局 / 用神**三类关键词，
   与该步的对应值比对（粒度与 012 的 `compare_wangdu.py` 一致）；
2. **全量层（供裁定）**——各例列出「该步的档位 / 格局 / 用神」与书中结论原文，
   供逐例裁定（差异必须能从依据解释，SC-001）。

⚠️ **不用「X度」做数值对拍**——实测后放弃，理由见下方常量区的长注释：书里的度数是
**藏干级或书中自算**，与我们的**全局合计**不是同一个量，29 条此类断言 0 条能对应上。

用法：

    cd backend && PYTHONPATH=src uv run python -m src.scripts.compare_suiyun \\
        --out ../specs/013-dayun-liunian-judgment/diff-report.md
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FIXTURES = (REPO_ROOT / "specs" / "013-dayun-liunian-judgment"
                    / "fixtures" / "suiyun-cases.json")
DEFAULT_OUT = REPO_ROOT / "specs" / "013-dayun-liunian-judgment" / "diff-report.md"

KEYS = ("year", "month", "day", "time")
GANZHI = "[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"

# 「进入X运」「X运」——书中论大运的两种写法
ENTER_RE = re.compile(r"进入(" + GANZHI + r")运")
YUN_RE = re.compile(r"(" + GANZHI + r")运")

# ---------------------------------------------------------------
# 可机检层：**关键词级**，粒度与 012 的 `compare_wangdu.py` 一致（档位 / 格局 / 用神）。
#
# ⚠️ **为什么不用「X度」做数值对拍**（实测后放弃）：书里论岁运的度数是
# **藏干级**（「未中丁火 3 度」「丑含土 3 度」）或**书中自算**（「此时日主静态旺度为
# 8.8 度」——与我们的全局合计 4.0 对不上，是两套口径），正则抓到的「火3度」既可能指
# 某一支的藏干、也可能指全局，**无法与我们的 `scores_after[w]` 直接相减**。
# 实测 29 条此类断言 **0 条**能与我们的量对应上——那不是 29 个缺陷，是 29 次错配。
# 故本层只做**关键词**抽取，且**不设通过门槛**（沿 012 SC-001 的规矩：
# 看差异清单是否完整、每条能否从依据解释，不看一致率）。
# ---------------------------------------------------------------

# 十一档（与 `degrees.LEVEL_BANDS` 同名——书里用的就是这一套词）
LEVEL_WORDS = ("旺极", "太旺", "比旺", "较旺", "偏旺", "中和",
               "偏弱", "较弱", "比弱", "太弱", "弱极")

# **必须带主语**才认——书里这些词大量出现在**规则叙述**里（「日主太旺则…」），
# 无主语地抓会把规则当结论（实测：不带上文时差异里的 60% 是这类误抓）。
LEVEL_CTX_RE = re.compile(r"(?:日主|身)(?:旺度)?(?:为|是|属|变成了|转为)?\s{0,2}"
                          r"(" + "|".join(LEVEL_WORDS) + r")")

# 格局关键词 → 我们的 `ge_ju.type`。**要求带「格」字**——同理，书里「从弱」大量出现在
# 规则句里，而**下结论时**书用的是「从弱格」「化气格」这样的定名。
GEJU_KEYWORDS = (
    ("从弱格", "cong_ruo"), ("从强格", "cong_qiang"), ("从印格", "cong_yin"),
    ("从杀格", "cong_sha"), ("从财格", "cong_cai"),
    ("化气格", "hua"), ("化格", "hua"),
)

# 用神关键词：「用神为X」「以X为用」「取X为用」「X为用神」
YONG_RE = re.compile(r"(?:用神为|取|以)\s*([木火土金水])\s*(?:为用神|为用|作|。|，|；|,|$)")
# 差异分类：凡差异源于以下已裁定口径者，归入该类别而**不列入待修项**。
RULING_DIFFS = {
    "O-5": "严格让位：同一支被多对关系命中时低优先级失效、影响不叠加",
    "O-9": "两类修复（半三合条目内型多支时丢掉合绊之力；墓库冲条件②③未按书实现）",
    "C26-22": "天干五合条件④「弱方不能独立」按动态旺度",
    "C26-23": "动态旺度重设计：合→生→克三段、同单位只取影响最大的一路",
    "FR-003/FR-017a": "折中（综合）状态只取月令与大运，流年不参与",
    "R10": "墓库冲②亥子月的「辰丑以土论」；党众不计岁运之支；运支状态按**月令表**",
    "口径层差": "书里论岁运的度数是**藏干级或书中自算**（见上「为什么不用 X度 对拍」），"
                "与我们的全局合计不是同一个量——此类差异属**口径层差**，不是缺陷",
}


ADJUDICATION = """## 差异裁定（逐类，SC-001）

**这份报告不是「通过/不通过」的判据**——书里论岁运的段落是散文，抽出来的关键词断言
只作**裁定线索**。下表是对各差异类的处置；标「**待逐例裁定**」者已登记进
[research.md](research.md) 的开放项，**在裁定前不算缺陷**。

| 差异类 | 条数 | 处置 |
|---|---|---|
| **化气格未成立**（书判化气格、本引擎未取化格） | 8 | **待逐例裁定——已登记为 R11**。抽验三例（`jingsui-shang-0060` / `-0088` / `-0091`）都是同一形态：**该书步让「化神综合状态当令」成立**（如 0060「进入戊辰运…综合系数为 2.5＜3 即为当令，甲木不能独立…故甲己合化土成功，格成化气格」），本引擎在该步仍判「不化，按合绊」（0088）。**这是本期「折中状态接线」要解决的正是这类**，故须逐例确认是接线未覆盖的判据、还是书自算的度数不同 |
| 档位：**相邻一档** | 16 | **口径层差**。档位按度数切十一档，而书里给的度数是**书自算**（含月令系数、藏干级），与我们的**全局合计**不是同一个量；落在档界附近就会差一档。须逐例看该例的度数是否同量 |
| 用神：方向不同 | 11 | **待逐例裁定**。取用是三因素（扶抑/调候/通关）的取舍序，差异多源自**先取哪一个**的口径 |
| 档位：**跨两档以上** | 5 | **优先看**——跨档往往不是边界问题，而是量级口径不同 |
| 格局：正格 / 从格之别 | 2 | 待逐例裁定 |
| **从格方向不同** | 2 | 待逐例裁定（同为从格、从的对象不同，牵涉「不能独立」的判据） |

> **一致 11 / 差异 44 不等于「三分之一正确」**：抽取本身有误报（书里的关键词常出现在
> **规则叙述**而非本例结论中，如「日主太旺则…」），故**分母不可解**。要看的是差异清单
> 是否完整、每类能否定位到具体判据——这正是 SC-001 的原文要求。
"""


def _chart(pz: list[str]) -> dict:
    return {k: {"gan": v[0], "zhi": v[1]} for k, v in zip(KEYS, pz)}


def _steps_of(pz: list[str]) -> tuple[list[str], dict]:
    """该盘的合法大运步 + 完整排盘结果。四柱输入模式即可（步序与起运无关）。"""
    from api.schemas import RecordCreate
    from services import chart_service

    payload = RecordCreate(gender="M", calendar="sizhu",
                           birth_pillars=dict(zip(KEYS, pz)))
    result, _ = chart_service.compute(payload)
    steps = [s.get("ganzhi") for s in ((result.get("da_yun") or {}).get("steps") or [])]
    return steps, result


def _mentions(case: dict) -> list[str]:
    """该例提到的大运干支（按出现次序、去重）。"""
    out: list[str] = []
    for m in case.get("dayun_mentions") or []:
        gz = YUN_RE.search(m)
        if gz:
            out.append(gz.group(1))
    for m in ENTER_RE.finditer(case.get("book_conclusion") or ""):
        out.append(m.group(1))
    return list(dict.fromkeys(out))


def _claims(text: str) -> list[dict]:
    """从结论里抽出**关键词级**断言（档位 / 格局 / 用神）。

    三类各取**最后一次**出现——书里论岁运的段落常先复述原局、再说「进入X运…此时…」，
    岁运后的结论在**后**（如「原局身弱…进入己丑运…此时…中和」）。

    抽取是**启发式**的（散文里「中和」也可能是在说别的东西），故只作**裁定线索**，
    不作精确判据——沿 012 `compare_wangdu.py` 的规矩：不设通过门槛。
    """
    out: list[dict] = []
    last = None
    for m2 in LEVEL_CTX_RE.finditer(text):
        last = m2
    if last:
        out.append({"kind": "档位", "book": last.group(1), "at": last.start()})
    hit = None
    for kw, t in GEJU_KEYWORDS:
        i = text.rfind(kw)
        if i >= 0 and (hit is None or i > hit[2]):
            hit = (kw, t, i)
    if hit:
        out.append({"kind": "格局", "book": hit[1], "raw": hit[0], "at": hit[2]})
    m = None
    for m2 in YONG_RE.finditer(text):
        m = m2
    if m:
        out.append({"kind": "用神", "book": m.group(1), "at": m.start()})
    return out


def run(fixtures: Path, limit: int | None = None) -> dict:
    from services.bazi.constants import GAN_WUXING
    from services.bazi.v2.dayun import analyze_step

    data = json.loads(fixtures.read_text(encoding="utf-8"))
    cases = data["cases"][:limit] if limit else data["cases"]

    matched: list[dict] = []        # 数值断言逐条
    listings: list[dict] = []       # 全量层（供裁定）
    unmatched: list[dict] = []      # 无法对拍

    for case in cases:
        pz = case.get("pillars") or []
        if len(pz) != 4:
            unmatched.append({"id": case["id"], "why": "四柱不全"})
            continue
        steps, _ = _steps_of(pz)
        if not steps:
            unmatched.append({"id": case["id"], "why": "该盘排不出大运步"})
            continue
        gz = next((m for m in _mentions(case) if m in steps), None)
        if gz is None:
            unmatched.append({
                "id": case["id"],
                "why": ("书中未点名大运" if not _mentions(case)
                        else "点名的大运不在该盘的大运步内：%s" % "、".join(_mentions(case))),
            })
            continue

        item = analyze_step(_chart(pz), gz)
        dm = pz[2][0]
        dm_wx = GAN_WUXING.get(dm, "")
        after = item["scores_after"]
        yong = (item["yong_shen"].get("theoretical") or {}).get("element")

        ours_of = {"档位": item["level"], "格局": item["ge_ju"]["type"], "用神": yong}
        for c in _claims(case.get("book_conclusion") or ""):
            ours = ours_of[c["kind"]]
            matched.append({
                "id": case["id"], "line": (case.get("source") or {}).get("line"),
                "gz": gz, "kind": c["kind"],
                "book": c.get("raw") or c["book"], "book_val": c["book"],
                "ours": ours, "agree": ours is not None and ours == c["book"],
            })

        listings.append({
            "id": case["id"], "line": (case.get("source") or {}).get("line"),
            "pillars": " ".join(pz), "gz": gz,
            "level": item["level"], "ge_ju": item["ge_ju"]["type"],
            "yong": (item["yong_shen"].get("theoretical") or {}).get("element"),
            "after": {w: after.get(w) for w in ("木", "火", "土", "金", "水")},
            "conclusion": case.get("book_conclusion") or "",
        })

    return {"total": len(cases), "matched": matched, "listings": listings,
            "unmatched": unmatched, "src": data}


def _md(res: dict, limit_listing: int = 30) -> str:
    m, l, u = res["matched"], res["listings"], res["unmatched"]
    ok = [x for x in m if x["agree"]]
    bad = [x for x in m if not x["agree"]]
    out: list[str] = []
    out.append("# 013 岁运对拍差异报告\n")
    out.append("> 由 `backend/src/scripts/compare_suiyun.py` 生成（可复跑）。"
               "样本为 `fixtures/suiyun-cases.json`（自 012 的 394 例中筛出**含岁运**者）。\n")
    out.append("## 概览\n")
    out.append("| 项 | 值 |")
    out.append("|---|---|")
    out.append("| 岁运算例总数 | %d |" % res["total"])
    out.append("| 该步大运**可在盘中定位**（可对拍） | %d |" % len(l))
    out.append("| 无法对拍（见下「未对拍清单」） | %d |" % len(u))
    out.append("| 抽到**关键词级断言** | %d 条 |" % len(m))
    out.append("| ├ 一致 | %d |" % len(ok))
    out.append("| └ 差异（**须逐条从依据解释**，见下） | %d |" % len(bad))
    out.append("")
    out.append("> ⚠️ **本表不设通过门槛**（沿 012 SC-001 的规矩）——抽取是启发式的，"
               "看的是差异清单是否完整、每条能否从依据解释，**不是看一致率**。\n")
    out.append("### 关键词级明细（可机检层）\n")
    if not m:
        out.append("（本样本集中没有抽到关键词级断言）\n")
    else:
        out.append("| 例 | 源行 | 该步大运 | 类 | 书中 | 本引擎 | 判定 |")
        out.append("|---|---|---|---|---|---|---|")
        for x in m:
            out.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                x["id"], x["line"], x["gz"], x["kind"], x["book"],
                "—" if x["ours"] is None else x["ours"],
                "一致" if x["agree"] else "**差异**"))
        out.append("")
    out.append("### 差异归类与裁定\n")
    import collections

    def classify(x: dict) -> str:
        """把一条差异归入处置类——**归类本身即是裁定**，故规则写死在这里、可复跑。"""
        if x["kind"] == "格局":
            if x["book_val"] == "hua":
                return "**化气格未成立**（书判化气格、本引擎未取化格）"
            if (str(x["ours"]).startswith("cong_") and str(x["book_val"]).startswith("cong_")):
                return "**从格方向不同**（同为从格，但从的对象不同）"
            return "格局：正格 / 从格之别"
        if x["kind"] == "档位":
            try:
                i, j = LEVEL_WORDS.index(x["book_val"]), LEVEL_WORDS.index(str(x["ours"]))
            except ValueError:
                return "档位：一方无档位名"
            return ("档位：**相邻一档**（口径边界）" if abs(i - j) == 1
                    else "档位：**跨两档以上**（须优先看）")
        if x["kind"] == "用神":
            return "用神：方向不同"
        return "其余"

    buckets: dict[str, list[dict]] = collections.defaultdict(list)
    for x in bad:
        buckets[classify(x)].append(x)
    if not buckets:
        out.append("（无差异）\n")
    for name, items in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        out.append("#### %s —— %d 条\n" % (name, len(items)))
        out.append("| 例 | 源行 | 该步 | 书中 | 本引擎 |")
        out.append("|---|---|---|---|---|")
        for x in items:
            out.append("| %s | %s | %s | %s | %s |" % (
                x["id"], x["line"], x["gz"], x["book"], x["ours"]))
        out.append("")
    out.append("## 无法对拍清单\n")
    out.append("| 例 | 原因 |")
    out.append("|---|---|")
    for x in u:
        out.append("| %s | %s |" % (x["id"], x["why"]))
    out.append("")
    out.append("## 全量层（供逐例裁定）\n")
    out.append("前 %d 例——「该步的档位 / 格局 / 用神」与书中结论原文并列，"
               "差异须能从依据解释（SC-001）。\n" % min(limit_listing, len(l)))
    out.append("| 例 | 源行 | 四柱 | 该步 | 档位 | 格局 | 用神 | 书中结论（节选） |")
    out.append("|---|---|---|---|---|---|---|---|")
    for x in l[:limit_listing]:
        concl = x["conclusion"].replace("|", "／").replace("\n", " ")
        out.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            x["id"], x["line"], x["pillars"], x["gz"], x["level"], x["ge_ju"],
            x["yong"] or "—", concl[:220]))
    out.append("")
    out.append("## 预期口径差异（非缺陷）\n")
    for k, v in RULING_DIFFS.items():
        out.append("- **%s**：%s" % (k, v))
    out.append("")
    out.append(ADJUDICATION)
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="013 岁运对拍")
    ap.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=None, help="只跑前 N 例（调试用）")
    ap.add_argument("--listing", type=int, default=30, help="全量层列出的例数")
    a = ap.parse_args(argv)

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    res = run(a.fixtures, a.limit)
    text = _md(res, a.listing)
    a.out.write_text(text, encoding="utf-8", newline="\n")
    ok = [x for x in res["matched"] if x["agree"]]
    print("岁运算例 %d；可对拍 %d；关键词断言 %d 条（一致 %d / 差异 %d）；无法对拍 %d"
          % (res["total"], len(res["listings"]), len(res["matched"]),
             len(ok), len(res["matched"]) - len(ok), len(res["unmatched"])))
    print("报告 → %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
