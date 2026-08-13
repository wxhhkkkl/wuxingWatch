"""通用 MySQL→MySQL 全表迁移（保留主键，逐表行数校验，失败回滚且不动源库）。

用法: uv run python -m src.scripts.migrate_all_tables --src <mysql url> --dst <mysql url>
所有 Base.metadata 注册的表都会迁移。
"""

import argparse

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

import models  # noqa: F401  (register all ORM models)
from db.session import Base

# 依赖序（外键）：先建被引用表
ORDER = [
    "users",
    "categories",
    "geo_cities",
    "books",
    "refresh_sessions",
    "bazi_charts",
    "chapters",
    "reading_progress",
    "audit_logs",
]


def migrate(src_url: str, dst_url: str) -> None:
    src_engine = create_engine(src_url)
    dst_engine = create_engine(dst_url)
    Base.metadata.create_all(dst_engine)  # 确保目标表存在（幂等）

    Src = sessionmaker(bind=src_engine)
    Dst = sessionmaker(bind=dst_engine)
    src, dst = Src(), Dst()
    try:
        is_mysql = dst_engine.dialect.name == "mysql"
        if is_mysql:
            dst.execute(text("SET FOREIGN_KEY_CHECKS=0"))

        for name in ORDER:
            tbl = Base.metadata.tables[name]
            rows = [dict(r) for r in src.execute(select(tbl)).mappings()]
            if rows:
                dst.execute(tbl.insert(), rows)
            print(f"迁移 {name}: {len(rows)} 行")

        if is_mysql:
            dst.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        dst.commit()

        # 行数校验
        for name in ORDER:
            got = dst.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
            exp = src.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
            if got != exp:
                raise RuntimeError(f"{name}: 期望 {exp} 行，实际 {got} 行")
        print("迁移完成，全部表行数校验通过。")
    except Exception:
        dst.rollback()
        raise
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MySQL→MySQL 全表迁移")
    parser.add_argument("--src", required=True, help="源 MySQL URL")
    parser.add_argument("--dst", required=True, help="目标 MySQL URL")
    args = parser.parse_args()
    migrate(args.src, args.dst)
