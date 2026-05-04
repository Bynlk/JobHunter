# 实习校招岗位聚合站

从多个真实招聘平台抓取 150+ 家大厂的实习岗位和校招岗位，在网页上展示、筛选、导出 Excel。

## 功能特性

- **多数据源抓取**：实习僧、国家大学生就业服务平台、150+ 大厂招聘官网
- **智能解析**：通用官网爬虫自动识别岗位列表，支持多种页面结构
- **实时进度**：抓取过程中实时显示进度和状态
- **多维筛选**：按关键词、公司、地点、类型、薪资、日期、来源筛选
- **分页浏览**：支持自定义每页条数和跳页
- **Excel 导出**：根据筛选条件导出格式化的 Excel 文件
- **数据去重**：基于 URL 唯一索引，自动更新已有数据

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.10+ / Flask |
| 前端 | HTML5 / Bootstrap 5 / Vue 3 (CDN) |
| 爬虫 | Playwright + playwright_stealth |
| 数据库 | SQLite |
| Excel | openpyxl |

## 快速开始

### 1. 创建虚拟环境

```bash
# 进入项目目录
cd job_aggregator

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 启动应用

```bash
python app.py
```

### 5. 访问页面

打开浏览器访问 `http://127.0.0.1:5003`

### 6. 抓取数据

点击页面右上角 **"抓取最新数据"** 按钮，选择数据源开始抓取：
- **全部数据源**：实习僧 + 国家平台 + 150+ 大厂官网（耗时较长）
- **实习僧**：抓取实习僧平台的实习和校招岗位
- **国家平台**：教育部官方平台，覆盖大量国企央企
- **150+ 大厂官网**：遍历配置文件中的大厂招聘官网（耗时最长）

## 项目结构

```
job_aggregator/
├── app.py                    # Flask 主应用，所有路由
├── config.py                 # 配置（数据库路径、爬虫页数、延迟时间等）
├── models.py                 # 数据库初始化、建表、CRUD 函数
├── crawler/
│   ├── __init__.py           # 爬虫模块初始化
│   ├── base_crawler.py       # 基础爬虫类：Playwright 浏览器管理
│   ├── shixiseng_crawler.py  # 实习僧爬虫类
│   ├── ncss_crawler.py       # 国家大学生就业服务平台爬虫类
│   └── website_crawler.py    # 通用官网爬虫类
├── config/
│   └── company_urls.json     # 150+ 大厂招聘官网 URL 列表
├── templates/
│   └── index.html            # 前端页面（Vue 3 + Bootstrap 5）
├── static/
│   ├── style.css             # 自定义样式
│   └── app.js                # Vue 应用逻辑
├── logs/                     # 日志目录
│   ├── app.log               # 应用日志
│   └── crawler.log           # 爬虫日志
├── requirements.txt          # Python 依赖
└── README.md                 # 项目说明
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 渲染首页 |
| GET | `/api/jobs` | 获取岗位列表（支持筛选和分页） |
| GET | `/api/jobs/<id>` | 获取单个岗位详情 |
| POST | `/api/crawl` | 启动爬虫任务 |
| GET | `/api/crawl/status` | 获取爬虫任务状态 |
| GET | `/api/export` | 导出 Excel |
| GET | `/api/companies` | 获取公司名称列表 |
| GET | `/api/stats` | 获取统计数据 |

### /api/jobs 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| keyword | string | 岗位关键词 |
| company | string | 公司名称 |
| location | string | 工作地点 |
| job_type | string | 岗位类型：intern/graduate/all |
| salary_min | int | 最低薪资 |
| salary_max | int | 最高薪资 |
| date_from | string | 开始日期 (YYYY-MM-DD) |
| date_to | string | 结束日期 (YYYY-MM-DD) |
| source | string | 数据来源（逗号分隔） |
| page | int | 页码（默认1） |
| per_page | int | 每页条数（默认20） |

## 配置说明

### config.py

- `SHIXISENG_CONFIG`：实习僧爬虫配置（页数、延迟、重试次数等）
- `NCSS_CONFIG`：国家平台爬虫配置
- `WEBSITE_CONFIG`：通用官网爬虫配置（CSS 选择器列表等）
- `DEFAULT_PER_PAGE`：默认每页条数
- `MAX_PER_PAGE`：最大每页条数

### config/company_urls.json

包含 150+ 家大厂的招聘官网 URL 配置，每个条目包含：
- `name`：公司全称
- `url`：校招或实习招聘页面 URL
- `industry`：行业分类
- `type`：类型（官网）
- `needs_verification`：URL 是否需要验证

## 常见问题

### Q: 抓取失败怎么办？

A: 可能原因：
1. 网站页面结构发生变化，需要调整爬虫中的 CSS 选择器
2. 遇到验证码或登录墙，爬虫会自动跳过并记录日志
3. 网络问题，爬虫会自动重试（最多3次）

### Q: 如何添加新的数据源？

A: 
1. 在 `crawler/` 目录下创建新的爬虫类，继承 `BaseCrawler`
2. 实现 `crawl()` 方法
3. 在 `app.py` 的 `run_crawler_task()` 函数中添加新数据源的调用逻辑

### Q: 如何添加新的公司？

A: 编辑 `config/company_urls.json`，按照现有格式添加新的公司配置。

### Q: 爬虫速度太慢？

A: 
- 可以在 `config.py` 中调整延迟时间（`min_delay` / `max_delay`）
- 可以减少 `max_pages` 配置
- 建议先抓取单一数据源测试，再抓取全部

### Q: 数据库在哪里？

A: SQLite 数据库文件 `job_aggregator.db` 位于项目根目录，首次运行时自动创建。

## 注意事项

- 本项目仅用于学习和研究目的
- 抓取间隔严格遵守，模拟人类浏览行为
- 不尝试绕过需要登录的页面
- 尊重各网站的 robots.txt 规则
- 数据来源于公开招聘信息，请勿用于商业用途

## 许可证

MIT License
