"""T027 — 迁移脚本行数/内容一致性（sqlite→sqlite 验证逻辑；MySQL 侧同 ORM 路径）。"""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.scripts.migrate_mysql import migrate

import models  # noqa: F401  (register all ORM models)
from db.session import Base
from models.bazi_chart import BaziChart
from models.user import User


def test_migrate_consistency(tmp_path):
    src_path = f"sqlite:///{tmp_path}/src.db"
    dst_path = f"sqlite:///{tmp_path}/dst.db"

    # 源库数据
    src_engine = create_engine(src_path)
    Base.metadata.create_all(src_engine)
    Src = sessionmaker(bind=src_engine)
    src = Src()
    src.add_all(
        [
            User(id=1, phone="13800138000", role="member"),
            User(id=2, phone="13900139000", role="admin", password_hash="argon2hash"),
            BaziChart(
                id=1,
                user_id=1,
                relationship_type="CHILD",
                birth_solar=datetime(1990, 5, 20, 10, 30, tzinfo=UTC),
                chart_result='{"day_master":"乙"}',
            ),
        ]
    )
    src.commit()
    src.close()

    # 执行迁移
    migrate(src_path, dst_path)

    # 校验目标库
    dst_engine = create_engine(dst_path)
    Dst = sessionmaker(bind=dst_engine)
    dst = Dst()
    try:
        assert dst.query(User).count() == 2
        assert dst.query(BaziChart).count() == 1
        admin = dst.query(User).filter(User.phone == "13900139000").first()
        assert admin.role == "admin"
        assert admin.password_hash == "argon2hash"
        chart = dst.query(BaziChart).first()
        assert chart.relationship_type == "CHILD"
        assert chart.chart_result == '{"day_master":"乙"}'
    finally:
        dst.close()
