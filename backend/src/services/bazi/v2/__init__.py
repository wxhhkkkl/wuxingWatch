"""旺度引擎 v2 —— 原局旺度管线（原 012 期；2026-10-28 起只保留旺度）。

本包只负责：关系判定 → 通根/月令 → 静态旺度 → 生克结算 → 动态旺度与十一档定级，
并输出逐步依据。

**不含格局、喜忌、用神、调候**——这四类内容已按使用者要求从产品与计算链中移除。
大运旺度另由 `services.bazi.v2.dayun2`（引擎2）独立计算。

**书源与权威顺序（012 spec C26-1）**：书中内容冲突时，
《四柱精髓（上）/（下）》 > 《四柱预测学入门》；《初级答疑》不在权威链内。
"""

from __future__ import annotations


def wan_du_analysis(pillars: dict, *, hour_known: bool = True) -> dict:
    """**原局旺度**对外入口。

    只跑 `pipeline.compute_strength`（不传大运、不传流年），返回旺度契约：
    静态/动态五行合计、十一档等级、实例明细、关系判定与逐步依据。

    时辰不详时剔掉时柱，走三柱路径（`input_scope = "three_pillars"`）——
    上游仍会用一个午时占位柱排盘，若照单全收就永远走不到三柱路径。
    """
    from services.bazi.constants import GAN_WUXING
    from services.bazi.v2 import pipeline

    src = pillars
    if not hour_known:
        src = {k: (None if k == "time" else v) for k, v in pillars.items()}
    r = pipeline.compute_strength(src)
    dm = r["day_master"]
    return {
        "engine": "wangdu-v2",
        "contract_version": 2,
        "day_master": dm,
        "day_master_original": r["day_master_original"],
        "day_master_wuxing": GAN_WUXING.get(dm, ""),
        "input_scope": r["input_scope"],
        "degradations": r["degradations"],
        "relations": r["relations"],
        "degrees": r["degrees"],
        "static_scores": r["static_scores"],
        "final_scores": r["final_scores"],
        "level": r["level"],
        "stem_groups": r["stem_groups"],
        "day_master_group": r["day_master_group"],
        "benqi_instances": r["benqi_instances"],
        "steps": r["steps"],
    }


# ---------------------------------------------------------------
# 引擎口径版本
# ---------------------------------------------------------------

# 参与版本哈希的模块——**改了旺度口径就会变**的那几个。
_VERSION_MODULES = (
    "pipeline.py", "stem_he.py", "shengke.py", "degrees.py",
    "relations.py", "tables.py", "ban.py",
)
_version_cache: str | None = None


def engine_version() -> str:
    """**引擎口径版本**——核心模块源码的 sha1 前 12 位。

    用来判断一条**已保存的排盘记录**还算不算数：记录里存了当时的版本号，读的时候
    版本不符就重算（见 `api/routers/records.py`）。
    """
    import hashlib
    import pathlib

    global _version_cache
    if _version_cache is None:
        v2_dir = pathlib.Path(__file__).resolve().parent
        h = hashlib.sha1()
        for name in _VERSION_MODULES:
            try:
                h.update((v2_dir / name).read_bytes())
            except OSError:                      # 缺文件（打包/裁剪部署）就跳过
                continue
        _version_cache = h.hexdigest()[:12]
    return _version_cache
