# -*- coding: utf-8 -*-
"""
通用官网爬虫模块
读取 config/company_urls.json 配置文件，遍历150+家大厂的招聘官网
使用智能解析逻辑尝试抓取岗位信息
"""

import logging
import json
import re

from .base_crawler import BaseCrawler
from config import WEBSITE_CONFIG, SOURCE_WEBSITE

# 配置日志
logger = logging.getLogger(__name__)


class WebsiteCrawler(BaseCrawler):
    """
    通用官网爬虫类
    读取公司配置文件，遍历各公司招聘官网，智能解析岗位信息
    """
    
    def __init__(self):
        """初始化通用官网爬虫"""
        super().__init__(WEBSITE_CONFIG)
        self.config_file = WEBSITE_CONFIG['config_file']
        self.job_list_selectors = WEBSITE_CONFIG['job_list_selectors']
        self.job_card_selectors = WEBSITE_CONFIG['job_card_selectors']
        self.companies = []
    
    def load_companies(self):
        """
        从配置文件加载公司列表
        
        Returns:
            list: 公司配置列表
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.companies = json.load(f)
            logger.info(f"成功加载 {len(self.companies)} 家公司配置")
            return self.companies
        except Exception as e:
            logger.error(f"加载公司配置文件失败: {e}")
            return []
    
    def crawl(self):
        """
        执行通用官网爬虫的抓取任务
        
        遍历配置文件中的所有公司，逐一抓取其招聘官网的岗位信息
        
        Returns:
            list: 抓取到的岗位数据列表
        """
        all_jobs = []
        
        # 加载公司配置
        companies = self.load_companies()
        if not companies:
            logger.error("未加载到公司配置，无法执行抓取")
            return all_jobs
        
        total_companies = len(companies)
        
        for idx, company in enumerate(companies, 1):
            company_name = company.get('name', '未知公司')
            company_url = company.get('url', '')
            
            if not company_url:
                logger.warning(f"[{idx}/{total_companies}] {company_name} 未配置URL，跳过")
                continue
            
            logger.info(f"[{idx}/{total_companies}] 开始抓取: {company_name} - {company_url}")
            self.report_progress(
                f"[{idx}/{total_companies}] 正在抓取: {company_name}",
                len(all_jobs)
            )
            
            try:
                # 抓取单个公司的岗位
                company_jobs = self._crawl_company(company)
                if company_jobs:
                    all_jobs.extend(company_jobs)
                    self.emit_jobs(company_jobs)
                logger.info(f"[{idx}/{total_companies}] {company_name} 抓取到 {len(company_jobs)} 条岗位")
            except Exception as e:
                logger.error(f"[{idx}/{total_companies}] {company_name} 抓取异常: {e}")
                continue
            
            # 每家公司之间随机延迟
            if idx < total_companies:
                self.random_delay()
        
        logger.info(f"通用官网爬虫完成，共抓取 {len(all_jobs)} 条岗位数据")
        return all_jobs
    
    def _crawl_company(self, company):
        """
        抓取单个公司的招聘官网
        
        Args:
            company: 公司配置字典
        
        Returns:
            list: 该公司的岗位数据列表
        """
        company_name = company.get('name', '')
        company_url = company.get('url', '')
        industry = company.get('industry', '')
        
        jobs = []
        page = self.create_page()
        
        try:
            # 访问公司招聘页面
            if not self.safe_goto(page, company_url):
                logger.warning(f"无法加载页面: {company_url}")
                return jobs
            
            # 检查是否遇到验证码或登录墙
            if self.check_captcha_or_login(page):
                logger.warning(f"{company_name} 遇到验证码或登录墙，跳过")
                return jobs
            
            # 等待页面稳定
            self.random_delay(1, 3)
            
            # 尝试查找岗位列表
            job_elements = self._find_job_elements(page)
            
            if not job_elements:
                # 尝试滚动加载更多内容
                self._scroll_page(page)
                job_elements = self._find_job_elements(page)
            
            if not job_elements:
                logger.warning(f"{company_name} 未找到岗位列表，跳过")
                return jobs
            
            # 解析每个岗位
            for element in job_elements[:50]:  # 限制每个公司最多50条
                try:
                    job_data = self._parse_job_element(element, company_name, industry, company_url)
                    if job_data and job_data.get('job_title') and job_data.get('job_url'):
                        jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"解析岗位元素失败: {e}")
                    continue
            
            # 如果列表页没有详情链接，尝试进入详情页
            if jobs and not any(j.get('job_desc') for j in jobs):
                self._enrich_job_details(page, jobs[:30])  # 对前30条获取详情
            
        except Exception as e:
            logger.error(f"抓取 {company_name} 异常: {e}")
        finally:
            page.close()
        
        return jobs
    
    def _find_job_elements(self, page):
        """
        智能查找页面上的岗位列表元素
        
        尝试多种常见的 CSS 选择器来定位岗位列表
        
        Args:
            page: Playwright 页面对象
        
        Returns:
            list: 岗位元素列表
        """
        # 首先尝试常见的岗位列表容器选择器
        for list_selector in self.job_list_selectors:
            try:
                container = page.query_selector(list_selector)
                if container:
                    # 在容器内查找岗位卡片
                    for card_selector in self.job_card_selectors:
                        cards = container.query_selector_all(card_selector)
                        if cards and len(cards) >= 2:  # 至少2个才算有效列表
                            logger.debug(f"找到岗位列表: {list_selector} > {card_selector}, 共 {len(cards)} 个")
                            return cards
            except Exception:
                continue
        
        # 如果以上都没找到，尝试直接查找岗位卡片
        for card_selector in self.job_card_selectors:
            try:
                cards = page.query_selector_all(card_selector)
                if cards and len(cards) >= 3:
                    # 验证这些元素是否包含链接和文本，过滤广告
                    valid_cards = []
                    for card in cards[:30]:  # 只检查前30个
                        text = card.inner_text().strip()
                        has_link = card.query_selector('a[href]') is not None
                        if text and len(text) > 10 and has_link and not self._is_ad_element(card, text):
                            valid_cards.append(card)
                    
                    if len(valid_cards) >= 2:
                        logger.debug(f"直接找到岗位卡片: {card_selector}, 有效 {len(valid_cards)} 个")
                        return valid_cards
            except Exception:
                continue
        
        # 最后尝试通过链接模式查找
        try:
            # 查找包含 "job", "position", "career" 等关键词的链接
            link_patterns = [
                'a[href*="job"]', 'a[href*="position"]',
                'a[href*="career"]', 'a[href*="recruit"]',
                'a[href*="intern"]', 'a[href*="campus"]',
            ]
            
            for pattern in link_patterns:
                links = page.query_selector_all(pattern)
                if links and len(links) >= 3:
                    # 获取这些链接的父元素作为岗位卡片
                    parent_elements = []
                    for link in links[:20]:
                        parent = link.evaluate('el => el.parentElement')
                        if parent:
                            parent_elements.append(link)
                    
                    if len(parent_elements) >= 2:
                        logger.debug(f"通过链接模式找到岗位: {pattern}, 共 {len(parent_elements)} 个")
                        return parent_elements
        except Exception:
            pass
        
        return []
    
    def _scroll_page(self, page):
        """
        滚动页面以触发懒加载
        
        Args:
            page: Playwright 页面对象
        """
        for _ in range(5):
            page.evaluate('window.scrollBy(0, 800)')
            self.random_delay(0.5, 1)
    
    # 广告/推广相关关键词
    AD_KEYWORDS = [
        '广告', '推广', 'banner', 'ad-', '-ad', 'sponsor', 'promo',
        'hot-list', 'recommend', 'promotion', 'marketing-banner',
        'sidebar', 'footer', 'header', 'nav', 'menu', 'breadcrumb',
    ]

    def _is_ad_element(self, element, full_text):
        """
        判断元素是否为广告或非岗位内容

        Args:
            element: DOM 元素
            full_text: 元素文本

        Returns:
            bool: True 表示是广告
        """
        # 检查 class 和 id 是否包含广告关键词
        try:
            class_attr = element.get_attribute('class') or ''
            id_attr = element.get_attribute('id') or ''
            attrs = (class_attr + ' ' + id_attr).lower()

            for kw in self.AD_KEYWORDS:
                if kw in attrs:
                    return True

            # 检查是否包含广告链接模式
            links = element.query_selector_all('a[href]')
            for link in links:
                href = (link.get_attribute('href') or '').lower()
                if any(x in href for x in ['ad.', 'ads.', 'click.', 'track.', 'redirect.', 'banner']):
                    return True

            # 文本过短或过长都不像岗位卡片
            if len(full_text) < 5 or len(full_text) > 500:
                return True

            # 纯图片/无文本内容
            text_only = re.sub(r'\s+', '', full_text)
            if len(text_only) < 3:
                return True

        except Exception:
            pass

        return False

    def _parse_job_element(self, element, company_name, industry, base_url):
        """
        解析单个岗位元素，提取岗位信息

        使用多种策略智能提取字段

        Args:
            element: 岗位元素
            company_name: 公司名称
            industry: 行业
            base_url: 基础URL

        Returns:
            dict: 岗位数据字典，如果判定为广告则返回 None
        """
        job_data = {
            'job_title': '',
            'company_name': company_name,
            'location': '',
            'salary': '',
            'job_type': 'graduate',  # 默认为校招
            'education': '',
            'publish_date': '',
            'job_desc': '',
            'job_url': '',
            'source': SOURCE_WEBSITE,
        }

        # 获取元素的完整文本
        full_text = element.inner_text().strip()

        # 过滤广告元素
        if self._is_ad_element(element, full_text):
            return None

        # 提取岗位名称
        # 策略1: 查找标题元素
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5',
            '.title', '.name', '.job-title', '.position-name',
            '[class*="title"]', '[class*="name"]',
            'a',  # 链接文本通常是岗位名称
        ]

        for selector in title_selectors:
            el = element.query_selector(selector)
            if el:
                text = el.inner_text().strip()
                if text and len(text) < 100:  # 标题不应该太长
                    job_data['job_title'] = text
                    break

        # 如果没找到标题，使用元素的第一行文本
        if not job_data['job_title'] and full_text:
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            if lines:
                job_data['job_title'] = lines[0][:80]  # 限制长度
        
        # 提取工作地点
        location_patterns = [
            r'(北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|重庆|天津|苏州|长沙|郑州|青岛|大连|厦门|合肥|福州|济南|昆明|贵阳|南昌|太原|石家庄|哈尔滨|长春|沈阳|南宁|兰州|银川|西宁|乌鲁木齐|呼和浩特|拉萨|海口|三亚|珠海|东莞|佛山|中山|惠州|无锡|常州|徐州|宁波|温州|嘉兴|绍兴|金华|台州|泉州|漳州|龙岩|三明|南平|宁德|莆田|晋江|石狮|南安|惠安|安溪|永春|德化|金门|连江|罗源|闽清|永泰|平潭|长乐|福清|闽侯)',
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)',  # 英文城市名
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, full_text)
            if match:
                job_data['location'] = match.group(1)
                break
        
        # 提取薪资
        salary_patterns = [
            r'(\d+[kK]-\d+[kK])',
            r'(\d+-\d+[kK])',
            r'(\d+万-\d+万)',
            r'(\d+-\d+万)',
            r'(\d+元/月)',
            r'(\d+-\d+元/月)',
            r'(面议)',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                job_data['salary'] = match.group(1)
                break
        
        # 提取学历要求
        education_patterns = [
            r'(博士|硕士|本科|大专|高中|中专|不限)',
            r'(PhD|Master|Bachelor|Diploma)',
        ]
        
        for pattern in education_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                job_data['education'] = match.group(1)
                break
        
        # 提取发布时间
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{1,2}[-/]\d{1,2})',
            r'(\d+天前)',
            r'(\d+小时前)',
            r'(今天|昨天)',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, full_text)
            if match:
                job_data['publish_date'] = self.parse_relative_date(match.group(1))
                break
        
        # 提取详情链接
        link_el = element.query_selector('a[href]')
        if link_el:
            href = link_el.get_attribute('href')
            if href:
                # 处理相对路径
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    # 从 base_url 提取域名
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                elif not href.startswith('http'):
                    href = base_url.rstrip('/') + '/' + href.lstrip('/')
                job_data['job_url'] = href
        
        # 如果元素本身是链接
        if not job_data['job_url']:
            try:
                tag_name = element.evaluate('el => el.tagName.toLowerCase()')
                if tag_name == 'a':
                    href = element.get_attribute('href')
                    if href:
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif href.startswith('/'):
                            from urllib.parse import urlparse
                            parsed = urlparse(base_url)
                            href = f"{parsed.scheme}://{parsed.netloc}{href}"
                        elif not href.startswith('http'):
                            href = base_url.rstrip('/') + '/' + href.lstrip('/')
                        job_data['job_url'] = href
            except Exception:
                pass
        
        # 判断岗位类型
        title_lower = job_data.get('job_title', '').lower()
        full_text_lower = full_text.lower()
        if '实习' in title_lower or 'intern' in title_lower or '实习' in full_text_lower:
            job_data['job_type'] = 'intern'
        elif '校招' in title_lower or '应届' in title_lower or 'graduate' in title_lower:
            job_data['job_type'] = 'graduate'
        
        return job_data
    
    def _enrich_job_details(self, page, jobs):
        """
        为岗位列表补充详情描述
        
        访问每个岗位的详情页，提取完整的岗位描述
        
        Args:
            page: Playwright 页面对象（用于创建新页面）
            jobs: 岗位数据列表
        """
        for job in jobs:
            if self.should_stop():
                break
            if not job.get('job_url') or job.get('job_desc'):
                continue
            
            try:
                detail_page = self.create_page()
                
                try:
                    if self.safe_goto(detail_page, job['job_url']):
                        # 查找详情内容
                        detail_selectors = [
                            '.job-detail', '.detail-content', '.job-desc',
                            '.position-detail', '.job-content', '.content',
                            '[class*="detail"]', '[class*="desc"]',
                            'article', 'main',
                        ]
                        
                        for selector in detail_selectors:
                            detail_el = detail_page.query_selector(selector)
                            if detail_el:
                                text = detail_el.inner_text().strip()
                                if len(text) > 50:
                                    job['job_desc'] = self.clean_text(text[:3000])
                                    break
                        
                        # 如果没找到详情，尝试获取页面主体
                        if not job.get('job_desc'):
                            body = detail_page.query_selector('main') or detail_page.query_selector('body')
                            if body:
                                text = body.inner_text().strip()
                                if len(text) > 100:
                                    job['job_desc'] = self.clean_text(text[:2000])
                finally:
                    detail_page.close()
                
                # 随机延迟
                self.random_delay(1, 2)
                
            except Exception as e:
                logger.debug(f"获取岗位详情失败: {job.get('job_url')} - {e}")
                continue


def run_website_crawler():
    """
    运行通用官网爬虫的入口函数
    
    Returns:
        list: 抓取到的岗位数据列表
    """
    crawler = WebsiteCrawler()
    return crawler.run()
