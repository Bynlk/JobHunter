# 实习 & 校招岗位聚合站

从多个招聘平台抓取实习和校招岗位数据，提供侧边栏多维筛选、实时抓取进度、Excel 导出等功能。

## 功能特性

- **多数据源**：实习僧（170+ 条/次）、国家大学生就业服务平台（100 条/页）、198 家大厂官网
- **实时抓取**：边抓边入库，前端每 2 秒自动刷新，无需等待抓取完成
- **详情丰富**：自动访问详情页获取薪资、描述、学历、行业、公司性质、福利标签
- **侧边栏筛选**：关键词、公司、地点、岗位类型、薪资范围、日期、数据来源、行业、公司性质、学历要求
- **统计面板**：实时显示各来源数据量
- **Excel 导出**：按筛选条件导出格式化 Excel（含 15 列完整字段）
- **数据去重**：基于 URL 唯一索引，重复抓取自动更新

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.10+ / Flask |
| 前端 | Vue 3 (CDN) / Bootstrap 5 |
| 爬虫 | Playwright + playwright-stealth |
| 数据库 | SQLite (WAL mode) |
| Excel | openpyxl |

## 快速开始

```bash
# 克隆项目
git clone <repo-url>
cd job_aggregator

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 安装浏览器引擎
playwright install chromium

# 启动
python app.py
```

访问 `http://127.0.0.1:5003`

## 使用方式

1. 打开页面，左侧侧边栏选择数据源（实习僧 / 国家平台 / 全部）
2. 点击「开始抓取」，右侧岗位列表实时更新
3. 使用侧边栏筛选条件缩小结果
4. 点击「导出 Excel」下载数据

## 项目结构

```
job_aggregator/
├── app.py                    # Flask 主应用 + API 路由
├── config.py                 # 全局配置
├── models.py                 # SQLite 数据库层
├── crawler/
│   ├── base_crawler.py       # 爬虫基类（Playwright 管理、重试、回调）
│   ├── shixiseng_crawler.py  # 实习僧爬虫
│   ├── ncss_crawler.py       # 国家平台爬虫（JSON API）
│   └── website_crawler.py    # 198 家大厂官网通用爬虫
├── config/
│   └── company_urls.json     # 大厂招聘 URL 配置
├── templates/
│   └── index.html            # 前端页面
├── static/
│   ├── style.css             # 样式
│   └── app.js                # Vue 应用逻辑
├── requirements.txt
└── README.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/jobs` | 岗位列表（支持筛选 + 分页） |
| GET | `/api/jobs/<id>` | 单个岗位详情 |
| POST | `/api/crawl` | 启动爬虫（body: `{"source":"shixiseng"}`） |
| GET | `/api/crawl/status` | 爬虫状态 |
| GET | `/api/export` | 导出 Excel（参数同 /api/jobs） |
| GET | `/api/companies` | 公司列表 |
| GET | `/api/industries` | 行业列表 |
| GET | `/api/stats` | 统计数据 |

### /api/jobs 查询参数

| 参数 | 说明 | 示例 |
|------|------|------|
| keyword | 岗位关键词 | `python` |
| company | 公司名 | `腾讯` |
| location | 地点 | `北京` |
| job_type | 类型 | `intern` / `graduate` / `all` |
| salary_min | 最低薪资(K) | `10` |
| salary_max | 最高薪资(K) | `30` |
| date_from | 起始日期 | `2026-01-01` |
| date_to | 截止日期 | `2026-05-01` |
| source | 来源 | `实习僧,国家平台` |
| industry | 行业 | `互联网` |
| company_nature | 公司性质 | `民营企业` / `国有企业` / `外资企业` |
| education | 学历 | `本科` |
| page | 页码 | `1` |
| per_page | 每页条数 | `20` |

## 数据字段

| 字段 | 来源 | 说明 |
|------|------|------|
| job_title | 列表页 | 岗位名称 |
| company_name | 列表页 | 公司名称 |
| location | 列表页 | 工作城市 |
| salary | 详情页 | 薪资（如 "150-200/天"） |
| job_type | 推断 | intern=实习 / graduate=校招 |
| education | 详情页/API | 学历要求 |
| industry | 详情页/API | 行业分类 |
| company_nature | 详情页/API | 公司性质（国企/民企/外企） |
| company_size | 详情页 | 公司规模 |
| welfare | 详情页 | 福利标签 |
| publish_date | 详情页/API | 发布日期 |
| job_desc | 详情页 | 岗位描述 |
| source | 爬虫 | 数据来源 |

## 配置说明

编辑 `config.py` 调整：

- `max_pages`：每个关键词抓取页数
- `min_delay` / `max_delay`：请求间隔（秒）
- `timeout`：页面加载超时（毫秒）
- `DEFAULT_PER_PAGE`：默认每页条数

## 注意事项

- 仅用于学习和研究目的
- 请求间隔严格遵守，模拟人类浏览
- 尊重各网站 robots.txt
- 数据来源于公开招聘信息
