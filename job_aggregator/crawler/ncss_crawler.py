# -*- coding: utf-8 -*-
"""
国家大学生就业服务平台爬虫模块（基于真实 API 2026-05）
从 ncss.cn 通过 JSON API 抓取岗位数据
"""

import logging
from datetime import datetime

from .base_crawler import BaseCrawler
from config import NCSS_CONFIG, SOURCE_NCSS

logger = logging.getLogger(__name__)


class NCSSCrawler(BaseCrawler):

    def __init__(self):
        super().__init__(NCSS_CONFIG)
        self.base_url = NCSS_CONFIG['base_url']
        self.api_url = 'https://www.ncss.cn/student/jobs/jobslist/ajax/'

    def crawl(self):
        """
        通过 NCSS 的 JSON API 抓取岗位数据
        每页获取后立即推送
        """
        all_jobs = []

        logger.info("开始抓取国家大学生就业服务平台")
        self.report_progress("国家平台 - 正在启动浏览器...")

        # 需要先访问页面获取 session cookies
        page = self.create_page()
        try:
            page.goto(self.base_url, timeout=self.timeout, wait_until='domcontentloaded')
            page.wait_for_timeout(5000)
            logger.info("国家平台首页加载完成")

            for page_num in range(1, self.max_pages + 1):
                offset = page_num
                limit = 20

                logger.info(f"抓取国家平台第 {page_num} 页 (offset={offset})")
                self.report_progress(f"国家平台 - 第{page_num}页", len(all_jobs))

                try:
                    result = page.evaluate(f'''async () => {{
                        const resp = await fetch("{self.api_url}?jobType=&areaCode=&jobName=&monthPay=&industrySectors=&property=&categoryCode=&memberLevel=&recruitType=&offset={offset}&limit={limit}&keyUnits=&degreeCode=&sourcesName=0&sourcesType=&_={int(datetime.now().timestamp()*1000)}");
                        return await resp.json();
                    }}''')

                    if not result or not result.get('data') or not result['data'].get('list'):
                        logger.info(f"第 {page_num} 页无数据，停止翻页")
                        break

                    jobs_data = result['data']['list']
                    logger.info(f"第 {page_num} 页获取到 {len(jobs_data)} 条数据")

                    page_jobs = []
                    for item in jobs_data:
                        job = self._normalize_job(item)
                        if job and job.get('job_url'):
                            page_jobs.append(job)

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

        logger.info(f"国家平台抓取完成，共获取 {len(all_jobs)} 条岗位数据")
        return all_jobs

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
