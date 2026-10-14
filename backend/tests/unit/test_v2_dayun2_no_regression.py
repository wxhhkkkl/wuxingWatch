"""014 期 T005：结构守门（不变量 I-7）。

FR-004 要求引擎2 与现引擎**互不影响**。这条若只靠人工 review，迟早会破——
本项目已有多次「两处路径须同值」的教训。故把「没接线」变成会失败的测试：

1. **import 图**：从现引擎的每一个入口模块出发做传递闭包，`dayun2` 不可达。
2. **开关已删**（R27）：`include_suiyun` 全仓不得残留——连片改走联通图，
   「含不含岁运」由传进来的 `cols` 自己决定。
3. **入口模块不自曝**：`v2/__init__.py` 不导出 dayun2。
4. **只读表只有一份**：`dangzhong_*` 只许定义在 `tables.py`。

本文件首跑（dayun2 尚不存在时）平凡通过——它是**回归护栏**，不是红-绿循环的一环。
"""

from __future__ import annotations

import ast
from pathlib import Path

V2_DIR = Path(__file__).resolve().parents[2] / "src" / "services" / "bazi" / "v2"

# 现引擎的入口模块：从它们出发，import 图里不得出现 dayun2
ENGINE_ENTRIES = (
    "dayun", "pipeline", "relations", "ban", "tables", "degrees",
    "shengke", "geju", "xiyong_v2", "layers", "yongshen_table", "_ordered",
)

# 只读表的归属：党众四个函数只许定义在这里。
_SWITCH_OWNER = "tables.py"


def _module_names(path: Path) -> set[str]:
    """该文件 import 的、属于 `services.bazi` 包内的**模块短名**（下划线开头的原样保留）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("services.bazi"):
                    out.add(a.name.rsplit(".", 1)[-1])
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith("services.bazi"):
                parts = mod.split(".")
                # `from services.bazi.v2 import dayun` → 目标是「导入的名字」
                if mod.endswith(".v2") or mod.endswith(".bazi"):
                    out.update(a.name for a in node.names)
                else:
                    out.add(parts[-1])
            elif node.level:                       # 相对 import（包内）
                out.update(a.name for a in node.names)
    return out


def _graph() -> dict[str, set[str]]:
    return {p.stem: _module_names(p) for p in V2_DIR.glob("*.py")}


def test_engine_import_graph_cannot_reach_dayun2():
    """① 传递闭包：现引擎的任一入口都到不了 dayun2。"""
    graph = _graph()
    seen: set[str] = set()
    stack = [m for m in ENGINE_ENTRIES if m in graph]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(n for n in graph.get(cur, ()) if n not in seen)
    assert "dayun2" not in seen, (
        f"现引擎的 import 图里出现了 dayun2（经由 {sorted(seen & set(graph))}）——"
        "FR-004 要求两套实现互不影响")


def test_the_dangzhong_switch_is_gone():
    """② R27 起没有 `include_suiyun` 开关——要不要把岁运算进连片，由**传进来的 cols**
    决定（图模型：带伪列即有枢纽边），不再由调用方挑。任何模块里残留它都是回退。"""
    offenders = sorted(
        p.name for p in V2_DIR.glob("*.py")
        if "include_suiyun" in p.read_text(encoding="utf-8")
    )
    assert not offenders, (
        f"`include_suiyun` 已在 R27 删除，但 {offenders} 里还有——"
        "「原始含土量」请改用 `dangzhong_natal*`")


def test_the_two_engines_share_one_dangzhong_implementation():
    """④ 连片只有一份实现：`dangzhong_*` 只定义在 `tables.py`，引擎2 走 import。

    （与 ③ 同旨：独立的是第 2–7 步的旺度链，**只读表共用**——spec 澄清①。
    本仓两度吃过「两处各写一套、然后悄悄漂移」的亏，故把「不许另立一份」变成测试。）"""
    names = ("dangzhong_run", "dangzhong_for", "dangzhong_natal", "dangzhong_natal_for")
    dup = sorted(
        f"{p.name}::{node.name}"
        for p in V2_DIR.glob("*.py") if p.name != _SWITCH_OWNER
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef) and node.name in names
    )
    assert not dup, f"这些模块另立了党众实现：{dup}——只许有 tables.py 那一份"


def test_v2_package_does_not_export_dayun2():
    """③ 包入口不把引擎2 暴露给现引擎侧。"""
    init = V2_DIR / "__init__.py"
    if not init.exists():
        return
    assert "dayun2" not in init.read_text(encoding="utf-8")


def test_the_gap_adapters_have_no_switch_argument():
    """⑤ SC-003 的第一道闸，R27 版：`dangzhong_*` 一律**不接受**开关形参。

    改前靠「形参默认 False」守住原局不变；现在靠**退化不变量**——
    盘上不带岁运伪列时图上没有枢纽边，结果与旧线性实现逐位相同
    （见 `tests/unit/test_v2_dangzhong_graph.py`）。若谁给这些函数加回开关形参，
    「两条路必须同值」的前提就没了，故在这里钉死。"""
    tree = ast.parse((V2_DIR / _SWITCH_OWNER).read_text(encoding="utf-8"))
    names = ("dangzhong_run", "dangzhong_for", "dangzhong_natal", "dangzhong_natal_for")
    found = {n.name: [a.arg for a in n.args.kwonlyargs]
             for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name in names}
    assert set(found) == set(names), "四个党众函数都须在 tables.py 里"
    for name, kwonly in found.items():
        assert not kwonly, f"{name} 多了开关形参：{kwonly}"
