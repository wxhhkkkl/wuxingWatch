# Quickstart: 移动端八字排盘工具

**Branch**: `001-bazi-mobile-tool` | **Date**: 2026-08-08

## 后端（FastAPI）

- 环境: Python 3.12+（建议 `uv` 管理）
- 安装与运行:
  ```bash
  cd backend
  uv sync                          # 安装依赖
  cp .env.example .env             # 配置 JWT_SECRET、SMS_* 等（见下）
  uv run uvicorn src.main:app --reload
  ```
- 测试（**测试先行**，新增功能先写失败测试）:
  ```bash
  uv run pytest                    # unit + contract + integration
  ```

## 前端（Vue 3）

- 环境: Node 20+，pnpm
- 安装与运行:
  ```bash
  cd frontend
  pnpm install
  pnpm dev                         # Vite dev server
  ```
- 测试:
  ```bash
  pnpm test:unit                   # Vitest + Vue Test Utils
  pnpm test:e2e                    # Playwright（可选）
  ```

## 关键环境变量（后端 .env）

| 变量 | 说明 |
|------|------|
| `JWT_SECRET` | 令牌签名密钥（必填，生产环境用强随机值） |
| `ACCESS_TOKEN_TTL` | 默认 900（秒，15 分钟） |
| `DATABASE_URL` | 默认 `sqlite:///wuxing.db` |
| `SMS_ACCESS_KEY` / `SMS_ACCESS_SECRET` | 阿里云短信凭证（本地可留空，SmsClient 走 stub） |
| `SMS_SIGN_NAME` / `SMS_TEMPLATE_CODE` | 已审核的短信签名与模板 |

## 依赖前提

- 阿里云短信：企业实名认证 + 签名备案（运营商审核约 5–7 个工作日）+ 模板审核后，短信才可实际发出；开发期用 stub。
- 出生地点解析：需要一份中国省市/城市→经纬度数据（实现时选轻量内置数据，见 data-model.md `longitude/latitude`）。

## 本地自测流程

1. 启动后端与前端。
2. 首页输入公历或农历出生信息排盘 → 校验四柱、大运、流年、喜忌（对照 SC-002 用已知命例抽检）。
3. 手机号登录 → 保存记录 → "我的记录"列表/详情 → 生成命盘长图并检查中文渲染。
