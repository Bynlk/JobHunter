# -*- coding: utf-8 -*-
"""
爬虫模块初始化文件
导出所有爬虫类供外部使用
"""

from .base_crawler import BaseCrawler
from .shixiseng_crawler import ShixisengCrawler
from .ncss_crawler import NCSSCrawler
from .website_crawler import WebsiteCrawler

__all__ = ['BaseCrawler', 'ShixisengCrawler', 'NCSSCrawler', 'WebsiteCrawler']
