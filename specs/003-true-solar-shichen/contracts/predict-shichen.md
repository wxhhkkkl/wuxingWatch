# API Contract 增量：POST /api/predict（精确时辰）

**Feature**: specs/003-true-solar-shichen | **Date**: 2026-08-10

既有契约不变（仅新增可选字段与响应块，向后兼容）。`POST /api/image` 请求体同步接受新字段（图片内容本期不变）。

## 请求增量

```jsonc
// POST /api/predict  —— BirthInput 新增可选字段
{
  "calendar": "solar",
  "birth_date": "1990-06-21",
  "birth_time": "05:40",
  "birth_place": "北京",
  "longitude": 116.41,
  "latitude": 39.9,
  "timezone": "Asia/Shanghai",
  "precise_shichen": true        // 【新增】默认 false；四柱模式忽略
}
```

校验规则：
- `precise_shichen=true` 但 `calendar=sizhu`、`birth_time` 缺省、或经纬度缺失时，不报错——响应 `shichen.applied=false`（无法应用时退化，保持排盘可用）
- 其余校验不变

## 响应增量

```jsonc
{
  // ……既有字段不变……
  "shichen": {                    // 【新增】经纬度齐全且非四柱模式时必返回
    "applied": true,              // 用户开启且成功应用
    "fallback": false,            // true = 极昼/极夜均分回退
    "shichen": "卯",              // 精确法归属时辰（applied=false 时仍给出参考值）
    "traditional_shichen": "卯",  // 现有均分规则时辰（对比小字，FR-013）
    "segment_index": 7,           // 出生落入的小段 0–23
    "day_offset": 0,              // +1 = 夜子时，日柱按次日
    "moments": {
      "sunrise": "1990-06-21T04:46:00",
      "sunset": "1990-06-21T19:46:00",
      "solar_noon": "1990-06-21T12:16:00",
      "solar_midnight": "1990-06-22T00:16:00",
      "prev_sunrise": "1990-06-20T04:46:00",
      "prev_noon": "1990-06-20T12:16:00",
      "prev_sunset": "1990-06-20T19:46:00",
      "next_sunrise": "1990-06-22T04:46:00"
    },
    "segments": [                 // 恰 24 段，前闭后开，按太阳高度角等分
      { "index": 0, "start": "1990-06-21T04:46:00", "end": "1990-06-21T05:58:00", "shichen": "卯", "alt_start": 0.0, "alt_end": 12.4 }
      // ……共 24 项；alt_start/alt_end 为视高度角（度），极区回退时为 null……
    ]
  }
}
```

错误与边界：
- 极昼/极夜：`moments.sunrise`/`sunset` 为 null，`fallback=true`，segments 为 24×1h 均分
- 夜子时：`day_offset=1`，`pillars.day`/`day_master` 已为次日值，详情页据此提示换日规则
- 经纬度缺失或四柱模式：响应不含 `shichen` 键（前端隐藏入口与开关）

## 前端路由契约

- `GET /shichen`（SPA 路由）：读取 Pinia chart store 的 `result.shichen`；无数据时显示空态 + "去排盘"引导（不直接请求后端）
