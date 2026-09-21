"""把 `bazi_charts.chart_result` 由 TEXT(64KB) 升为 MEDIUMTEXT(16MB)。

**为什么需要**：判定依据（8 段命盘快照）整份 JSON 实测已到 **89KB**，超过 `TEXT` 的
64KB 上限。超限时 MySQL 会**截断并劈开多字节汉字**，报出的是
`1366 Incorrect string value: '\\xE6\\x9C\\xA8\\xE3\\x80\\x81...' for column 'chart_result'`
——字符集/连接看着全都正常，极难定位（本脚本即为此事的修复）。

`Base.metadata.create_all` **不会**改已存在的列，故老库须跑一次本脚本（幂等：
已是 mediumtext/mediumblob 就跳过）。

用法：
    uv run python -m src.scripts.upgrade_chart_result_mediumtext          # 用 .env 的 URL
    uv run python -m src.scripts.upgrade_chart_result_mediumtext --url <mysql url>
"""

import argparse

from sqlalchemy import create_engine, text

import models  # noqa: F401  (register all ORM models)
from core.config import get_settings

TABLE = "bazi_charts"
COLUMN = "chart_result"
TARGET = "mediumtext"


def _current_type(conn) -> str | None:
    return conn.execute(text(
        "SELECT DATA_TYPE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"),
        {"t": TABLE, "c": COLUMN}).scalar()


def upgrade(url: str) -> None:
    engine = create_engine(url)
    if engine.dialect.name != "mysql":
        print(f"[skip] 目标库是 {engine.dialect.name}，非 MySQL，无需升级")
        return
    with engine.begin() as conn:
        cur = _current_type(conn)
        if cur is None:
            print(f"[skip] 表 {TABLE}.{COLUMN} 不存在（新库由 create_all 直接按模型建 MEDIUMTEXT）")
            return
        if cur.lower() in ("mediumtext", "longtext"):
            print(f"[skip] {TABLE}.{COLUMN} 已是 {cur}，无需升级")
            return
        print(f"[do] {TABLE}.{COLUMN}: {cur} → {TARGET} …")
        conn.execute(text(
            f"ALTER TABLE {TABLE} MODIFY {COLUMN} {TARGET.upper()} NOT NULL"))
        print(f"[ok] 已升级为 {_current_type(conn)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=None, help="目标库 URL（缺省用 .env 的 DATABASE_URL）")
    args = ap.parse_args()
    upgrade(args.url or get_settings().database_url)


if __name__ == "__main__":
    main()
