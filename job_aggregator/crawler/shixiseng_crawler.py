# -*- coding: utf-8 -*-
"""
实习僧爬虫模块（基于真实页面结构 2026-05）
从 shixiseng.com 抓取实习和校招岗位数据
"""

import logging
import re
from .base_crawler import BaseCrawler
from config import SHIXISENG_CONFIG, SOURCE_SHIXISENG

logger = logging.getLogger(__name__)


class ShixisengCrawler(BaseCrawler):

    def __init__(self):
        super().__init__(SHIXISENG_CONFIG)
        self.base_url = SHIXISENG_CONFIG['base_url']
        self.keywords = SHIXISENG_CONFIG['keywords']

    def crawl(self):
        all_jobs = []

        for keyword in self.keywords:
            logger.info(f"开始抓取实习僧，关键词: {keyword}")
            self.report_progress(f"实习僧 - 关键词: {keyword}")

            for page_num in range(1, self.max_pages + 1):
                try:
                    search_url = f"{self.base_url}?keyword={keyword}&type=intern&page={page_num}"
                    logger.info(f"抓取第 {page_num} 页: {search_url}")

                    page = self.create_page()
                    try:
                        if not self.safe_goto(page, search_url, wait_ms=5000):
                            logger.warning(f"无法加载页面: {search_url}")
                            continue

                        # 真实选择器：.intern-item 是岗位卡片
                        job_cards = page.query_selector_all('.intern-item')
                        if not job_cards:
                            logger.warning(f"第 {page_num} 页无岗位卡片，停止翻页")
                            break

                        logger.info(f"第 {page_num} 页找到 {len(job_cards)} 个岗位卡片")

                        page_jobs = []
                        for card in job_cards:
                            try:
                                job_data = self._parse_card(card)
                                if job_data and job_data.get('job_url'):
                                    page_jobs.append(job_data)
                            except Exception as e:
                                logger.debug(f"解析卡片失败: {e}")
                                continue

                        if page_jobs:
                            all_jobs.extend(page_jobs)
                            self.emit_jobs(page_jobs)

                        self.report_progress(
                            f"实习僧 - {keyword} - 第{page_num}页完成，累计{len(all_jobs)}条",
                            len(all_jobs)
                        )

                    finally:
                        page.close()

                    self.random_delay()

                except Exception as e:
                    logger.error(f"抓取第 {page_num} 页异常: {e}")
                    continue

        logger.info(f"实习僧抓取完成，共获取 {len(all_jobs)} 条岗位数据")
        return all_jobs

    def _parse_card(self, card):
        """解析列表页的岗位卡片"""
        job_data = {
            'job_title': '',
            'company_name': '',
            'location': '',
            'salary': '',
            'job_type': 'intern',
            'education': '',
            'publish_date': '',
            'job_desc': '',
            'job_url': '',
            'source': SOURCE_SHIXISENG,
            'industry': '',
            'company_nature': '',
            'company_size': '',
            'welfare': '',
        }

        # 岗位链接（必须有）
        link = card.query_selector('a[href*="/intern/"]')
        if not link:
            return None

        href = link.get_attribute('href')
        if href:
            if not href.startswith('http'):
                href = 'https://www.shixiseng.com' + href
            job_data['job_url'] = href.split('?')[0]  # 去掉 tracking 参数

        # 岗位名称（a.title.font，icon font 可能部分乱码，但关键中文能读）
        title_el = card.query_selector('.intern-detail__job a.title')
        if title_el:
            raw = title_el.text_content().strip()
            # 过滤掉不可打印字符
            clean = re.sub(r'[-￿]', '', raw).strip()
            if clean:
                job_data['job_title'] = clean

        # 公司名称（纯文本）
        company_el = card.query_selector('.intern-detail__company a.title')
        if company_el:
            job_data['company_name'] = company_el.text_content().strip()

        # 城市（纯文本）
        city_el = card.query_selector('.city')
        if city_el:
            job_data['location'] = city_el.text_content().strip()

        # 判断岗位类型
        if job_data['job_title']:
            t = job_data['job_title'].lower()
            if '校招' in t or '应届' in t or 'graduate' in t:
                job_data['job_type'] = 'graduate'

        return job_data

    def enrich_jobs(self, jobs, max_count=50):
        """
        获取岗位详情页的薪资和描述信息
        只对前 max_count 条岗位访问详情页
        """
        count = 0
        for job in jobs:
            if count >= max_count:
                break
            if not job.get('job_url'):
                continue
            try:
                self._enrich_single(job)
                count += 1
                self.random_delay(1, 2)
            except Exception as e:
                logger.debug(f"获取详情失败: {job['job_url']} - {e}")

    def _enrich_single(self, job):
        """访问详情页，提取薪资、描述、学历、行业等字段"""
        page = self.create_page()
        try:
            if not self.safe_goto(page, job['job_url'], wait_ms=3000):
                return

            # 薪资
            salary_el = page.query_selector('.job_money, [class*="money"]')
            if salary_el:
                salary_text = salary_el.text_content().strip()
                if salary_text and salary_text != '面议':
                    job['salary'] = salary_text

            # 岗位描述
            desc_selectors = ['.job_detail', '.job-content', '[class*="detail"]', '[class*="desc"]']
            for sel in desc_selectors:
                el = page.query_selector(sel)
                if el:
                    text = el.text_content().strip()
                    if len(text) > 50:
                        job['job_desc'] = self.clean_text(text[:3000])
                        break

            # 学历要求
            academic_el = page.query_selector('.job_academic, [class*="academic"]')
            if academic_el:
                job['education'] = academic_el.text_content().strip()

            # 发布日期
            date_el = page.query_selector('.job_date, [class*="date"]')
            if date_el:
                raw_date = date_el.text_content().strip()
                # 格式: "2023-07-25 16:53:43 刷新"
                import re
                m = re.search(r'(\d{4}-\d{2}-\d{2})', raw_date)
                if m:
                    job['publish_date'] = m.group(1)

            # 公司详情（行业、性质、规模）
            com_detail_el = page.query_selector('.com-detail')
            if com_detail_el:
                lines = [l.strip() for l in com_detail_el.text_content().split('\n') if l.strip()]
                if len(lines) >= 1 and not job.get('industry'):
                    job['industry'] = lines[0]
                if len(lines) >= 2 and not job.get('company_nature'):
                    job['company_nature'] = lines[1]
                if len(lines) >= 3 and not job.get('company_size'):
                    job['company_size'] = lines[2]

            # 福利标签
            welfare_el = page.query_selector('.job_good_list, [class*="good_list"]')
            if welfare_el:
                job['welfare'] = welfare_el.text_content().strip()

        finally:
            page.close()
