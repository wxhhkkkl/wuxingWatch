"""运支的旺相休囚死与状态增减——**只保留管线共用的两个量**。

2026-10-28：原 013 期的大运推导（`analyze_step` / `analyze_all` / 用神随大运变化）
已从产品中移除。本模块只剩 `dayun_state` 与 `STATE_DELTA`：它们被
`pipeline` / `relations` / `ban` 在**岁运列存在时**调用，是旺度管线的底层口径，
不是大运引擎本身。大运旺度由 `services.bazi.v2.dayun2`（引擎2）独立计算。
"""

from __future__ import annotations

from services.bazi.v2 import tables

# 状态 → 静态旺度增减（书 上 909「大运也具有部分月令的作用」）
STATE_DELTA = {"旺": 2.0, "余气": 1.5, "相": 1.0, "休": -1.0, "囚": -1.5, "死": -2.0}


def dayun_state(wx: str, dayun_zhi: str) -> str:
    """某五行在**运支**所处的旺相休囚死。

    **运支按「月令」取状态表**——书 上 204-299 的旺相休囚死表覆盖十二支，运支与月令
    同用此表（书 上 909「月令是五行旺衰的来源，而大运**也具有部分月令的作用**」）。
    """
    if not dayun_zhi:
        return "旺"
    return tables.month_state(wx, dayun_zhi)
