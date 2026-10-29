"""条件求值器（015 期 FR-005）：把书中的条件写成可测试的谓词。

每个谓词接收 `(facts, params)`，返回 bool；`evaluate` 把结果连同书证、分支、
未知标记一起返回。`status="open"` 的条件仍求值，但 `unknown=True`，由引擎
输出「存疑/未定」，不得被当成 False 静默消解。
"""

from __future__ import annotations

from dataclasses import dataclass

from .rules import Citation, Condition

_BAD_TYPES = ("冲", "刑", "害", "破")


@dataclass(frozen=True)
class ConditionResult:
    id: str
    text: str
    result: bool
    branch: str | None
    citation: Citation
    note: str = ""
    unknown: bool = False


def _count(facts, ten_god: str) -> int:
    return sum(1 for t in facts.all_ten_gods if t == ten_god)


def _p_month_ten_god(facts, p: dict) -> bool:
    return facts.month_ten_god == p.get("ten_god")


def _p_has_ten_god(facts, p: dict) -> bool:
    return _count(facts, p.get("ten_god", "")) >= int(p.get("min", 1))


def _p_no_ten_god(facts, p: dict) -> bool:
    return _count(facts, p.get("ten_god", "")) <= int(p.get("max", 0))


def _p_count_le(facts, p: dict) -> bool:
    return _count(facts, p.get("ten_god", "")) <= int(p.get("max", 0))


_YANG_REN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}


def _p_yang_ren(facts, p: dict) -> bool:
    return _YANG_REN.get(facts.day_master) == facts.month_zhi


def _p_not_yang_ren(facts, p: dict) -> bool:
    return _YANG_REN.get(facts.day_master) != facts.month_zhi


def _p_dm_in_relation(facts, p: dict) -> bool:
    types = p.get("types") or ("五合", "天合地合")
    for rel in facts.relations.get("established", []):
        typ = str(rel.get("type", ""))
        if any(t in typ for t in types) and facts.day_master in (rel.get("members") or []):
            return True
    return False


def _p_month_zhi(facts, p: dict) -> bool:
    return facts.month_zhi == p.get("zhi")


def _p_month_ten_god_in(facts, p: dict) -> bool:
    return facts.month_ten_god in p.get("ten_gods", ())


def _p_day_master_gan(facts, p: dict) -> bool:
    return facts.day_master in p.get("gan", ())


def _p_day_master_wx(facts, p: dict) -> bool:
    return facts.day_master_wx == p.get("wx")


def _p_has_any_ten_god(facts, p: dict) -> bool:
    return any(_count(facts, g) >= int(p.get("min", 1)) for g in p.get("ten_gods", ()))


def _p_no_any_ten_god(facts, p: dict) -> bool:
    return all(_count(facts, g) <= int(p.get("max", 0)) for g in p.get("ten_gods", ()))


def _p_tou_gan(facts, p: dict) -> bool:
    return p.get("ten_god") in facts.tou_gan.values()


def _p_no_tou_gan(facts, p: dict) -> bool:
    return p.get("ten_god") not in facts.tou_gan.values()


def _p_no_bad_month(facts, p: dict) -> bool:
    month = facts.month_zhi
    for rel in facts.relations.get("established", []):
        typ = str(rel.get("type", ""))
        members = rel.get("members") or []
        if month and month in members and any(b in typ for b in _BAD_TYPES):
            return False
    return True


def _p_relation(facts, p: dict) -> bool:
    types = tuple(p.get("types") or ())
    members = set(p.get("members") or ())
    for rel in facts.relations.get("established", []):
        typ = str(rel.get("type", ""))
        rel_members = set(rel.get("members") or [])
        if types and not any(t in typ for t in types):
            continue
        if members and not members.issubset(rel_members):
            continue
        return True
    return False


def _p_root(facts, p: dict) -> bool:
    return facts.dm_root >= float(p.get("min", 0.0))


def _p_strength(facts, p: dict) -> bool:
    return facts.shen_qiang_ruo == p.get("value")


def _p_always(facts, p: dict) -> bool:
    return True


_PREDICATES = {
    "month_ten_god": _p_month_ten_god,
    "yang_ren": _p_yang_ren,
    "not_yang_ren": _p_not_yang_ren,
    "dm_in_relation": _p_dm_in_relation,
    "month_zhi": _p_month_zhi,
    "month_ten_god_in": _p_month_ten_god_in,
    "day_master_gan": _p_day_master_gan,
    "day_master_wx": _p_day_master_wx,
    "has_ten_god": _p_has_ten_god,
    "has_any_ten_god": _p_has_any_ten_god,
    "no_any_ten_god": _p_no_any_ten_god,
    "no_ten_god": _p_no_ten_god,
    "count_le": _p_count_le,
    "tou_gan": _p_tou_gan,
    "no_tou_gan": _p_no_tou_gan,
    "no_bad_relation_to_month": _p_no_bad_month,
    "relation": _p_relation,
    "root": _p_root,
    "strength": _p_strength,
    "always": _p_always,
}


def evaluate(condition: Condition, facts) -> ConditionResult:
    fn = _PREDICATES.get(condition.predicate)
    if fn is None:
        raise ValueError(f"未知谓词：{condition.predicate}（条件 {condition.id}）")
    result = bool(fn(facts, condition.params))
    branch = condition.params.get("branch")
    note = condition.params.get("note", "")
    return ConditionResult(
        id=condition.id, text=condition.text, result=result, branch=branch,
        citation=condition.citation, note=note,
        unknown=(condition.status == "open"),
    )
