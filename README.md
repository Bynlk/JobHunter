<div align="center">

# 🎯 JobHunter — 实习 & 校招岗位聚合平台

**一站式聚合多平台实习/校招信息，智能筛选、实时抓取、一键导出**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ✨ 项目简介

**JobHunter** 是一个面向应届毕业生和实习生的岗位信息聚合工具。它能自动从多个招聘平台抓取岗位数据，提供强大的多维筛选和 Excel 导出功能，帮助你高效找到心仪的工作机会。

> 💡 告别在多个招聘网站之间反复切换的烦恼，一个平台搞定所有信息！

## 🚀 功能亮点

| 功能 | 说明 |
|:-----|:-----|
| 🌐 **多数据源聚合** | 实习僧（170+ 条/次）、国家大学生就业服务平台（100 条/页）、198 家大厂官网（⚠️ 反爬严重，见下方说明）、API 接口直连（13 家大厂） |
| 🔌 **API 直连** | 阿里巴巴、腾讯、字节跳动、美团、京东、小红书、科大讯飞、滴滴、网易、哔哩哔哩、百度、快手、大疆 |
| 🤖 **自动检测** | 爬虫自动监听网络请求，识别并提取未配置公司的岗位 API |
| ⚡ **实时抓取** | 边抓边入库，前端每 2 秒自动刷新，无需等待抓取完成 |
| 📋 **详情丰富** | 自动访问详情页获取薪资、描述、学历、行业、公司性质、福利标签 |
| 🔍 **多维筛选** | 关键词、公司、地点、岗位类型、薪资范围、日期、数据来源、行业、公司性质、学历要求 |
| 📊 **统计面板** | 实时显示各来源数据量 |
| 📥 **Excel 导出** | 按筛选条件导出格式化 Excel（含 15 列完整字段） |
| 🔄 **数据去重** | 基于 URL 唯一索引，重复抓取自动更新 |

## ⚠️ 关于大厂官网爬虫

**坦白说：大厂官网爬虫目前基本抓不到数据。** 大部分大厂招聘网站都有非常完善的反爬机制（动态渲染、接口加密、验证码、IP 封禁等），仅靠通用的 CSS 选择器匹配很难稳定获取数据。目前 `company_urls.json` 中配置了 198 家公司的官网链接，但实际能成功抓取的寥寥无几。

**如果你需要大厂岗位信息，建议优先使用「API 接口」数据源**，已对接 13 家大厂的 JSON API，数据质量更稳定。

## 🤝 社区共建 — 需要你的帮助！

一个人的精力有限，我实在没有太多空闲时间去逐一维护每家公司的爬虫逻辑。**如果你有以下任何一种能力，非常欢迎提交 PR：**

- **补充大厂招聘官网链接** — 在 `config/company_urls.json` 中添加新的公司 URL
- **贡献针对性爬虫** — 为特定大厂编写专用爬虫（解析其独特的页面结构或 API）
- **修复失效爬虫** — 网站改版后更新选择器和解析逻辑
- **分享 API 接口** — 如果你发现了某家公司的公开招聘 API，欢迎贡献

### 如何贡献

1. Fork 本仓库
2. 在 `crawler/` 下编写爬虫（继承 `BaseCrawler`）或在 `config/company_urls.json` 中补充链接
3. 提交 PR，简要说明爬取的是哪家公司、测试结果

> 众人拾柴火焰高，每一条链接、每一行爬虫代码都是对求职者的帮助 🙏

## 🛠️ 技术栈

<table>
  <tr>
    <td><strong>后端</strong></td>
    <td>Python 3.10+ / Flask 3.0</td>
  </tr>
  <tr>
    <td><strong>前端</strong></td>
    <td>Vue 3 (CDN) / Bootstrap 5</td>
  </tr>
  <tr>
    <td><strong>爬虫引擎</strong></td>
    <td>Playwright + playwright-stealth（反检测）</td>
  </tr>
  <tr>
    <td><strong>数据库</strong></td>
    <td>SQLite（WAL 模式，高并发读写）</td>
  </tr>
  <tr>
    <td><strong>Excel 导出</strong></td>
    <td>openpyxl</td>
  </tr>
</table>

## 📦 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/JobHunter.git
cd JobHunter
```

### 2. 创建虚拟环境 & 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 安装浏览器引擎

```bash
playwright install chromium
```

### 4. 启动服务

```bash
python app.py
```

访问 **http://127.0.0.1:5003** 即可使用 🎉

## 📖 使用指南

```
┌─────────────────────────────────────────────────────┐
│  1️⃣  选择数据源  →  实习僧 / 国家平台 / API接口 / 全部  │
│  2️⃣  点击「开始抓取」→  岗位列表实时更新             │
│  3️⃣  使用侧边栏筛选  →  精准定位目标岗位            │
│  4️⃣  点击「导出 Excel」→  下载筛选后的数据          │
└─────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
JobHunter/
├── app.py                      # Flask 主应用 + API 路由
├── config.py                   # 全局配置（爬虫参数、数据库路径等）
├── models.py                   # SQLite 数据库层（CRUD 操作）
├── requirements.txt            # Python 依赖清单
│
├── crawler/                    # 爬虫模块
│   ├── base_crawler.py         # 爬虫基类（Playwright 管理、重试机制、回调）
│   ├── shixiseng_crawler.py    # 实习僧爬虫
│   ├── ncss_crawler.py         # 国家大学生就业服务平台爬虫（JSON API）
│   ├── website_crawler.py      # 198 家大厂官网通用爬虫（HTML 解析）
│   └── api_crawler.py          # API 接口爬虫（13 家大厂 JSON API 直连）
│
├── detect_apis.py              # 自动化 API 检测脚本
│
├── config/
│   ├── company_urls.json       # 大厂招聘页面 URL 配置（198 家）
│   └── api_detection_results.json  # API 检测结果
│
├── templates/
│   └── index.html              # 前端页面（Vue 3 + Bootstrap 5）
│
└── static/
    ├── style.css               # 自定义样式
    └── app.js                  # Vue 应用逻辑
```

## 🔌 API 接口

<details>
<summary><strong>点击展开完整 API 文档</strong></summary>

### 岗位相关

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| `GET` | `/api/jobs` | 岗位列表（支持筛选 + 分页） |
| `GET` | `/api/jobs/<id>` | 单个岗位详情 |
| `GET` | `/api/companies` | 公司列表 |
| `GET` | `/api/industries` | 行业列表 |
| `GET` | `/api/stats` | 统计数据 |

### 爬虫相关

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| `POST` | `/api/crawl` | 启动爬虫（body: `{"source":"shixiseng"}`） |
| `GET` | `/api/crawl/status` | 爬虫运行状态 |

### 数据导出

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| `GET` | `/api/export` | 导出 Excel（查询参数同 `/api/jobs`） |

### `/api/jobs` 查询参数

| 参数 | 类型 | 说明 | 示例 |
|:-----|:-----|:-----|:-----|
| `keyword` | string | 岗位关键词 | `python` |
| `company` | string | 公司名 | `腾讯` |
| `location` | string | 工作地点 | `北京` |
| `job_type` | string | 岗位类型 | `intern` / `graduate` / `all` |
| `salary_min` | int | 最低薪资 (K) | `10` |
| `salary_max` | int | 最高薪资 (K) | `30` |
| `date_from` | string | 起始日期 | `2026-01-01` |
| `date_to` | string | 截止日期 | `2026-05-01` |
| `source` | string | 数据来源 | `实习僧,国家平台,官网,api` |
| `industry` | string | 行业分类 | `互联网` |
| `company_nature` | string | 公司性质 | `民营企业` / `国有企业` / `外资企业` |
| `education` | string | 学历要求 | `本科` |
| `page` | int | 页码 | `1` |
| `per_page` | int | 每页条数 | `20` |

</details>

## 📊 数据字段说明

| 字段 | 来源 | 说明 |
|:-----|:-----|:-----|
| `job_title` | 列表页 | 岗位名称 |
| `company_name` | 列表页 | 公司名称 |
| `location` | 列表页 | 工作城市 |
| `salary` | 详情页 | 薪资（如 "150-200/天"） |
| `job_type` | 推断 | `intern`=实习 / `graduate`=校招 |
| `education` | 详情页/API | 学历要求 |
| `industry` | 详情页/API | 行业分类 |
| `company_nature` | 详情页/API | 公司性质（国企/民企/外企） |
| `company_size` | 详情页 | 公司规模 |
| `welfare` | 详情页 | 福利标签 |
| `publish_date` | 详情页/API | 发布日期 |
| `job_desc` | 详情页 | 岗位描述 |
| `source` | 爬虫 | 数据来源 |

## ⚙️ 配置说明

编辑 [`config.py`](config.py) 可调整以下参数：

| 配置项 | 说明 | 默认值 |
|:-------|:-----|:-------|
| `max_pages` | 每个关键词抓取页数 | `5` |
| `min_delay` / `max_delay` | 请求间隔（秒） | `2` / `5` |
| `timeout` | 页面加载超时（毫秒） | `60000` |
| `DEFAULT_PER_PAGE` | 默认每页条数 | `20` |

## ⚠️ 免责声明

- 本项目仅用于 **学习和研究目的**
- 请求间隔严格遵守，模拟人类浏览行为
- 尊重各网站 `robots.txt` 规则
- 所有数据来源于公开招聘信息

## 📄 License

[MIT License](LICENSE) © 2026
