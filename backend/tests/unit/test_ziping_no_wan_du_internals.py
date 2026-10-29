"""015 T016：结构守门——ziping 只消费旺度/引擎2 的公开结论。"""
import ast
import pathlib

FORBIDDEN = (
    "services.bazi.v2.pipeline",
    "services.bazi.v2.degrees",
    "services.bazi.v2.shengke",
    "services.bazi.v2.relations",
    "services.bazi.v2.ban",
)
ROOT = pathlib.Path(__file__).resolve().parents[2] / "src/services/bazi/ziping"


def test_ziping_does_not_import_wan_du_internals():
    for p in ROOT.rglob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.ImportFrom) and node.module:
                mods.append(node.module)
            if isinstance(node, ast.Import):
                mods.extend(a.name for a in node.names)
            for mod in mods:
                for bad in FORBIDDEN:
                    assert not mod.startswith(bad), f"{p} 引入了 {mod}"
