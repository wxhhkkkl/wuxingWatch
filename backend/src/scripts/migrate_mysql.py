"""SQLite → 腾讯云 MySQL 数据迁移（ORM，事务 + 行数校验，失败回滚且不动源库）。

用法: uv run python -m src.scripts.migrate_mysql [--src sqlite:///wuxing.db] [--dst <mysql url>]
默认 dst 取配置 DATABASE_URL（当前指向腾讯云 MySQL）。
"""

import argparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import models  # noqa: F401  (register all ORM models)
from core.config import get_settings
from db.session import Base
from models.bazi_chart import BaziChart
from models.session import RefreshSession
from models.user import User

DEFAULT_SQLITE = "sqlite:///wuxing.db"

TABLES = {
    "users": User,
    "refresh_sessions": RefreshSession,
    "bazi_charts": BaziChart,
}


def migrate(src_url: str, dst_url: str) -> None:
    src_engine = create_engine(src_url)
    dst_engine = create_engine(dst_url)
    Base.metadata.create_all(dst_engine)  # 确保目标表存在（幂等）
    Src = sessionmaker(bind=src_engine)
    Dst = sessionmaker(bind=dst_engine)
    src, dst = Src(), Dst()
    try:
        rows = {t: src.query(model).all() for t, model in TABLES.items()}
        print(
            f"读取源库: users={len(rows['users'])}, "
            f"sessions={len(rows['refresh_sessions'])}, charts={len(rows['bazi_charts'])}"
        )

        is_mysql = dst_engine.dialect.name == "mysql"
        if is_mysql:
            dst.execute(text("SET FOREIGN_KEY_CHECKS=0"))

        # 按依赖序写入（显式 id，保留原主键）
        for user in rows["users"]:
            dst.merge(
                User(
                    id=user.id,
                    phone=user.phone,
                    name=user.name,
                    gender=user.gender,
                    password_hash=user.password_hash,
                    role=user.role,
                    created_at=user.created_at,
                )
            )
        for sess in rows["refresh_sessions"]:
            dst.merge(
                RefreshSession(
                    id=sess.id,
                    user_id=sess.user_id,
                    refresh_token_hash=sess.refresh_token_hash,
                    expires_at=sess.expires_at,
                    created_at=sess.created_at,
                )
            )
        for chart in rows["bazi_charts"]:
            dst.merge(
                BaziChart(
                    id=chart.id,
                    user_id=chart.user_id,
                    person_name=chart.person_name,
                    relationship_type=chart.relationship_type,
                    name=chart.name,
                    gender=chart.gender,
                    birth_solar=chart.birth_solar,
                    birth_input_is_lunar=chart.birth_input_is_lunar,
                    birth_lunar=chart.birth_lunar,
                    birth_place=chart.birth_place,
                    longitude=chart.longitude,
                    latitude=chart.latitude,
                    notes=chart.notes,
                    chart_result=chart.chart_result,
                    created_at=chart.created_at,
                )
            )
        if is_mysql:
            dst.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        dst.commit()

        # 行数校验
        for table, expected in rows.items():
            got = dst.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            if got != len(expected):
                raise RuntimeError(f"{table}: 期望 {len(expected)} 行，实际 {got} 行")
        print("迁移完成，行数校验通过。")
    except Exception:
        dst.rollback()
        raise
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQLite → MySQL 数据迁移")
    parser.add_argument("--src", default=DEFAULT_SQLITE, help="源 SQLite URL")
    parser.add_argument(
        "--dst", default=get_settings().database_url, help="目标 MySQL URL（默认取 DATABASE_URL）"
    )
    args = parser.parse_args()
    migrate(args.src, args.dst)
