# Research: 移动端八字排盘工具

**Branch**: `001-bazi-mobile-tool` | **Date**: 2026-08-08
**Input**: Technical Context 中的未决项（/speckit-plan Phase 0，3 项并行研究）

## 1. 排盘引擎与历法库选型

- **Decision**: 采用 **lunar-python** 作为排盘核心库（四柱、节气定月、农历↔公历含闰月、大运顺逆排与起运岁数、胎元/命宫/身宫），自建 `hidden_stems.py`（人元司令）与 `xiyong.py`（喜忌，基于日主强弱）两个模块。
- **Rationale**: lunar-python 覆盖排盘所需的大部分计算，MIT 协议、活跃维护（2025 年仍持续发布）、零依赖；其 `getXiShen/getYongShen` 返回的是"方位"而非"日主强弱用神"，人元司令也无原生支持，故这两块为明确的自建边界。
- **Alternatives considered**:
  - sxtwl（寿星天文历）：节气分钟精度更高、日期范围更大（BC722–9999）、内置真太阳时；但十神/大运/宫位需全部自建，底层 C++ 继承许可需商用前核实。→ 仅作节气边界交叉校验的可选工具，不选为主库。
  - 完全自研干支算法：重复造轮子、节气/农历数据需长期维护，正确性风险高。→ 拒绝。

### 真太阳时

- **Decision**: `真太阳时 = 平太阳时 + 4分钟 × (经度 − 15 × 时区) + 均时差`。在 `solar_time.py` 中实现经度修正 + Spencer 近似均时差；经度由出生地点解析获得。
- **Rationale**: 中国境内经度修正可达 14–90 分钟、均时差 ±16 分钟，对近子时/节气交界的日柱、时柱判定影响显著，必须纳入（对齐 FR-002）。
- **Alternatives considered**: sxtwl 内置真太阳时 → 仅当以 sxtwl 为主库才划算；pvlib 库 → 依赖过重，单函数可替代。

### 大运起运约定（定稿）

- **Decision**: 起运按子平惯例"3 天折 1 岁、1 天折 4 个月"计算；结果页以实岁展示起运岁数并注明说明。
- **Rationale**: 消除虚岁/实岁歧义，保证 SC-002 抽检结果一致。

### 人元司令数据来源（定稿）

- **Decision**: 采用《子平真诠》司权天数表；结果页注明数据来源版本。

### 关键边界与注意

- lunar-python 日期范围 1900–2100；超范围提示"暂不支持"（与 spec 边界"超出 120 年"一致）。
- 子时/日柱分界可用 `setSect` 配置；大运起运采用虚岁/实岁的约定需在实现时固定并在结果页注明。
- 人元司令使用"司权天数"表（如寅月 戊7/丙7/甲16），需固定《三命通会》或《子平真诠》版本并在结果中注明数据来源。
- 月柱/日柱在节气交接邻近日需与权威排盘交叉校验（对应 SC-002 抽检 100 组 100%）。

## 2. 手机号 + 短信验证码登录

- **Decision**: **JWT 混合方案** —— 短时 access token（10–15 分钟，客户端内存持有，`Authorization: Bearer` 头）+ 长效不透明 refresh token（服务端哈希存储、HttpOnly Cookie 下发、每次刷新轮换并带重用检测）。
- **Rationale**: 前端是浏览器端移动 SPA，纯 JWT 存 localStorage 可被 XSS 读取；HttpOnly refresh cookie 实现"重启免登录"且 JS 不可读；服务端会话表支持即时吊销与按用户会话控制（对齐 FR-012 / SC-006 数据隔离）。
- **Alternatives considered**: 纯 opaque DB 会话令牌 → 更简单但每请求查库，作为可接受回退；纯 JWT 无刷新 → 无法吊销。→ 选混合方案。

### 短信服务商

- **Decision**: v1 采用 **阿里云短信**（验证码模板），包一层 `SmsClient` 接口以便测试 stub。
- **Rationale**: 阿里云按量付费（约 0.04–0.05 元/条），低/变动量更友好；腾讯云强制预付套餐。企业实名 + 签名备案（2025 年起需运营商审核，预留 5–7 个工作日）与模板审核需提前安排（依赖项）。
- **Alternatives considered**: 腾讯云短信 → 预付模式不灵活。→ 拒绝。

### 验证码规则与存储

- **Decision**: 6 位数字（`secrets` 生成），只存 HMAC-SHA256 哈希（含 pepper）；TTL 5 分钟；60 秒重发冷却；重发作废旧码；5 次尝试后作废；单次使用；发送侧限流（每手机 5 次/时、每 IP 10–20 次/时）+ 图形验证码防轰炸。
- **Rationale**: 哈希存储防拖库泄露明文；短 TTL 与限流平衡体验与安全（对齐 spec 边界"验证码获取过于频繁"）。
- **存储位置**: v1 单进程可用进程内存储；多实例上线后迁移 Redis。登录会话仍存 DB。
- **Alternatives considered**: OTP 存 DB → 需清理任务且不必要地持久化短期敏感数据。→ 进程内缓存。

### TDD 顺序（对齐原则 II）

先纯单元：验证码生成/OTP 存储（TTL、次数、单次使用）/令牌轮换与重用检测；再 API（TestClient + `app.dependency_overrides` stub 短信与 OTP 存储）：发送码（200/422/429 限流）、验证登录（成功/错码 401/5 次锁定/过期/重用）、受保护路由（无 token 401/有效 200/过期 401）、刷新重用检测吊销整族。

## 3. 前端 Vue 3 移动端架构与命盘长图

- **Decision**: 前端采用 **Vue 3.5 + Vite + Vue Router 4 + Pinia（+ persistedstate）+ Vant 4**，TypeScript，pnpm；测试用 **Vitest + Vue Test Utils**（组件）+ **Playwright**（E2E）。
- **Rationale**: 2026 年 Vue 移动端 H5 的主流成熟栈；Vant 提供表单、弹窗、选择器等移动组件，契合公历/农历输入表单与结果展示。
- **Alternatives considered**: 小程序/React → 超出用户指定技术栈（宪法原则 I）。→ 拒绝。

### 命盘长图生成

- **Decision**: **服务端生成（FastAPI + Pillow）**，捆绑开源 CJK 字体（Noto Sans SC / Source Han Sans；Pillow 默认字体不支持中文，必须加载 TTF）。
- **Rationale**: 客户端 html2canvas 在 iOS Safari 存在 `toDataURL()` 返回空图的已知缺陷，而微信用户中 iOS 占比高，风险不可接受；服务端 Pillow 渲染确定性强、中文一致、像素/DPI 可控（对齐 SC-008 清晰可读），且可纳入后端 TDD。
- **Alternatives considered**: 客户端 html2canvas/canvas → iOS 兼容风险 + 中文字体不一致；ReportLab → 面向 PDF。→ 服务端 Pillow。
