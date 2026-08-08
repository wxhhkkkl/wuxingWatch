"""命盘长图 generation with Pillow (server-side, CJK font).

Rendered as a vertical long image so it can be saved to the album / shared on
WeChat. A bundled CJK font is preferred; system fonts are used as fallback so
local dev/tests work out of the box.
"""

import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    # bundled font (production)
    os.path.join(os.path.dirname(__file__), "fonts", "NotoSansSC-Regular.otf"),
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]

WIDTH = 720
BG = (255, 255, 255)
INK = (33, 33, 33)
ACCENT = (156, 39, 39)
GRAY = (120, 120, 120)


def _font_path() -> str | None:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = _font_path()
    if path:
        return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def render_long_image(result: dict, person_name: str | None = None) -> bytes:
    """Render a chart to a PNG byte string."""
    title_font = _font(34)
    section_font = _font(24)
    body_font = _font(20)

    lines: list[str] = []
    if person_name:
        lines.append(f"命主：{person_name}")
    if result.get("solar_birth"):
        lines.append(f"出生：{result['solar_birth'][:16]}（农历 {result['lunar_birth']}）")
    else:
        p = result["pillars"]
        lines.append(
            f"出生：四柱输入 {p['year']['ganzhi']} {p['month']['ganzhi']} "
            f"{p['day']['ganzhi']} {p['time']['ganzhi']}"
        )

    pillars = result["pillars"]
    p_line = "  ".join(
        f"{name} {p['ganzhi']}" if p else f"{name} —"
        for name, p in (
            ("年", pillars["year"]),
            ("月", pillars["month"]),
            ("日", pillars["day"]),
            ("时", pillars["time"]),
        )
    )
    lines.append(p_line)

    day_master = result["day_master"]
    xi = result["xi_yong"]["conclusion"]
    lines.append(
        f"喜忌：{day_master}日主 {'身强' if xi['summary'] == '身强' else '身弱'}，"
        f"用神 {xi['yong_shen']}，喜 {('、'.join(xi['xi_shen']) or '—')}，"
        f"忌 {('、'.join(xi['ji_shen']) or '—')}"
    )

    dayun = result["da_yun"]
    if dayun.get("start_age"):
        lines.append(f"大运：{dayun['start_age']} 岁起运")
    else:
        lines.append("大运：四柱输入，无起运岁数")
    for step in dayun["steps"][:4]:
        if step.get("start_year") is not None:
            lines.append(f"  {step['ganzhi']}（{step['start_year']}–{step['end_year']}）")
        else:
            lines.append(f"  {step['ganzhi']}")

    lian = result["liu_nian"][:6]
    lines.append("流年：" + "  ".join(f"{n['year']} {n['ganzhi']}" for n in lian))

    lines.append("—")
    lines.append("内容为算法生成的参考信息，仅供参考，不构成专业命理建议。")

    height = 120 + len(lines) * 44
    img = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((32, 32), "八字命盘", font=title_font, fill=ACCENT)
    y = 96
    for i, line in enumerate(lines):
        draw.text(
            (32, y),
            line,
            font=section_font if i == 0 else body_font,
            fill=INK if i < len(lines) - 1 else GRAY,
        )
        y += 44

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
