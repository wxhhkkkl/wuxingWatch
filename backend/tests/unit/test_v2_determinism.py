"""T061 · v2 计算确定性测试（012 期 US6，FR-058）。

**要求**：同一输入在**任何进程、任何运行次序**下 MUST 产生**逐位相同**的结论，
包括各步骤依据文本的排列顺序（不得依赖无序集合的遍历顺序）。

**为什么需要**：既有引擎曾因 `SAN_HE`/`SAN_HUI` 的 `frozenset` 迭代顺序导致
**跨进程结果不一致**；v2 引入十八级顺序 + 并存判定后集合遍历点更多，风险面更大。

本测试通过**子进程 + 不同 `PYTHONHASHSEED`** 实跑，而非同进程内重复调用——
同进程内哈希种子相同，重复调用永远一致，测不出该缺陷。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]

CHART = {"year": {"gan": "甲", "zhi": "子"},
         "month": {"gan": "丙", "zhi": "寅"},
         "day": {"gan": "戊", "zhi": "辰"},
         "time": {"gan": "庚", "zhi": "申"}}

SCRIPT = """
import json, sys
sys.path.insert(0, {src!r})
from services.bazi.v2 import xiyong_analysis_v2
chart = json.load(open({chart_file!r}, encoding="utf-8"))
r = xiyong_analysis_v2({dm!r}, chart)
print(json.dumps({{"level": r["level"], "ge_ju": r["ge_ju"], "steps": r["steps"]}},
                 ensure_ascii=False, sort_keys=False))
"""


def _run(seed: str, chart: dict | None = None) -> str:
    """在**子进程**中跑一遍，`PYTHONHASHSEED` 指定。

    脚本与数据都经**临时文件**（UTF-8）传递——Windows 下把中文经 `-c` 传参会
    被控制台 GBK 编码破坏，测出来的失败是环境噪声而非确定性缺陷。
    """
    import tempfile

    chart = chart or CHART
    with tempfile.TemporaryDirectory() as td:
        chart_file = Path(td) / "chart.json"
        script_file = Path(td) / "run.py"
        chart_file.write_text(json.dumps(chart, ensure_ascii=False), encoding="utf-8")
        script_file.write_text(
            SCRIPT.format(src=str(BACKEND / "src"), chart_file=str(chart_file), dm="戊"),
            encoding="utf-8")
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONIOENCODING="utf-8",
                   PYTHONUTF8="1")
        p = subprocess.run([sys.executable, "-X", "utf8", str(script_file)],
                           capture_output=True, env=env, cwd=str(BACKEND), timeout=120)
    err = p.stderr.decode("utf-8", "replace") or p.stderr.decode("gbk", "replace")
    assert p.returncode == 0, err[-800:]
    return p.stdout.decode("utf-8", "replace").strip()


def test_same_result_across_hash_seeds():
    """不同 `PYTHONHASHSEED` 下结论与依据**逐位一致**（FR-058）。"""
    a = _run("0")
    b = _run("12345")
    c = _run("999")
    assert a == b == c, "跨进程结果不一致——存在依赖无序集合遍历的代码"


def test_steps_order_stable_across_processes():
    """`steps` 的键序列与各段 traces 顺序跨进程稳定。"""
    a = json.loads(_run("1"))
    b = json.loads(_run("777"))
    assert [s["key"] for s in a["steps"]] == [s["key"] for s in b["steps"]]
    for sa, sb in zip(a["steps"], b["steps"]):
        assert [t["expression"] for t in sa["traces"]] == \
               [t["expression"] for t in sb["traces"]], sa["key"]


def test_determinism_holds_for_relation_rich_chart():
    """关系密集的命局（多组刑冲合害）同样确定。"""
    rich = {"year": {"gan": "戊", "zhi": "辰"},
            "month": {"gan": "丁", "zhi": "未"},
            "day": {"gan": "甲", "zhi": "子"},
            "time": {"gan": "庚", "zhi": "申"}}
    assert _run("3", rich) == _run("4242", rich)
