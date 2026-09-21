"""三阶段的**跨阶段不变量**（013 期 T045）。

一个文件承载七项——它们的共同点是「**不随阶段而变**」：无论原局、加入大运还是加入流年，
下面每条都必须成立。放在一处是因为它们一起构成「三页是同一条管线的层层增量、
不是三套并列结论」这句话的可验证形式。

| # | 不变量 | 依据 |
|---|---|---|
| ① | 来源标注**无歧义**——任一结论只标一个来源 | FR-024 / SC-008 |
| ② | `pairs` 的 7 类**两侧齐备**，不得只给一侧 | FR-016c / SC-009 |
| ③ | **依据可追溯**——每条关系与每条 effect 均带依据文本 | SC-005 |
| ④ | **同一命盘、同一步大运**在原局页与「加入大运」页的用神一致 | FR-022a / SC-007 |
| ⑤ | 大运干支**十年一体**，无「前五年干 / 后五年支」分割 | FR-013 |
| ⑥ | 岁运介入**不另立**专用次序，沿用同一套十八级 | FR-018 |
| ⑦ | 结论里**没有吉凶** | FR-016a |
"""

import pytest

from services.bazi.v2 import dayun
from services.bazi.v2.dayun import analyze_step, build_pairs

KEYS = ("year", "month", "day", "time")
SAMPLES = [
    "辛酉 庚寅 丙寅 乙未",
    "甲子 丙寅 戊午 辛酉",
    "己丑 辛未 甲戌 戊辰",
    "壬戌 壬子 戊子 戊午",
    "癸亥 乙卯 丁卯 辛亥",
]
DAYUN = "己丑"
LIUNIAN = "壬午"
SOURCES = {"yuanju", "dayun", "liunian"}


def _chart(pz: str) -> dict:
    return {k: {"gan": v[0], "zhi": v[1]}
            for k, v in zip(KEYS, pz.split())}


def _stages(pz: str):
    p = _chart(pz)
    return p, analyze_step(p, DAYUN), analyze_step(p, DAYUN, liunian_ganzhi=LIUNIAN)


def _strings(obj, path=()):
    """递归产出所有**字符串叶子**及其路径——用于「依据文本」「吉凶字样」这类全量扫描。"""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, path + (k,))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _strings(v, path + (i,))


def _relation_pairs(item: dict):
    for side in ("established", "rejected"):
        for r in (item["relations"] or {}).get(side, []):
            yield side, r


# ---------------------------------------------------------------
# ① 来源标注无歧义（FR-024 / SC-008）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_each_stage_tags_exactly_one_source(pz):
    """阶段本身只标一个来源；阶段 3 里**每一条关系**也只标一个。"""
    _, s2, s3 = _stages(pz)
    assert s2["source"] == "dayun"
    assert s3["source"] == "liunian"
    for item in (s2, s3):
        for side, r in _relation_pairs(item):
            assert r.get("source") in SOURCES, \
                "%s 的 %s 条目来源缺失或不在三值内：%r" % (side, item["source"], r.get("source"))


def _src_of(cols) -> str:
    """该组柱位对应的来源阶段——与后端 `relations._source_of` 同口径（流年优先）。"""
    keys = set(cols or ())
    if "_liunian" in keys:
        return "liunian"
    if "_dayun" in keys:
        return "dayun"
    return "yuanju"


@pytest.mark.parametrize("pz", SAMPLES)
def test_relation_source_is_always_justified(pz):
    """来源不是随便标的——它必须能**指着某一处柱位**说出来：

    - 属原局：自身不牵涉岁运，且**抢占者也不牵涉**（纯原局内的事）；
    - 属大运 / 属流年：**自身牵涉**该阶段之支，**或**被该阶段的某条关系抢占了柱位
      （让位——「本关系为何不成」正是岁运带来的）。

    两处都可能给出不同答案（如一条 `[年, _大运]` 的六合被 `[年, _流年]` 的六冲抢了柱位），
    此时来源随**抢占者**走：页面上要解释的是「它为什么不成」，那答案是流年给的。
    """
    _, s2, s3 = _stages(pz)
    for item in (s2, s3):
        for side, r in _relation_pairs(item):
            own = _src_of(r["cols"])
            blk = (r.get("blocked_by") or {}).get("cols")
            bsrc = _src_of(blk) if blk else "yuanju"
            assert r["source"] in SOURCES
            if r["source"] == "yuanju":
                assert own == "yuanju" and bsrc == "yuanju", \
                    "标成属原局，但自身或抢占者牵涉岁运：%r（自身 %s / 抢占者 %s）" \
                    % (r.get("detail") or r["type"], own, bsrc)
            else:
                assert r["source"] in (own, bsrc), \
                    "标成属%s，但无论自身柱位还是抢占者都对不上：%r" \
                    % (r["source"], r.get("detail") or r["type"])


@pytest.mark.parametrize("pz", SAMPLES)
def test_rejected_relation_attributes_to_the_blocker(pz):
    """被让位的关系，其来源随**抢占者**走——否则「为什么不成」这件事在页面上说不清来源。"""
    _, _, s3 = _stages(pz)
    checked = 0
    for _, r in _relation_pairs(s3):
        blk = r.get("blocked_by")
        if not blk:
            continue
        bcols = set(blk["cols"])
        want = "liunian" if "_liunian" in bcols else ("dayun" if "_dayun" in bcols else "yuanju")
        if want == "yuanju":
            continue
        checked += 1
        assert r["source"] == want, \
            "被岁运抢占却不标岁运来源：%r（抢占者柱位 %r，标成 %r）" % (r.get("reason"), sorted(bcols), r["source"])
    assert checked >= 0        # 样本里可能没有这种情形，不强制非零


# ---------------------------------------------------------------
# ② pairs 七类两侧齐备（FR-016c / SC-009）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_pairs_cover_seven_items_with_both_sides(pz):
    _, s2, s3 = _stages(pz)
    pairs = build_pairs(s2, s3)
    assert [p["key"] for p in pairs] == [
        "yong_shen.theoretical.element", "yong_shen.xi_shen", "yong_shen.ji_shen",
        "level", "ge_ju.type", "tiaohou", "layers",
    ]
    for p in pairs:
        assert p["dayun"]["source"] == "dayun" and p["liunian"]["source"] == "liunian"
        assert p["dayun"]["value"] is not None, "缺属大运一侧：%s" % p["key"]
        assert p["liunian"]["value"] is not None, "缺属流年一侧：%s" % p["key"]
        assert p["changed"] == (p["dayun"]["value"] != p["liunian"]["value"])


# ---------------------------------------------------------------
# ③ 依据可追溯（SC-005）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_every_relation_and_effect_carries_a_reason(pz):
    """每条关系与非空的 effects 都必须带**可读依据文本**——否则页面上是一堆无出处的判定。"""
    _, s2, s3 = _stages(pz)
    for item in (s2, s3):
        for side, r in _relation_pairs(item):
            if side == "established":
                assert (r.get("detail") or "").strip(), \
                    "成立的关系没有依据文本：%r" % r
            else:
                assert (r.get("reason") or "").strip(), \
                    "未成立的关系没有说明原因：%r" % r
            for e in r.get("effects") or []:
                assert (e.get("reason") or "").strip(), \
                    "effect 没有依据文本：%r" % e


@pytest.mark.parametrize("pz", SAMPLES)
def test_every_step_has_rule_and_result(pz):
    """依据段逐段可读（title / rule / result）——页面按这三项渲染。"""
    _, s2, s3 = _stages(pz)
    for item in (s2, s3):
        steps = item.get("steps") or []
        assert steps, "阶段结论须带依据段（data-model §1）"
        for s in steps:
            assert (s.get("title") or "").strip()
            assert (s.get("rule") or "").strip()
            assert (s.get("result") or "").strip()


# ---------------------------------------------------------------
# ④ 同一步大运，两页的用神一致（FR-022a / SC-007）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_same_step_same_yongshen_on_both_pages(pz):
    """原局页「用神随大运变化」那一行的用神，与「加入大运」页该步的用神**逐项相同**。

    两页若各有一套大运口径，同一命盘同一步会显示两个用神——这正是 FR-022a 要禁的。
    """
    from services.bazi.v2 import xiyong_analysis_v2

    p = _chart(pz)
    steps = [{"ganzhi": DAYUN, "start_year": 2020, "start_age_xu": 30}]
    s1 = xiyong_analysis_v2(p["day"]["gan"], p, steps)
    assert s1["dayun"], "原局结论须含「用神随大运变化」那一行"
    row = s1["dayun"][0]
    page2 = analyze_step(p, DAYUN, dayun_meta=steps[0])
    assert row["yong_shen"] == page2["yong_shen"]
    assert row["tiaohou"] == page2["tiaohou"]
    assert row["layers"] == page2["layers"]


# ---------------------------------------------------------------
# ⑤ 大运干支十年一体（FR-013）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_the_step_is_taken_as_a_whole_decade(pz):
    """**没有**前五年干 / 后五年支这回事——结论里不得出现任何半年份分割的痕迹。

    判据两条：① 结果里不出现「前五年 / 后五年 / 前半 / 后半」之类字样；
    ② `analyze_step` 没有「第几年」这个入参——它只认干支，十年只有一份结论。
    """
    import inspect

    _, s2, s3 = _stages(pz)
    banned = ("前五年", "后五年", "前半", "后半", "上半运", "下半运")
    for item in (s2, s3):
        for path, txt in _strings(item):
            for b in banned:
                assert b not in txt, "%s 出现 %r：%s" % (".".join(map(str, path)), b, txt)
    params = set(inspect.signature(analyze_step).parameters)
    assert not ({"year", "elapsed_year", "year_index"} & params), \
        "analyze_step 出现了「第几年」入参——那意味着十年被切开判（FR-013）"


# ---------------------------------------------------------------
# ⑥ 沿用同一套十八级（FR-018）
# ---------------------------------------------------------------

@pytest.mark.parametrize("pz", SAMPLES)
def test_suiyun_reuses_the_same_eighteen_tiers(pz):
    """岁运介入**不另立**专用次序：级号仍落在 1..18，类型名仍取自**同一张十八级级表**。

    注意判据取的是 `TYPE_OF_TIER` 的**全表**，不是「本盘原局出现过的类型」——
    岁运之支会带来原局里原本没有的支，因而合法地引出原局没出现过的类型
    （如原局无六害、加入流年之支后成六害）。那是**同一张表的新条目**，不是新次序。
    """
    from services.bazi.v2 import relations

    _, s2, s3 = _stages(pz)
    vocab = set(relations.TYPE_OF_TIER.values())
    assert len(relations.TYPE_OF_TIER) == 18, "十八级级表本身的条目数变了"
    for item in (s2, s3):
        for _, r in _relation_pairs(item):
            assert 1 <= r["tier"] <= 18, "级号越界：%r" % r
            assert r["type"] in vocab, \
                "岁运引入了级表之外的关系类型 %r——等于另立了一套次序（FR-018）" % r["type"]


# ---------------------------------------------------------------
# ⑦ 没有吉凶（FR-016a）
# ---------------------------------------------------------------

# 注：**不列 `verdict`** —— `layers.verdict` 是**格局层次**（贵气高低），
# 不是吉凶结论（同 tests/contract/test_suiyun_api.py 的口径）。
_FORBIDDEN_KEYS = {"jixiong", "吉凶", "lucky", "unlucky", "score_ji", "score_xiong",
                   "ji_xiong", "断语", "事件"}


@pytest.mark.parametrize("pz", SAMPLES)
def test_no_verdict_anywhere_in_the_stages(pz):
    _, s2, s3 = _stages(pz)
    for item in (s2, s3):
        for path, _txt in _strings(item):
            for seg in path:
                assert str(seg) not in _FORBIDDEN_KEYS, \
                    "结论里出现吉凶类字段：%s" % ".".join(map(str, path))
        pairs = build_pairs(s2, s3)
        for p in pairs:
            assert set(p) == {"key", "label", "dayun", "liunian", "changed"}, \
                "成对项里多了字段（可能是吉凶）：%r" % sorted(p)
