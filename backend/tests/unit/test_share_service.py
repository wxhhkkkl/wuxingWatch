"""T052 — Pillow long-image generation."""

from datetime import datetime

from services import share_service
from services.bazi.engine import compute_chart


def _result():
    return compute_chart(datetime(1990, 5, 20, 10, 30, 0), "M")


def test_render_png_bytes():
    png = share_service.render_long_image(_result())
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 1000


def test_render_with_person_name():
    png = share_service.render_long_image(_result(), person_name="张三")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 1000
