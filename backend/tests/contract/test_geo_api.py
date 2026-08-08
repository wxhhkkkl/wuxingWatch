"""地理模糊搜索端点契约测试（中英文）。"""


def test_geo_search_chinese(client):
    resp = client.get("/api/geo/search", params={"q": "北京"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(
        i["name"] == "北京市"
        and i["name_zh"] == "北京"
        and i["admin1_zh"] == "北京市"
        and i["timezone"] == "Asia/Shanghai"
        and i["longitude"] > 100
        for i in items
    )


def test_geo_search_english(client):
    resp = client.get("/api/geo/search", params={"q": "london"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["name"] == "London" and i["longitude"] < 0 for i in items)


def test_geo_search_empty_query(client):
    assert client.get("/api/geo/search").status_code == 422
