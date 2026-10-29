"""子平格局喜忌引擎（015 期）。

对外入口：
- `judge_yuanju(pillars, wan_du)`：原局取格/成破/存疑；
- `judge_dayun(yuanju, pillars, wan_du, steps)`：逐步大运；
- `build_facts` / `rules_version`：事实层与规则版本。

规则源：相也《格局真诠》（2018）。旺度只提供身强弱（日主组动态，10 度）。
"""

from .engine import judge_dayun, judge_yuanju
from .facts import build_facts
from .rules import rules_version

__all__ = ["judge_yuanju", "judge_dayun", "build_facts", "rules_version"]
