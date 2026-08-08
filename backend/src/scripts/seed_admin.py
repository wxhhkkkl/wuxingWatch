"""将指定手机号提升为管理员（首个管理员需账户已存在）。

用法: uv run python -m src.scripts.seed_admin --phone 13800138000
"""

import argparse
import sys

import models  # noqa: F401  (register all ORM models)
from db.session import SessionLocal
from models.user import User


def promote(phone: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if user is None:
            print(f"手机号 {phone} 不存在；请先在应用中注册该账户后再提升。")
            sys.exit(1)
        if user.role == "admin":
            print(f"{phone} 已是管理员。")
            return
        user.role = "admin"
        db.commit()
        print(f"已将 {phone} 提升为管理员。")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将指定手机号提升为管理员")
    parser.add_argument("--phone", required=True, help="管理员手机号")
    args = parser.parse_args()
    promote(args.phone)
