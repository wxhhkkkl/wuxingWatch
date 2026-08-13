# API Contract 增量：xi_yong.strength（五行力量评分 + 强弱详情）

**Feature**: specs/005-wuxing-strength-scoring | **Date**: 2026-08-12

既有契约不变——**仅新增 `xi_yong.strength` 键**（向后兼容，旧客户端忽略新键即可）。请求体无任何变化；`POST /api/charts/predict`、`POST /api/charts/image`、`POST/PUT /api/records` 因复用同一 `chart_service.compute` 自动携带 strength。

## 响应增量

```jsonc
{
  // ……既有字段不变……
  "xi_yong": {
    "conclusion": {
      "yong_shen": "火",
      "xi_shen": ["土", "金"],
      "ji_shen": ["木", "水"],
      "summary": "偏旺"            // 【语义更新】= strength.level；旧记录仍为"身强/身弱"
    },
    "favorable_elements": ["火", "土"],
    "avoid_elements": ["木"],
    "reasoning": "日主乙属木……",   // 既有；可提及强弱等级
    "ten_gods": { "year": "正官", "month": "七杀", "day": "日主", "time": "七杀" },
    "direction": { "career": "...", "fortune": "...", "health": {}, "note": "..." },
    "disclaimer": "内容为算法生成的参考信息，仅供参考，不构成专业命理建议。",
    "strength": {                    // 【新增】StrengthVerdict；旧记录缺此键
      "level": "偏旺",               // 旺极/太旺/偏旺/中和/偏弱/太弱/从格
      "classification": "身强",      // 身强/身弱/中和/从格
      "cong_ge": false,
      "day_master": "乙",
      "day_master_wuxing": "木",
      "day_master_score": 132.4,     // 保留 1 位小数
      "balance_line": 109,
      "scores": { "木": 132.4, "火": 98.2, "土": 120.1, "金": 95.3, "水": 98.0 },  // 和≈544
      "steps": [
        { "title": "天干基础分", "description": "同五行透干 × 36", "values": { "木": 72 } },
        { "title": "地支藏干基础分", "description": "文档表 0 分值", "values": { "木": 120 } },
        { "title": "天干坐支修正", "description": "文档表 2（五类干支关系）", "values": { "木": 66 } },
        { "title": "天干间生克修正", "description": "文档表 3/4 + 距离修正", "values": { "火": 88 } },
        { "title": "有效根气（通根远近）", "description": "藏干分 × 距离 × 状态系数", "values": { "木": 96 } },
        { "title": "月令权重", "description": "文档表 5/6（月令系数）", "values": { "木": 1.2 } },
        { "title": "合冲刑会修正", "description": "文档表 7（结构系数）", "values": { "木": 1.0 } },
        { "title": "标准化", "description": "W ÷ ΣW × 544", "values": { "木": 132.4, "火": 98.2, "土": 120.1, "金": 95.3, "水": 98.0 } },
        { "title": "旺衰等级判定", "description": "日主分 132.4 ∈ 114~272 → 偏旺", "values": { "木": 132.4 } }
      ]
    }
  }
}
```

## 前端路由契约：`/strength`（强弱详情页）

- **入口**：ChartDisplay 喜忌区"强弱"标签（`xi_yong.strength` 存在时可点击）→ `router.push('/strength')`。
- **数据来源**：`chartStore.result.xi_yong.strength`（与时辰详解 `/shichen` 同模式；排盘后内存中必有，无需新接口）。
- **旧记录兜底**：`strength` 缺失 → 喜忌区标题回退 `conclusion.summary`，不渲染点击入口（FR-016）。
- **渲染**：逐步骤卡片渲染 `steps[]`（title/description/values 五行色值），顶部展示 等级/分类/日主分/五行分数横条。
- **返回**：`van-nav-bar` 左箭头 `router.back()`。

## 校验

- `scores` 五键之和 ∈ [543.5, 544.5]（浮点容差）。
- `level` ∈ {旺极, 太旺, 偏旺, 中和, 偏弱, 太弱, 从格}；`classification` ∈ {身强, 身弱, 中和, 从格}。
- `steps[8].title === "旺衰等级判定"`（末步），前端可据此判定详情完整性。
