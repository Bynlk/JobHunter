# -*- coding: utf-8 -*-
"""
项目配置文件
包含数据库路径、爬虫参数、日志配置等
"""

import os

# ==================== 基础配置 ====================
# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库配置
DATABASE_PATH = os.path.join(BASE_DIR, 'job_aggregator.db')

# 日志配置
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'crawler.log')
APP_LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# ==================== 爬虫配置 ====================
# 实习僧爬虫配置
SHIXISENG_CONFIG = {
    'base_url': 'https://www.shixiseng.com/interns',
    'keywords': ['实习', '校招', '应届生'],  # 可配置的搜索关键词
    'max_pages': 5,  # 最大抓取页数
    'min_delay': 2,  # 最小延迟秒数
    'max_delay': 5,  # 最大延迟秒数
    'max_retries': 3,  # 最大重试次数
    'timeout': 60000,  # 页面加载超时（毫秒）
}

# 国家大学生就业服务平台配置
NCSS_CONFIG = {
    'base_url': 'https://www.ncss.cn/student/jobs/index.html',
    'max_pages': 5,
    'min_delay': 2,
    'max_delay': 5,
    'max_retries': 3,
    'timeout': 60000,
}

# 通用官网爬虫配置
WEBSITE_CONFIG = {
    'config_file': os.path.join(BASE_DIR, 'config', 'company_urls.json'),
    'min_delay': 3,  # 每家公司之间的最小延迟
    'max_delay': 8,  # 每家公司之间的最大延迟
    'max_retries': 2,  # 每个URL的最大重试次数
    'timeout': 60000,
    # 常见的岗位列表CSS选择器
    'job_list_selectors': [
        '.position-list',
        '.job-list',
        '.career-list',
        '.recruit-list',
        '.intern-list',
        '.positions-list',
        '.job-listing',
        '.career-opportunities',
        '[class*="position"]',
        '[class*="job"]',
        '[class*="career"]',
        '[class*="recruit"]',
    ],
    # 常见的岗位卡片选择器
    'job_card_selectors': [
        '.position-item',
        '.job-item',
        '.career-item',
        '.recruit-item',
        '.intern-item',
        '[class*="position-item"]',
        '[class*="job-item"]',
        '[class*="card"]',
        'li',
        'tr',
    ],
}

# ==================== Flask 应用配置 ====================
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5003,
    'debug': True,
}

# ==================== 分页配置 ====================
DEFAULT_PER_PAGE = 20  # 默认每页条数
MAX_PER_PAGE = 100  # 最大每页条数

# ==================== Excel 导出配置 ====================
EXPORT_CONFIG = {
    'max_rows': 10000,  # 单次导出最大行数
    'sheet_name': '岗位数据',
}

# ==================== 数据源标识 ====================
SOURCE_SHIXISENG = '实习僧'
SOURCE_NCSS = '国家平台'
SOURCE_WEBSITE = '官网'

# ==================== 岗位类型 ====================
JOB_TYPE_INTERN = 'intern'  # 实习
JOB_TYPE_GRADUATE = 'graduate'  # 校招
JOB_TYPE_ALL = 'all'  # 全部

# 岗位类型中文映射
JOB_TYPE_MAP = {
    'intern': '实习',
    'graduate': '校招',
}
