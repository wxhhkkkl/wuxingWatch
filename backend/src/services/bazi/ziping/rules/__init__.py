"""规则模型与注册表（015 期 FR-001/FR-003/FR-010/FR-011）。

硬约束：**无书证不立规**——`Condition` / `Remedy` 必须有 `Citation`；书内矛盾/只有歌诀的
条件标 `status="open"`，由引擎输出「存疑/未定」，不得静默选边。
"""

from __future__ import annotations

import hashlib
import importlib
import pathlib
from dataclasses import dataclass, field

_RULE_MODULES = (
    "zhengguan", "qisha", "cai", "yin", "shishen", "shangguan",
    "yangren", "lujie", "zhuanwang", "huagi", "congge", "zage",
)
_BIG_GE_ORDER = {
    "正官格": 0, "七煞格": 1, "财格": 2, "印格": 3, "食神格": 4, "伤官格": 5,
    "阳刃格": 6, "禄劫格": 7, "专旺格": 8, "化气格": 9, "从格": 10, "杂格": 11,
}


@dataclass(frozen=True)
class Citation:
    chapter: str
    section: str
    condition_no: str | None = None
    page: str = ""
    quote: str | None = None

    def __post_init__(self):
        if not self.chapter or not self.section:
            raise ValueError("Citation 需 chapter + section")
        if not self.page:
            raise ValueError("Citation 需 page（书页/PDF 页）")


@dataclass(frozen=True)
class Condition:
    id: str
    text: str
    kind: str
    predicate: str
    citation: Citation
    params: dict = field(default_factory=dict)
    status: str = "active"           # active | open
    branch_options: tuple[str, ...] = ()
    degraded_if_missing: tuple[str, ...] = ()

    def __post_init__(self):
        if self.status not in ("active", "open"):
            raise ValueError(f"Condition.status 非法：{self.status}")
        if not self.citation:
            raise ValueError(f"Condition {self.id} 缺书证")


@dataclass(frozen=True)
class Remedy:
    id: str
    disease: str
    medicine: str
    path: str
    citation: Citation
    requires: tuple[Condition, ...] = ()
    status: str = "active"

    def __post_init__(self):
        if self.status not in ("active", "open"):
            raise ValueError(f"Remedy.status 非法：{self.status}")


@dataclass(frozen=True)
class GeJuDefinition:
    id: str
    name: str
    aliases: tuple[str, ...]
    category: str                   # inner | outer
    big_ge: str
    sub_ge: str | None
    status: str                     # implemented | reserved | open
    citations: tuple[Citation, ...]
    prerequisites: tuple[Condition, ...] = ()
    cheng_conditions: tuple[Condition, ...] = ()
    po_conditions: tuple[Condition, ...] = ()
    jiang_conditions: tuple[Condition, ...] = ()
    remedies: tuple[Remedy, ...] = ()
    yong_shen: dict = field(default_factory=dict)
    xiang_shen: dict = field(default_factory=dict)
    xi_ji: dict = field(default_factory=dict)
    gao_di: tuple = ()
    yun_xi_ji: tuple = ()
    specificity: int = 0            # 小格 > 大格；同 big_ge 内先取更具体者

    def __post_init__(self):
        if self.category not in ("inner", "outer"):
            raise ValueError(f"GeJuDefinition.category 非法：{self.category}")
        if self.status not in ("implemented", "reserved", "open"):
            raise ValueError(f"GeJuDefinition.status 非法：{self.status}")
        if not self.citations:
            raise ValueError(f"GeJuDefinition {self.id} 缺总书证")
        for c in (*self.prerequisites, *self.cheng_conditions,
                  *self.po_conditions, *self.jiang_conditions):
            if not c.citation:
                raise ValueError(f"GeJuDefinition {self.id} 的条件 {c.id} 缺书证")
        for r in self.remedies:
            if not r.citation:
                raise ValueError(f"GeJuDefinition {self.id} 的救应 {r.id} 缺书证")


_REGISTRY: list[GeJuDefinition] = []
_LOADED = False


def register(defn: GeJuDefinition) -> GeJuDefinition:
    if any(d.id == defn.id for d in _REGISTRY):
        raise ValueError(f"重复的格 id：{defn.id}")
    _REGISTRY.append(defn)
    return defn


def big_ge_order(name: str) -> int:
    """大格在书中的次序（用于同 stage 内的并列排序）。"""
    return _BIG_GE_ORDER.get(name, 99)


def all_definitions() -> list[GeJuDefinition]:
    load_rules()
    return sorted(
        _REGISTRY,
        key=lambda d: (0 if d.category == "inner" else 1,
                       _BIG_GE_ORDER.get(d.big_ge, 99),
                       -d.specificity,
                       d.id),
    )


def load_rules() -> None:
    """导入 12 个大格模块以触发注册；缺模块不报错（分批实现期）。"""
    global _LOADED
    if _LOADED:
        return
    for name in _RULE_MODULES:
        try:
            importlib.import_module(f"{__name__}.{name}")
        except ModuleNotFoundError as exc:
            if exc.name != f"{__name__}.{name}":
                raise
    _LOADED = True


def rules_version() -> str:
    """规则表源码哈希——规则一改就变，便于记录「同一输入、不同规则版本」。"""
    root = pathlib.Path(__file__).resolve().parent
    h = hashlib.sha1()
    for p in sorted(root.glob("*.py")):
        h.update(p.read_bytes())
    return h.hexdigest()[:12]
