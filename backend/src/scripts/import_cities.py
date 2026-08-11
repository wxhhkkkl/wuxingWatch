"""将 GeoNames cities15000 导入 geo_cities 表（幂等，已存在则跳过）。

用法: uv run python -m src.scripts.import_cities --file /path/to/cities15000.txt [--limit N]
"""

import argparse
import re

import models  # noqa: F401  (register all ORM models)
from db.session import Base, SessionLocal
from models.city import GeoCity

# GeoNames 中国 admin1 代码 → 中文省名（源自 admin1CodesASCII.txt）
CN_PROVINCES = {
    "01": "安徽省",
    "02": "浙江省",
    "03": "江西省",
    "04": "江苏省",
    "05": "吉林省",
    "06": "青海省",
    "07": "福建省",
    "08": "黑龙江省",
    "09": "河南省",
    "10": "河北省",
    "11": "湖南省",
    "12": "湖北省",
    "13": "新疆维吾尔自治区",
    "14": "西藏自治区",
    "15": "甘肃省",
    "16": "广西壮族自治区",
    "18": "贵州省",
    "19": "辽宁省",
    "20": "内蒙古自治区",
    "21": "宁夏回族自治区",
    "22": "北京市",
    "23": "上海市",
    "24": "山西省",
    "25": "山东省",
    "26": "陕西省",
    "28": "天津市",
    "29": "云南省",
    "30": "广东省",
    "31": "海南省",
    "32": "四川省",
    "33": "重庆市",
}

_ZH_RE = re.compile(r"[一-鿿]+")
_ADM_SUFFIX = ("特别行政区", "自治州", "地区", "市", "县", "区", "镇", "盟", "旗", "州")


def _extract_zh(alternatenames: str | None) -> str | None:
    """从 alternatenames 提取中文城市名。

    优先取带行政后缀的完整名（如 北京市/成都市）并剥掉后缀得通用名（北京/成都），
    避免命中昵称（如 成都 的 天府）。
    """
    runs = _ZH_RE.findall(alternatenames or "")
    if not runs:
        return None
    for run in runs:
        for suffix in _ADM_SUFFIX:
            if run.endswith(suffix) and len(run) - len(suffix) >= 2:
                return run[: -len(suffix)]
    return min(runs, key=len)


FIELDS = [
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "latitude",
    "longitude",
    "feature_class",
    "feature_code",
    "country_code",
    "cc2",
    "admin1",
    "admin2",
    "admin3",
    "admin4",
    "population",
    "elevation",
    "dem",
    "timezone",
    "moddate",
]


def import_file(path: str, limit: int | None = None) -> None:
    db = SessionLocal()
    try:
        Base.metadata.create_all(db.get_bind())  # 确保 geo_cities 表存在
        count = db.query(GeoCity).count()
        if count > 0:
            print(f"geo_cities 已有 {count} 行，跳过导入（如需重导请先清空该表）。")
            return
        batch: list[GeoCity] = []
        imported = 0
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if limit is not None and i >= limit:
                    break
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 19 or parts[6] != "P":  # 只导入人口居住地 feature class P
                    continue
                is_cn = parts[8] == "CN"
                batch.append(
                    GeoCity(
                        name=parts[1],
                        asciiname=parts[2] or None,
                        alternatenames=(parts[3][:2000] if parts[3] else None),
                        country_code=parts[8] or None,
                        latitude=float(parts[4]),
                        longitude=float(parts[5]),
                        timezone=parts[17] or None,
                        population=int(parts[15]) if parts[15] else None,
                        name_zh=_extract_zh(parts[3]) if is_cn else None,
                        admin1_zh=CN_PROVINCES.get(parts[10]) if is_cn else None,
                    )
                )
                if len(batch) >= 500:
                    db.add_all(batch)
                    db.commit()
                    imported += len(batch)
                    batch = []
                    print(f"  已导入 {imported} 条...")
        if batch:
            db.add_all(batch)
            db.commit()
            imported += len(batch)
        print(f"导入完成，共 {db.query(GeoCity).count()} 条。")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入 GeoNames 城市数据到 geo_cities")
    parser.add_argument("--file", required=True, help="cities15000.txt 路径")
    parser.add_argument("--limit", type=int, default=None, help="限制导入行数（调试用）")
    args = parser.parse_args()
    import_file(args.file, args.limit)
