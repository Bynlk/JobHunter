# -*- coding: utf-8 -*-
"""
实习僧爬虫模块（基于真实页面结构 2026-05）
从 shixiseng.com 抓取实习和校招岗位数据
通过解析动态字体的 glyph 名称破解反爬字体
"""

import logging
import re
import io
from .base_crawler import BaseCrawler
from config import SHIXISENG_CONFIG, SOURCE_SHIXISENG

logger = logging.getLogger(__name__)


class ShixisengCrawler(BaseCrawler):

    def __init__(self):
        super().__init__(SHIXISENG_CONFIG)
        self.base_url = SHIXISENG_CONFIG['base_url']
        self.keywords = SHIXISENG_CONFIG['keywords']
        self._font_mapping = {}  # PUA char -> real char

    def crawl(self):
        all_jobs = []

        for keyword in self.keywords:
            if self.should_stop():
                break
            logger.info(f"开始抓取实习僧，关键词: {keyword}")
            self.report_progress(f"实习僧 - 关键词: {keyword}")

            for page_num in range(1, self.max_pages + 1):
                if self.should_stop():
                    break
                try:
                    search_url = f"{self.base_url}?keyword={keyword}&type=intern&page={page_num}"
                    logger.info(f"抓取第 {page_num} 页: {search_url}")

                    page = self.create_page()
                    try:
                        # 每页重置字体映射，防止跨页脏数据
                        self._font_mapping = {}

                        # 拦截动态字体文件
                        font_data = [None]
                        def intercept_font(route):
                            try:
                                resp = route.fetch()
                                font_data[0] = resp.body()
                                route.fulfill(response=resp)
                            except Exception as e:
                                logger.warning(f"字体拦截失败: {e}")
                                route.continue_()
                        page.route('**/iconfonts/file**', intercept_font)

                        if not self.safe_goto(page, search_url, wait_ms=5000):
                            logger.warning(f"无法加载页面: {search_url}")
                            continue

                        # 解析字体文件获取映射
                        self._decode_font(font_data[0])

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

        # 获取详情页信息（薪资、描述等）
        if all_jobs:
            self.report_progress("实习僧 - 正在获取岗位详情...", len(all_jobs))
            self.enrich_jobs(all_jobs, max_count=50)

        logger.info(f"实习僧抓取完成，共获取 {len(all_jobs)} 条岗位数据")
        return all_jobs

    def _decode_font(self, font_bytes):
        """从字体文件的 glyph 名称解析 PUA->真实字符映射"""
        if not font_bytes:
            logger.warning("未获取到字体文件")
            return
        try:
            from fontTools.ttLib import TTFont
            font = TTFont(io.BytesIO(font_bytes))
            cmap = font.getBestCmap()
            mapping = {}
            for pua_cp, glyph_name in cmap.items():
                if 0xE000 <= pua_cp <= 0xF8FF and glyph_name.startswith('uni'):
                    try:
                        real_cp = int(glyph_name[3:], 16)
                        mapping[chr(pua_cp)] = chr(real_cp)
                    except (ValueError, OverflowError):
                        pass
            if mapping:
                self._font_mapping = mapping
                logger.info(f"字体解码成功，映射 {len(mapping)} 个字符")
                sample = dict(list(mapping.items())[:8])
                logger.info(f"映射样例: {sample}")
            else:
                logger.warning("字体文件中未找到 PUA 映射")
        except ImportError:
            logger.error("fonttools 未安装，无法解码字体")
        except Exception as e:
            logger.error(f"字体解码异常: {e}")

    def _apply_font_mapping(self, text):
        """将 PUA 字符替换为真实字符"""
        if not self._font_mapping or not text:
            return text
        return ''.join(self._font_mapping.get(ch, ch) for ch in text)

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
            job_data['job_url'] = href.split('?')[0]

        # 岗位名称 — 应用字体映射解码 PUA 字符
        title_el = card.query_selector('.intern-detail__job a.title')
        if title_el:
            raw = title_el.text_content().strip()
            clean = self._apply_font_mapping(raw)
            clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', clean).strip()
            if clean:
                job_data['job_title'] = clean

        # 公司名称
        company_el = card.query_selector('.intern-detail__company a.title')
        if company_el:
            raw = company_el.text_content().strip()
            job_data['company_name'] = self._apply_font_mapping(raw)

        # 城市
        city_el = card.query_selector('.city')
        if city_el:
            raw = city_el.text_content().strip()
            job_data['location'] = self._apply_font_mapping(raw)

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
            if count >= max_count or self.should_stop():
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
            # 拦截动态字体
            self._font_mapping = {}
            font_data = [None]
            def intercept_font(route):
                try:
                    resp = route.fetch()
                    font_data[0] = resp.body()
                    route.fulfill(response=resp)
                except Exception as e:
                    logger.warning(f"详情页字体拦截失败: {e}")
                    route.continue_()
            page.route('**/iconfonts/file**', intercept_font)

            if not self.safe_goto(page, job['job_url'], wait_ms=3000):
                return

            # 详情页字体可能不同，重新解码
            if font_data[0]:
                self._decode_font(font_data[0])

            # 薪资
            salary_el = page.query_selector('.job_money, [class*="money"]')
            if salary_el:
                salary_text = self._apply_font_mapping(salary_el.text_content().strip())
                if salary_text and salary_text != '面议':
                    job['salary'] = salary_text

            # 岗位描述
            desc_selectors = ['.job_detail', '.job-content', '[class*="detail"]', '[class*="desc"]']
            for sel in desc_selectors:
                el = page.query_selector(sel)
                if el:
                    text = self._apply_font_mapping(el.text_content().strip())
                    if len(text) > 50:
                        job['job_desc'] = self.clean_text(text[:3000])
                        break

            # 学历要求
            academic_el = page.query_selector('.job_academic, [class*="academic"]')
            if academic_el:
                job['education'] = self._apply_font_mapping(academic_el.text_content().strip())

            # 发布日期
            date_el = page.query_selector('.job_date, [class*="date"]')
            if date_el:
                raw_date = date_el.text_content().strip()
                m = re.search(r'(\d{4}-\d{2}-\d{2})', raw_date)
                if m:
                    job['publish_date'] = m.group(1)

            # 公司详情（行业、性质、规模）
            com_detail_el = page.query_selector('.com-detail')
            if com_detail_el:
                lines = [self._apply_font_mapping(l.strip())
                         for l in com_detail_el.text_content().split('\n') if l.strip()]
                if len(lines) >= 1 and not job.get('industry'):
                    job['industry'] = lines[0]
                if len(lines) >= 2 and not job.get('company_nature'):
                    job['company_nature'] = lines[1]
                if len(lines) >= 3 and not job.get('company_size'):
                    job['company_size'] = lines[2]

            # 福利标签
            welfare_el = page.query_selector('.job_good_list, [class*="good_list"]')
            if welfare_el:
                job['welfare'] = self._apply_font_mapping(welfare_el.text_content().strip())

        finally:
            page.close()
