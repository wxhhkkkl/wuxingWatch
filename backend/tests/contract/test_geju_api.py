"""015 T044：格局喜忌端点契约。"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

BASE = {
    "gender": "M",
    "calendar": "sizhu",
    "birth_pillars": {"year": "己卯", "month": "辛未",
                      "day": "壬寅", "time": "辛亥"},
}


def test_geju_endpoint_shape():
    r = client.post("/api/charts/geju", json=BASE)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["engine"] == "ziping-geju"
    assert body["rules_version"]
    assert body["input_scope"] in ("four_pillars", "three_pillars")
    y = body["yuanju"]
    assert y["main_ge"]["name"] == "正官配印格"
    assert y["main_ge"]["big_ge"] == "正官格"
    assert y["shen_qiang_ruo"]["value"] in ("strong", "weak", "unknown")
    assert y["main_ge_basis"]["citation"]["page"]
    assert y["yong_shen"] and y["yong_shen"]["citation"]["page"]
    assert isinstance(y["xiang_shen"], list)
    assert isinstance(y["xi_shen"], list) and isinstance(y["ji_shen"], list)
    assert y["gao_di"]["value"] in ("上", "中", "下", "未定")
    assert isinstance(y["disease"], list)
    assert "remedy" in y
    assert isinstance(y["conditions"], list) and y["conditions"]
    assert any(c["branch"] is None for c in y["conditions"])
    assert isinstance(body["dayun_steps"], list)
    if body["dayun_steps"]:
        assert "diff" in body["dayun_steps"][0]
    assert isinstance(body["open_issues"], list)


def test_geju_invalid_dayun_is_422():
    r = client.post("/api/charts/geju", json={**BASE, "dayun_ganzhi": "甲甲"})
    assert r.status_code == 422, r.text
    assert "不在该盘的大运步内" in r.json()["detail"]


def test_geju_three_pillars_degrades():
    r = client.post("/api/charts/geju", json={
        "gender": "M", "calendar": "solar", "birth_date": "1990-05-20",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["input_scope"] == "three_pillars"
    assert body["degradations"], "缺时柱须给出降级说明"


def test_outer_ge_shape():
    """外格（专旺·曲直）也能走同一端点，并带 open_issues。"""
    r = client.post("/api/charts/geju", json={
        "gender": "M", "calendar": "sizhu",
        "birth_pillars": {"year": "癸亥", "month": "乙卯",
                          "day": "乙未", "time": "壬午"},
    })
    assert r.status_code == 200, r.text
    y = r.json()["yuanju"]
    assert y["main_ge"]["category"] == "outer"
    assert y["main_ge"]["big_ge"] == "专旺格"
    assert y["open_issues"]
    assert y["gao_di"]["value"] in ("上", "中", "下", "未定")
