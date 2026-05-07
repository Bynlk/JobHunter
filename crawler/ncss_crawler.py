# -*- coding: utf-8 -*-
"""
国家大学生就业服务平台爬虫模块（基于真实 API 2026-05）
从 ncss.cn 通过 JSON API 抓取岗位数据
"""

import logging
from datetime import datetime

from .base_crawler import BaseCrawler
from config import NCSS_CONFIG, SOURCE_NCSS, NCSS_AREA_CODES, NCSS_INDUSTRY_CODES

logger = logging.getLogger(__name__)


class NCSSCrawler(BaseCrawler):

    def __init__(self):
        super().__init__(NCSS_CONFIG)
        self.base_url = NCSS_CONFIG['base_url']
        self.api_url = 'https://www.ncss.cn/student/jobs/jobslist/ajax/'

    def crawl(self, filters=None):
        """
        通过 NCSS 的 JSON API 抓取岗位数据
        每页获取后立即推送

        Args:
            filters: 定向抓取过滤条件 dict，可选键: companies, industries, locations
        """
        all_jobs = []

        logger.info("开始抓取国家大学生就业服务平台")
        self.report_progress("国家平台 - 正在启动浏览器...")

        # 解析过滤条件为 NCSS API 参数
        filter_params = self._build_filter_params(filters)
        if filters:
            logger.info(f"定向抓取条件: {filter_params}")

        # 需要先访问页面获取 session cookies
        page = self.create_page()
        try:
            page.goto(self.base_url, timeout=self.timeout, wait_until='domcontentloaded')
            page.wait_for_timeout(5000)
            logger.info("国家平台首页加载完成")

            for page_num in range(1, self.max_pages + 1):
                if self.should_stop():
                    break
                offset = page_num
                limit = 20

                logger.info(f"抓取国家平台第 {page_num} 页 (offset={offset})")
                self.report_progress(f"国家平台 - 第{page_num}页", len(all_jobs))

                try:
                    ts = int(datetime.now().timestamp() * 1000)
                    api_url = f"{self.api_url}?jobType={filter_params['jobType']}&areaCode={filter_params['areaCode']}&jobName={filter_params['jobName']}&monthPay=&industrySectors={filter_params['industrySectors']}&property=&categoryCode=&memberLevel=&recruitType=&offset={offset}&limit={limit}&keyUnits={filter_params['keyUnits']}&degreeCode=&sourcesName=0&sourcesType=&_={ts}"
                    result = page.evaluate('async (url) => { const resp = await fetch(url); return await resp.json(); }', api_url)

                    if not result or not result.get('data') or not result['data'].get('list'):
                        logger.info(f"第 {page_num} 页无数据，停止翻页")
                        break

                    jobs_data = result['data']['list']
                    logger.info(f"第 {page_num} 页获取到 {len(jobs_data)} 条数据")

                    page_jobs = []
                    for item in jobs_data:
                        try:
                            job = self._normalize_job(item)
                            if job and job.get('job_url'):
                                page_jobs.append(job)
                        except Exception as e:
                            logger.debug(f"解析岗位数据失败: {e}")
                            continue

                    if page_jobs:
                        all_jobs.extend(page_jobs)
                        self.emit_jobs(page_jobs)

                    self.report_progress(
                        f"国家平台 - 第{page_num}页完成，累计{len(all_jobs)}条",
                        len(all_jobs)
                    )

                    if len(jobs_data) < limit:
                        logger.info(f"第 {page_num} 页数据不足 {limit} 条，已是最后一页")
                        break

                    self.random_delay()

                except Exception as e:
                    logger.error(f"抓取第 {page_num} 页异常: {e}")
                    continue

        finally:
            page.close()

        # 获取详情页描述
        if all_jobs:
            self.report_progress("国家平台 - 正在获取岗位详情...", len(all_jobs))
            self._enrich_jobs(all_jobs, max_count=50)

        logger.info(f"国家平台抓取完成，共获取 {len(all_jobs)} 条岗位数据")
        return all_jobs

    def _enrich_jobs(self, jobs, max_count=50):
        """访问详情页获取岗位描述"""
        count = 0
        for job in jobs:
            if count >= max_count or self.should_stop():
                break
            if not job.get('job_url') or job.get('job_desc'):
                continue
            try:
                detail_page = self.create_page()
                try:
                    if self.safe_goto(detail_page, job['job_url'], wait_ms=3000):
                        desc_selectors = [
                            '.job-detail', '.detail-content', '.job-desc',
                            '.position-detail', '.job-content', '.content',
                            '[class*="detail"]', '[class*="desc"]',
                            'article', 'main',
                        ]
                        for sel in desc_selectors:
                            el = detail_page.query_selector(sel)
                            if el:
                                text = el.inner_text().strip()
                                if len(text) > 50:
                                    job['job_desc'] = self.clean_text(text[:3000])
                                    break
                        # 补充学历（如果详情页有更精确的）
                        if not job.get('education'):
                            edu_el = detail_page.query_selector('[class*="degree"], [class*="education"], [class*="academic"]')
                            if edu_el:
                                job['education'] = edu_el.text_content().strip()
                finally:
                    detail_page.close()
                count += 1
                self.random_delay(1, 2)
            except Exception as e:
                logger.debug(f"获取详情失败: {job.get('job_url')} - {e}")

    def _build_filter_params(self, filters):
        """
        将前端传来的过滤条件转换为 NCSS API 参数

        Args:
            filters: dict，可选键: companies, industries, locations

        Returns:
            dict: NCSS API 参数
        """
        params = {
            'areaCode': '',
            'industrySectors': '',
            'keyUnits': '',
            'jobName': '',
            'jobType': '',
        }
        if not filters:
            return params

        # 地区: 取第一个匹配的 areaCode（NCSS 只支持单个地区）
        if filters.get('locations'):
            for loc in filters['locations']:
                code = NCSS_AREA_CODES.get(loc)
                if code:
                    params['areaCode'] = code
                    break

        # 行业: 取第一个匹配的 industrySectors 编码
        if filters.get('industries'):
            for ind in filters['industries']:
                code = NCSS_INDUSTRY_CODES.get(ind)
                if code:
                    params['industrySectors'] = code
                    break

        # 公司: NCSS 的 keyUnits 参数接受公司名关键词
        if filters.get('companies'):
            # 用第一个公司名作为搜索关键词
            params['keyUnits'] = filters['companies'][0]

        return params

    def _normalize_job(self, item):
        """
        将 API 返回的岗位数据标准化
        API 字段: jobName, recName, areaCodeName, lowMonthPay, highMonthPay,
                  degreeName, jobId, publishDate, recProperty, headCount
        """
        job_id = item.get('jobId', '')
        if not job_id:
            return None

        # 薪资
        low = item.get('lowMonthPay')
        high = item.get('highMonthPay')
        salary = ''
        if low is not None and high is not None:
            salary = f"{float(low):.0f}K-{float(high):.0f}K"

        # 发布日期
        pub_ts = item.get('publishDate')
        publish_date = ''
        if pub_ts:
            try:
                publish_date = datetime.fromtimestamp(pub_ts / 1000).strftime('%Y-%m-%d')
            except Exception:
                pass

        # 岗位类型
        title = item.get('jobName', '')
        job_type = 'graduate'
        if '实习' in title or 'intern' in title.lower():
            job_type = 'intern'

        return {
            'job_title': title,
            'company_name': item.get('recName', ''),
            'location': item.get('areaCodeName', ''),
            'salary': salary,
            'job_type': job_type,
            'education': item.get('degreeName', ''),
            'publish_date': publish_date,
            'job_desc': '',
            'job_url': f"https://www.ncss.cn/student/jobs/{job_id}/detail.html",
            'source': SOURCE_NCSS,
            'industry': item.get('industrySectorsName', '') or item.get('industryName', ''),
            'company_nature': item.get('recProperty', ''),
            'company_size': '',
            'welfare': '',
        }
