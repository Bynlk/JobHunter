# CLAUDE.md

本文件为 Claude Code 提供项目上下文和开发规范。

## 项目概述

JobHunter — 中文实习/校招岗位聚合平台。从多个数据源抓取岗位信息，存入 SQLite，通过 Flask + Vue 3 SPA 提供查询和管理界面。

## 快速启动

```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python app.py                  # Flask 开发服务器 http://0.0.0.0:5003
```

无测试套件，通过 Web UI 和 API 手动验证。

## 项目结构

```
├── app.py                    # Flask 应用：所有 REST API 路由 + 爬虫线程管理
├── config.py                 # 全局配置：数据库路径、爬虫参数、Flask 设置、地区/行业编码映射
├── models.py                 # SQLite 数据层：建表、CRUD、查询构建、导出
├── crawler/
│   ├── __init__.py           # 导出 BaseCrawler, ShixisengCrawler, NCSSCrawler, WebsiteCrawler
│   ├── base_crawler.py       # 抽象基类：Playwright 生命周期、stealth 模式、重试、日期解析
│   ├── shixiseng_crawler.py  # 实习僧 HTML 爬虫（含反爬字体破解）
│   ├── ncss_crawler.py       # 国家平台 JSON API 爬虫（浏览器内执行 fetch）
│   └── website_crawler.py    # 通用官网爬虫（遍历 company_urls.json 中的公司）
├── config/
│   └── company_urls.json     # 198 家公司招聘官网 URL 及元数据
├── templates/
│   └── index.html            # Jinja2 模板，承载 Vue 3 SPA（用 {% raw %} 避免 {{ }} 冲突）
├── static/
│   ├── app.js                # Vue 3 Composition API — 全部前端逻辑（851 行）
│   └── style.css             # Glassmorphism CSS 设计
└── requirements.txt          # Flask, playwright, playwright-stealth, openpyxl
```

## 核心架构

### 数据流

```
用户点击抓取 → POST /api/crawl → 启动 daemon 线程 → 爬虫实例化
    → 每页抓取后调用 jobs_callback → batch_insert_jobs() 实时入库
    → progress_callback 更新 crawl_status 字典（线程锁保护）
    → 前端每 2s 轮询 GET /api/crawl/status 更新 UI
```

### 爬虫类层次

- [`BaseCrawler`](crawler/base_crawler.py:22) — 抽象基类，提供：
  - Playwright 浏览器管理（`start_browser()` / `close_browser()`）
  - stealth 反检测（`playwright-stealth`）
  - 随机延迟（`random_delay()`）、重试逻辑（`retry()`）
  - 回调注入：`set_progress_callback()`、`set_jobs_callback()`、`set_stop_check()`
  - 子类必须实现 `crawl(filters=None)` 方法
- [`ShixisengCrawler`](crawler/shixiseng_crawler.py:17) — 实习僧，HTML 解析 + 动态字体 glyph 映射破解
- [`NCSSCrawler`](crawler/ncss_crawler.py:16) — 国家平台，在浏览器上下文中执行 `fetch()` 调用 JSON API
- [`WebsiteCrawler`](crawler/website_crawler.py:19) — 通用官网，智能 CSS 选择器匹配岗位列表

### 数据库

- SQLite，WAL 模式，`job_url` 字段有 UNIQUE 约束
- [`batch_insert_jobs()`](models.py:186) 执行 INSERT OR UPDATE（upsert）
- Schema 迁移：内联 `ALTER TABLE ADD COLUMN` + `try/except`，无迁移框架
- 关键索引：`job_url`, `company_name`, `source`, `job_type`, `publish_date`

### 前端

- Vue 3 从 CDN 加载，无构建步骤
- [`static/app.js`](static/app.js:1) — 单文件 Composition API，包含全部状态管理、筛选、分页
- [`templates/index.html`](templates/index.html:1) — Jinja2 模板，用 `{% raw %}` 包裹 Vue 模板语法
- 弹窗系统：`showSettingsModal`（爬虫设置）、`showTargetedModal`（定向抓取）、`showCompanyModal`（公司列表）— 各弹窗必须是独立的顶层 `v-if` 块，不能嵌套

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 渲染首页 |
| GET | `/api/jobs` | 分页岗位列表，支持 keyword/company/location/job_type/salary_min/salary_max/date_from/date_to/source/industry/page/per_page 筛选 |
| GET | `/api/jobs/<id>` | 单条岗位详情 |
| POST | `/api/jobs/clear` | 清空所有数据 |
| POST | `/api/crawl` | 启动爬虫任务，body: `{source, filters?}` |
| GET | `/api/crawl/status` | 轮询爬虫进度 |
| POST | `/api/crawl/stop` | 停止爬虫 |
| GET | `/api/crawl/industries` | 定向抓取可选行业列表 |
| GET | `/api/crawl/companies` | 定向抓取可选公司列表 |
| GET | `/api/export` | Excel 导出（同 /api/jobs 筛选参数） |
| GET | `/api/companies` | 已有数据中的公司列表 |
| GET | `/api/companies/config` | company_urls.json 中的公司配置 |
| GET | `/api/industries` | 已有数据中的行业列表 |
| GET | `/api/locations` | 已有数据中的地点列表 |
| GET | `/api/stats` | 聚合统计（总数、公司数、数据源分布） |
| GET | `/api/config` | 获取运行时爬虫配置 |
| POST | `/api/config` | 更新运行时爬虫配置 |

## 关键常量（config.py）

- 数据源标识：`SOURCE_SHIXISENG = '实习僧'`、`SOURCE_NCSS = '国家平台'`、`SOURCE_WEBSITE = '官网'`
- 岗位类型：`JOB_TYPE_INTERN = 'intern'`、`JOB_TYPE_GRADUATE = 'graduate'`、`JOB_TYPE_ALL = 'all'`
- NCSS 地区编码：`NCSS_AREA_CODES` 字典（省-市 → 6位行政区划代码）
- NCSS 行业编码：`NCSS_INDUSTRY_CODES` 字典（行业名 → 2位代码）

## 开发规范

### 编码原则

1. **简单优先** — 只写解决问题所需的最少代码，不做预设性扩展
2. **外科手术式修改** — 只改必须改的内容，保持现有代码风格，不顺手优化
3. **目标驱动** — 先定义成功标准，再循环推进直到验证通过

### 项目特定规则

- 所有 UI 文本使用中文
- 爬虫在 daemon 线程中运行，通过回调推送数据，不要在爬虫中直接操作数据库
- 新增爬虫：继承 `BaseCrawler`，实现 `crawl(filters=None)`，在 `__init__.py` 中导出，在 `app.py` 的 `run_crawler_task()` 中注册
- 前端弹窗必须是独立的顶层 `v-if` 块，不能嵌套在其他弹窗的 `v-if` 块内
- SQLite schema 变更：在 `init_database()` 中用 `ALTER TABLE ADD COLUMN` + `try/except`
- 爬虫配置可通过 `/api/config` 动态修改，运行时存储在 `app.py` 的 `runtime_config` 字典中
- 爬虫状态通过 `crawl_status` 字典管理，所有读写必须经过 `crawl_status_lock` 线程锁

### 常见陷阱

- Jinja2 和 Vue 3 的 `{{ }}` 冲突：HTML 模板中 Vue 表达式必须在 `{% raw %}` 块内
- Playwright 需要先 `playwright install chromium` 安装浏览器
- 实习僧使用动态字体反爬，需要通过 fonttools 解析 glyph 映射
- NCSS 爬虫在浏览器上下文中执行 JS fetch，不是直接 HTTP 请求
- `job_url` 有 UNIQUE 约束，重复 URL 会触发 upsert 而非报错
