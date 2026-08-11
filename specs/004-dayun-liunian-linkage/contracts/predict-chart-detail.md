# API Contract 增量：POST /api/predict（四柱明细 + 大运流年联动数据）

**Feature**: specs/004-dayun-liunian-linkage | **Date**: 2026-08-11

既有契约不变——**仅新增字段**（向后兼容，旧客户端忽略新键即可）。请求体无任何变化；`POST /api/image`、`POST/PUT /api/records` 因复用同一 chart_result 结构自动获得新字段。

## 响应增量

```jsonc
{
  // ……既有字段不变……
  "pillars": {
    "year": {
      // 既有：ganzhi/gan/zhi/gan_wuxing/zhi_wuxing/shishen
      "detail": {                    // 【新增】PillarDetail；时辰不详的 time 柱无此键
        "gan_shishen": "正官",       // 主星（日柱为 "日主"）
        "zhi_shishen": "正财",       // 地支十神（本气）
        "cang_gan": [                // 藏干 + 十神
          {"gan": "乙", "shishen": "正财"}
        ],
        "xing_yun": "胎",            // 星运：日主临该支十二长生（阳顺阴逆）
        "zi_zuo": "病",              // 自坐：本柱干坐本支
        "xun_kong": "戌亥",          // 空亡：该柱自身旬空
        "na_yin": "炉中火",
        "shen_sha": ["太极贵人", "飞刃"]   // 可空数组
      }
    }
    // month/day/time 同构
  },
  "da_yun": {
    "start_age": 8, "start_month": 6,   // 既有
    "steps": [{
      "ganzhi": "甲辰", "start_year": 1995, "end_year": 2005,  // 既有
      "gan": "甲", "zhi": "辰",            // 【新增】
      "gan_shishen": "正财", "zhi_shishen": "偏印",  // 【新增】
      "start_age_xu": 9,                  // 【新增】起始虚岁；四柱模式为 null
      "detail": { /* PillarDetail 同构 */ },          // 【新增】大运柱明细
      "liu_nian": [{                      // 【新增】该运逐年（start_year ≤ y ≤ end_year，含端点通常 10 个）；四柱模式无此键
        "year": 1995, "gan": "乙", "zhi": "亥", "ganzhi": "乙亥",
        "gan_shishen": "伤官", "zhi_shishen": "劫财",
        "detail": { /* PillarDetail 同构 */ }
      }]
    }]
  },
  "liu_nian": [ /* 既有"当前年+10年"列表保留不动（兼容旧前端）；联动数据以 da_yun.steps[*].liu_nian 为准 */ ]
}
```

## 规则

- 所有 PillarDetail 均以**日主**为十神/星运基准；十二长生阳顺阴逆
- `xun_kong` 恒为 2 字符；`shen_sha` 为空数组而非 null
- 时辰不详：`pillars.time = null`（既有行为），无 detail
- 四柱输入模式：`steps[*].start_year/end_year/start_age_xu/liu_nian` 为 null/缺省，`detail` 仍返回（干支已知即可算）
- 响应体积增量 <50KB；无新端点、无请求参数变化
