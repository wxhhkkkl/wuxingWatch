"""016 期：以《子平真诠》为规则源的 25 类格局判定。"""

from .engine import judge_yuanju, rules_version
from .facts import Facts, build_facts
from .rules import Decision, classify
from .taxonomy import CLASS_GROUP, UNSUPPORTED

__all__ = [
    "judge_yuanju", "rules_version", "Facts", "build_facts", "Decision",
    "classify", "CLASS_GROUP", "UNSUPPORTED",
]
