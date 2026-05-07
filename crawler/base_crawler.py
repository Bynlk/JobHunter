# -*- coding: utf-8 -*-
"""
基础爬虫类
提供 Playwright 浏览器管理、通用抓取方法、反爬策略等
所有具体爬虫类都应继承此类
"""

import logging
import random
import time
import re
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth

# 配置日志
logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """
    基础爬虫抽象类
    提供浏览器管理、页面操作、反爬策略等通用功能
    """
    
    def __init__(self, config):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置字典，包含 max_pages, min_delay, max_delay, max_retries, timeout 等
        """
        self.config = config
        self.max_pages = config.get('max_pages', 5)
        self.min_delay = config.get('min_delay', 2)
        self.max_delay = config.get('max_delay', 5)
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30000)
        
        # Playwright 相关对象
        self.playwright = None
        self.browser = None
        self.context = None
        
        # 抓取结果
        self.jobs = []
        
        # 进度回调函数
        self.progress_callback = None

        # 岗位数据回调函数（用于实时推送）
        self.jobs_callback = None

        # 停止检查函数（由外部注入）
        self._stop_check = None

        logger.info(f"爬虫初始化完成: {self.__class__.__name__}")
    
    def set_progress_callback(self, callback):
        """
        设置进度回调函数，用于向外部报告抓取进度

        Args:
            callback: 回调函数，接受 (message, total_new) 参数
        """
        self.progress_callback = callback

    def set_jobs_callback(self, callback):
        """
        设置岗位数据回调函数，用于实时推送抓取到的岗位

        Args:
            callback: 回调函数，接受 jobs_list 参数
        """
        self.jobs_callback = callback

    def set_stop_check(self, check_fn):
        """注入停止检查函数"""
        self._stop_check = check_fn

    def should_stop(self):
        """检查是否应该停止"""
        return self._stop_check() if self._stop_check else False

    def emit_jobs(self, jobs_list):
        """
        推送岗位数据到回调函数

        Args:
            jobs_list: 岗位数据列表
        """
        if jobs_list and self.jobs_callback:
            try:
                self.jobs_callback(jobs_list)
            except Exception as e:
                logger.error(f"推送岗位数据失败: {e}")
    
    def report_progress(self, message, total_new=0):
        """
        报告抓取进度
        
        Args:
            message: 进度描述信息
            total_new: 新增数据条数
        """
        if self.progress_callback:
            self.progress_callback(message, total_new)
        logger.info(f"[进度] {message}")
    
    def start_browser(self):
        """
        启动 Playwright 浏览器
        使用 Chromium 浏览器，启用 stealth 模式以规避反爬检测
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,  # 无头模式
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            # 创建浏览器上下文，模拟真实浏览器环境
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            logger.info("浏览器启动成功")
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise
    
    def close_browser(self):
        """
        关闭 Playwright 浏览器，释放资源
        """
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")
    
    def create_page(self):
        """
        创建一个新的浏览器页面，并应用 stealth 模式
        
        Returns:
            Page: Playwright 页面对象
        """
        page = self.context.new_page()
        # 应用 stealth 模式，隐藏自动化特征（playwright-stealth v2 API）
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        # 设置默认超时
        page.set_default_timeout(self.timeout)
        return page
    
    def random_delay(self, min_delay=None, max_delay=None):
        """
        随机延迟，模拟人类浏览行为
        
        Args:
            min_delay: 最小延迟秒数（默认使用配置值）
            max_delay: 最大延迟秒数（默认使用配置值）
        """
        min_d = min_delay or self.min_delay
        max_d = max_delay or self.max_delay
        delay = random.uniform(min_d, max_d)
        logger.debug(f"随机延迟 {delay:.1f} 秒")
        time.sleep(delay)
    
    def safe_goto(self, page, url, retries=None, wait_ms=3000):
        """
        安全地导航到指定 URL，支持自动重试

        Args:
            page: Playwright 页面对象
            url: 目标 URL
            retries: 最大重试次数（默认使用配置值）
            wait_ms: 页面加载后的额外等待时间（毫秒）

        Returns:
            bool: 是否成功加载页面
        """
        max_retries = retries or self.max_retries

        for attempt in range(max_retries):
            try:
                # 只等待 DOM 加载完成，不等 networkidle（现代 SPA 永远不会 idle）
                page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                # 固定等待页面渲染
                page.wait_for_timeout(wait_ms)
                logger.debug(f"成功加载页面: {url}")
                return True
            except Exception as e:
                logger.warning(f"加载页面失败 (尝试 {attempt + 1}/{max_retries}): {url} - {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    logger.error(f"页面加载最终失败: {url}")
                    return False
    
    def safe_click(self, page, selector, retries=3):
        """
        安全地点击元素，支持重试
        
        Args:
            page: Playwright 页面对象
            selector: CSS 选择器
            retries: 最大重试次数
        
        Returns:
            bool: 是否成功点击
        """
        for attempt in range(retries):
            try:
                page.click(selector, timeout=5000)
                return True
            except Exception as e:
                logger.debug(f"点击失败 (尝试 {attempt + 1}/{retries}): {selector} - {e}")
                if attempt < retries - 1:
                    time.sleep(1)
        return False
    
    def safe_wait_for_selector(self, page, selector, timeout=None):
        """
        安全地等待元素出现
        
        Args:
            page: Playwright 页面对象
            selector: CSS 选择器
            timeout: 超时时间（毫秒）
        
        Returns:
            bool: 元素是否出现
        """
        try:
            page.wait_for_selector(selector, timeout=timeout or self.timeout)
            return True
        except Exception as e:
            logger.debug(f"等待元素超时: {selector} - {e}")
            return False
    
    def extract_text(self, page, selector, default=''):
        """
        安全地提取元素文本内容
        
        Args:
            page: Playwright 页面对象
            selector: CSS 选择器
            default: 默认值
        
        Returns:
            str: 元素文本内容
        """
        try:
            element = page.query_selector(selector)
            if element:
                return element.inner_text().strip()
        except Exception as e:
            logger.debug(f"提取文本失败: {selector} - {e}")
        return default
    
    def extract_all_texts(self, page, selector):
        """
        提取所有匹配元素的文本内容
        
        Args:
            page: Playwright 页面对象
            selector: CSS 选择器
        
        Returns:
            list: 文本内容列表
        """
        try:
            elements = page.query_selector_all(selector)
            return [el.inner_text().strip() for el in elements if el.inner_text().strip()]
        except Exception as e:
            logger.debug(f"提取文本列表失败: {selector} - {e}")
            return []
    
    def extract_attribute(self, page, selector, attribute, default=''):
        """
        安全地提取元素属性值
        
        Args:
            page: Playwright 页面对象
            selector: CSS 选择器
            attribute: 属性名
            default: 默认值
        
        Returns:
            str: 属性值
        """
        try:
            element = page.query_selector(selector)
            if element:
                value = element.get_attribute(attribute)
                return value.strip() if value else default
        except Exception as e:
            logger.debug(f"提取属性失败: {selector}[{attribute}] - {e}")
        return default
    
    def extract_link(self, page, selector, base_url=''):
        """
        提取元素的链接地址，并处理相对路径
        
        Args:
            page: Playwright 页面对象
            selector: CSS 选择器
            base_url: 基础 URL，用于处理相对路径
        
        Returns:
            str: 完整的链接地址
        """
        href = self.extract_attribute(page, selector, 'href', '')
        if href and not href.startswith('http'):
            if base_url:
                href = base_url.rstrip('/') + '/' + href.lstrip('/')
        return href
    
    def parse_relative_date(self, date_text):
        """
        解析相对日期文本，转换为 YYYY-MM-DD 格式
        
        支持的格式：
        - "发布于 3 天前" / "3天前"
        - "发布于 1 周前" / "1周前"
        - "发布于 2 个月前" / "2个月前"
        - "今天" / "昨天"
        - "2024-01-15" / "2024/01/15"
        
        Args:
            date_text: 日期文本
        
        Returns:
            str: YYYY-MM-DD 格式的日期字符串，解析失败返回空字符串
        """
        if not date_text:
            return ''
        
        date_text = date_text.strip()
        today = datetime.now()
        
        # 处理"今天"
        if '今天' in date_text:
            return today.strftime('%Y-%m-%d')
        
        # 处理"昨天"
        if '昨天' in date_text:
            return (today - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 处理"X天前"
        days_match = re.search(r'(\d+)\s*天前', date_text)
        if days_match:
            days = int(days_match.group(1))
            return (today - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 处理"X周前"
        weeks_match = re.search(r'(\d+)\s*周前', date_text)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return (today - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        
        # 处理"X个月前"
        months_match = re.search(r'(\d+)\s*个月前', date_text)
        if months_match:
            months = int(months_match.group(1))
            # 简单处理，每月按30天计算
            return (today - timedelta(days=months * 30)).strftime('%Y-%m-%d')
        
        # 处理标准日期格式 YYYY-MM-DD
        date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_text)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 处理 MM-DD 格式（假设为当年）
        md_match = re.search(r'(\d{1,2})[-/](\d{1,2})', date_text)
        if md_match:
            month, day = md_match.groups()
            return f"{today.year}-{int(month):02d}-{int(day):02d}"
        
        logger.warning(f"无法解析日期: {date_text}")
        return ''
    
    def clean_text(self, text):
        """
        清理文本内容，去除多余空白和 HTML 标签
        
        Args:
            text: 原始文本
        
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ''
        
        # 去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    def check_captcha_or_login(self, page):
        """
        检测页面是否出现验证码或登录墙
        
        Args:
            page: Playwright 页面对象
        
        Returns:
            bool: True 表示遇到了验证码或登录墙
        """
        # 常见验证码和登录相关的关键词
        captcha_keywords = ['验证码', 'captcha', '滑块', '请登录', 'login', 'sign in', '人机验证']
        
        try:
            page_text = page.content().lower()
            for keyword in captcha_keywords:
                if keyword in page_text:
                    logger.warning(f"检测到验证码或登录墙: {keyword}")
                    return True
        except Exception:
            pass
        
        return False
    
    @abstractmethod
    def crawl(self):
        """
        执行抓取任务的抽象方法
        子类必须实现此方法
        
        Returns:
            list: 抓取到的岗位数据列表
        """
        pass
    
    def run(self):
        """
        运行爬虫的主入口方法
        负责启动浏览器、执行抓取、关闭浏览器
        
        Returns:
            list: 抓取到的岗位数据列表
        """
        self.jobs = []
        try:
            self.start_browser()
            self.jobs = self.crawl()
            logger.info(f"抓取完成，共获取 {len(self.jobs)} 条岗位数据")
        except Exception as e:
            logger.error(f"爬虫运行异常: {e}")
            raise
        finally:
            self.close_browser()
        
        return self.jobs
