"""Birth-place → longitude/latitude lookup.

v1 ships a small starter dataset (provincial capitals + major cities). Unknown
places return None and the chart falls back to standard UTC+8 time (spec edge
case: "出生地点无法解析...回退为东八区标准时间").
"""

CITY_COORDS: dict[str, tuple[float, float]] = {
    "北京": (116.41, 39.90),
    "上海": (121.47, 31.23),
    "天津": (117.19, 39.13),
    "重庆": (106.55, 29.56),
    "广州": (113.26, 23.13),
    "深圳": (114.06, 22.54),
    "杭州": (120.16, 30.29),
    "南京": (118.78, 32.06),
    "苏州": (120.62, 31.30),
    "成都": (104.07, 30.67),
    "武汉": (114.30, 30.59),
    "西安": (108.94, 34.34),
    "郑州": (113.63, 34.75),
    "济南": (117.12, 36.65),
    "青岛": (120.38, 36.07),
    "沈阳": (123.43, 41.80),
    "大连": (121.62, 38.91),
    "哈尔滨": (126.53, 45.80),
    "长春": (125.32, 43.90),
    "石家庄": (114.51, 38.04),
    "太原": (112.55, 37.87),
    "呼和浩特": (111.75, 40.84),
    "兰州": (103.83, 36.06),
    "西宁": (101.78, 36.62),
    "银川": (106.27, 38.47),
    "乌鲁木齐": (87.62, 43.82),
    "拉萨": (91.14, 29.65),
    "昆明": (102.71, 25.04),
    "贵阳": (106.63, 26.65),
    "南宁": (108.33, 22.82),
    "海口": (110.20, 20.04),
    "长沙": (112.94, 28.23),
    "南昌": (115.86, 28.68),
    "合肥": (117.28, 31.86),
    "福州": (119.30, 26.08),
    "厦门": (118.09, 24.48),
}

# 常见"省/市"后缀与别名（简单规范化）
_STRIP = ("省", "市", "自治州", "地区", "盟")


def _normalize(name: str) -> str:
    n = name.strip()
    for suffix in _STRIP:
        if n.endswith(suffix):
            n = n[: -len(suffix)]
            break
    return n


def lookup(place: str | None) -> tuple[float, float] | None:
    """Return (longitude, latitude) for a place name, or None if unknown."""
    if not place:
        return None
    n = _normalize(place)
    coords = CITY_COORDS.get(n) or CITY_COORDS.get(_normalize(place[:2]))
    return (coords[0], coords[1]) if coords else None
