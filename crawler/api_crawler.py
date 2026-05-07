# -*- coding: utf-8 -*-
"""
API 接口爬虫
直接调用公司招聘 API 获取数据，比解析 HTML 更稳定
"""

import logging
import json
import time

from .base_crawler import BaseCrawler
from config import WEBSITE_CONFIG, SOURCE_WEBSITE

logger = logging.getLogger(__name__)


class ApiCrawler(BaseCrawler):
    """
    API 接口爬虫
    直接调用公司招聘 API 获取数据
    """

    # 已知的 API 配置（由 detect_apis.py 自动生成 + 手动优化）
    API_CONFIGS = {
        "阿里巴巴": {
            "api_url": "https://campus-talent.alibaba.com/position/search",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "batchId": 100000540002,
                "pageIndex": 1,
                "pageSize": 50,
                "channel": "campus_group_official_site",
                "language": "zh",
            },
            "referer": "https://campus-talent.alibaba.com/campus/position",
            "csrf_cookie": "XSRF-TOKEN",
            "csrf_header": "X-XSRF-TOKEN",
            "data_path": "content.datas",
            "field_mapping": {
                "job_title": "name",
                "location": "workLocations",
                "job_desc": "description",
            },
        },
        "腾讯": {
            "api_url": "https://join.qq.com/api/v1/position/searchPosition",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "pageIndex": 1,
                "pageSize": 20,
                "keyword": "",
                "city": "",
                "categoryId": "",
            },
            "referer": "https://join.qq.com/post.html?query=",
            "data_path": "data.positionList",
            "field_mapping": {
                "job_title": "positionTitle",
                "location": "workCities",
                "job_desc": "recruitLabelName",
            },
        },
        "字节跳动": {
            "api_url": "https://jobs.bytedance.com/api/v1/search/job/posts",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "portal-channel": "campus",
                "portal-platform": "pc",
                "website-path": "campus",
            },
            "payload": {
                "keyword": "",
                "limit": 10,
                "offset": 0,
                "portal_type": 3,
                "portal_entrance": 1,
                "language": "zh",
            },
            "referer": "https://jobs.bytedance.com/campus/position",
            "data_path": "data.job_post_list",
            "field_mapping": {
                "job_title": "title",
                "location": "city_info.name",
                "job_desc": "description",
            },
        },
        "美团": {
            "api_url": "https://zhaopin.meituan.com/api/official/job/getJobList",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "page": {"pageNo": 1, "pageSize": 20},
                "jobShareType": "1",
                "keywords": "",
                "cityList": [],
                "department": [],
                "jobType": [{"code": "3", "subCode": []}],
            },
            "referer": "https://zhaopin.meituan.com/job-list",
            "data_path": "data.list",
            "field_mapping": {
                "job_title": "name",
                "job_desc": "desc",
                "job_url": "jobUnionId",
            },
            "job_url_template": "https://zhaopin.meituan.com/job-list/{jobUnionId}",
        },
        "京东": {
            "api_url": "https://campus.jd.com/api/wx/position/page?type=internship",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            "payload": {
                "pageNo": 1,
                "pageSize": 20,
            },
            "referer": "https://campus.jd.com/",
            "data_path": "data",
            "field_mapping": {
                "job_title": "name",
                "location": "city",
                "job_desc": "desc",
            },
        },
        "小红书": {
            "api_url": "https://job.xiaohongshu.com/websiterecruit/position/pageQueryPosition",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "recruitType": "social",
                "positionName": "",
                "pageNum": 1,
                "pageSize": 20,
            },
            "referer": "https://job.xiaohongshu.com/jobs",
            "data_path": "data.list",
            "field_mapping": {
                "job_title": "positionName",
                "location": "workplace",
                "job_desc": "duty",
            },
        },
        "科大讯飞": {
            "api_url": "https://iflytek.zhiye.com/api/Jobad/GetJobAdPageList",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "pageIndex": 1,
                "pageSize": 20,
                "keyword": "",
            },
            "referer": "https://iflytek.zhiye.com/jobs",
            "data_path": "Data",
            "total_key": "Count",
            "field_mapping": {
                "job_title": "JobAdName",
                "location": "LocNames",
                "job_desc": "Duty",
                "education": "Degree",
                "publish_date": "PostDate",
            },
        },
        "滴滴": {
            "api_url": "https://talent.didiglobal.com/recruit-portal-service/api/job/front/list",
            "method": "GET",
            "headers": {
                "Accept": "application/json",
            },
            "params": {
                "pageIndex": 1,
                "pageSize": 20,
                "jobType": "",
            },
            "referer": "https://talent.didiglobal.com/campus",
            "data_path": "data.items",
            "total_key": "data.total",
            "field_mapping": {
                "job_title": "jobName",
                "location": "workArea",
                "job_desc": "deptName",
                "publish_date": "refreshTime",
                "job_url": "jdId",
            },
            "job_url_template": "https://talent.didiglobal.com/recruit-portal-service/api/job/front/view/{jdId}",
        },
        "网易": {
            "api_url": "https://hr.163.com/api/hr163/position/queryPage",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "language": "zh",
            },
            "payload": {
                "pageSize": 20,
                "pageIndex": 1,
            },
            "referer": "https://hr.163.com/job-list.html?workType=1",
            "data_path": "data.list",
            "total_key": "data.total",
            "field_mapping": {
                "job_title": "name",
                "location": "workPlaceNameList",
                "job_desc": "description",
                "education": "reqEducationName",
                "publish_date": "updateTime",
            },
        },
        "哔哩哔哩": {
            "api_url": "https://jobs.bilibili.com/api/campus/position/positionList",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-appkey": "ops.ehr-api.auth",
                "x-channel": "campus",
                "x-usertype": "2",
            },
            "payload": {
                "pageNo": 1,
                "pageSize": 20,
            },
            "referer": "https://jobs.bilibili.com",
            "csrf_cookie": "bili_jct",
            "data_path": "data.list",
            "field_mapping": {
                "job_title": "name",
                "location": "city",
                "job_desc": "desc",
                "publish_date": "publishTime",
            },
        },
        "快手": {
            "api_url": "https://campus.kuaishou.cn/recruit/campus/e/api/v1/open/positions/simple",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "pageNum": 1,
                "pageSize": 20,
            },
            "referer": "https://campus.kuaishou.cn/recruit/campus/e/",
            "data_path": "result.list",
            "total_key": "result.total",
            "field_mapping": {
                "job_title": "name",
                "job_desc": "description",
                "publish_date": "releaseTime",
                "job_url": "code",
            },
            "job_url_template": "https://campus.kuaishou.cn/recruit/campus/e/#/campus/job-list/{code}",
        },
        "大疆": {
            "api_url": "https://we.dji.com/hire_front/api/common/position/queryPositionCardList",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "currentPage": 1,
                "keyWord": "",
                "pageSize": 20,
                "recruitmentTypes": [],
                "cityList": [],
                "teamList": [],
                "positionCategoryList": [],
                "schoolFlag": "Y",
            },
            "referer": "https://we.dji.com/zh-CN/campus/position",
            "data_path": "data.datas",
            "total_key": "data.total",
            "field_mapping": {
                "job_title": "jobTitle",
                "location": "locationDescription",
                "job_desc": "requirement",
                "publish_date": "createdate",
            },
        },
    }

    def __init__(self):
        super().__init__(WEBSITE_CONFIG)

    def crawl(self, filters=None):
        """执行 API 抓取，只抓取有已知 API 配置的公司"""
        all_jobs = []
        company_names = list(self.API_CONFIGS.keys())

        # 按过滤条件筛选
        if filters and filters.get('companies'):
            company_names = [n for n in company_names if n in filters['companies']]

        total = len(company_names)

        for idx, name in enumerate(company_names, 1):
            if self.should_stop():
                break

            logger.info(f"[{idx}/{total}] 开始抓取: {name}")
            self.report_progress(f"[{idx}/{total}] 正在抓取: {name}", len(all_jobs))

            try:
                jobs = self._crawl_by_api(name)
                if jobs:
                    all_jobs.extend(jobs)
                    self.emit_jobs(jobs)
                    logger.info(f"[{idx}/{total}] {name} 抓取到 {len(jobs)} 条岗位")
                else:
                    logger.info(f"[{idx}/{total}] {name} 未抓取到岗位")
            except Exception as e:
                logger.error(f"[{idx}/{total}] {name} 抓取异常: {e}")
                continue

            if idx < total:
                self.random_delay()

        logger.info(f"API 爬虫完成，共抓取 {len(all_jobs)} 条岗位")
        return all_jobs

    def _crawl_by_api(self, company_name):
        """使用已知 API 配置抓取，支持分页，支持 GET 和 POST"""
        api_config = self.API_CONFIGS[company_name]
        jobs = []

        page = self.create_page()

        try:
            # 先访问页面获取 Cookie 和 CSRF token
            referer = api_config.get('referer', '')
            if not self.safe_goto(page, referer):
                logger.warning(f"无法加载页面: {referer}")
                return jobs

            time.sleep(3)

            # 获取 CSRF token（如果有配置的话）
            csrf_token = self._get_csrf_token(page, api_config) or ''

            api_url = api_config['api_url']
            method = api_config.get('method', 'POST').upper()
            base_payload = api_config.get('payload', {})
            base_params = api_config.get('params', {})
            data_path = api_config.get('data_path', 'data')

            # 检测分页参数名（在 payload 或 params 中查找）
            all_params = {**base_payload, **base_params}
            page_key = None
            for key in ['pageIndex', 'pageNo', 'page', 'offset', 'pageNum', 'currentPage']:
                if key in all_params:
                    page_key = key
                    break
            if not page_key:
                page_key = 'pageIndex'

            # 检测每页大小参数名
            size_key = None
            for key in ['pageSize', 'size', 'limit', 'count']:
                if key in all_params:
                    size_key = key
                    break
            if not size_key:
                size_key = 'pageSize'

            page_index = 1
            page_size = all_params.get(size_key, 20)

            while True:
                if self.should_stop():
                    break

                # 构建请求参数
                if method == 'GET':
                    # GET 请求：参数拼接到 URL
                    params = {**base_params, page_key: page_index}
                    query_parts = [f"{k}={v}" for k, v in params.items()]
                    full_url = f"{api_url}?{'&'.join(query_parts)}"
                    if csrf_token:
                        full_url += f"&_csrf={csrf_token}"

                    response_text = page.evaluate('''
                        async ([url]) => {
                            try {
                                const resp = await fetch(url, {
                                    method: "GET",
                                    headers: { "Accept": "application/json" },
                                    credentials: "include"
                                });
                                return JSON.stringify(await resp.json());
                            } catch(e) {
                                return JSON.stringify({error: e.message});
                            }
                        }
                    ''', [full_url])
                else:
                    # POST 请求
                    payload = {**base_payload, page_key: page_index}
                    full_url = f"{api_url}?_csrf={csrf_token}" if csrf_token else api_url

                    response_text = page.evaluate('''
                        async ([url, payload, csrf]) => {
                            try {
                                const resp = await fetch(url, {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                        "Accept": "application/json",
                                        "X-XSRF-TOKEN": csrf,
                                    },
                                    body: JSON.stringify(payload),
                                    credentials: "include"
                                });
                                return JSON.stringify(await resp.json());
                            } catch(e) {
                                return JSON.stringify({error: e.message});
                            }
                        }
                    ''', [full_url, payload, csrf_token])

                response = json.loads(response_text)

                if not response or response.get('error'):
                    logger.warning(f"API 请求失败: {response}")
                    break

                # 检查是否需要登录
                resp_str = json.dumps(response, ensure_ascii=False).lower()
                if 'need-login' in resp_str or 'need login' in resp_str or '未登录' in resp_str or '"code":40008' in resp_str:
                    logger.warning(f"{company_name} API 需要登录，跳过")
                    break

                # 解析响应数据
                data = self._get_nested_value(response, data_path)
                if not data or not isinstance(data, list):
                    logger.info(f"第 {page_index} 页无数据，抓取结束")
                    break

                for item in data:
                    job = self._parse_api_item(item, company_name, api_config)
                    if job and job.get('job_title'):
                        jobs.append(job)

                logger.info(f"第 {page_index} 页返回 {len(data)} 条，累计 {len(jobs)} 条岗位")

                # 判断是否还有下一页
                if len(data) < page_size:
                    break

                # 检查 total_key 判断是否已获取全部数据
                total_key = api_config.get('total_key')
                if total_key:
                    total_count = self._get_nested_value(response, total_key)
                    if isinstance(total_count, (int, float)) and len(jobs) >= total_count:
                        logger.info(f"已获取全部 {total_count} 条岗位")
                        break

                page_index += 1
                self.random_delay(1, 2)

        except Exception as e:
            logger.error(f"API 抓取失败: {e}")
        finally:
            page.close()

        return jobs

    def _get_csrf_token(self, page, api_config):
        """从 Cookie 中获取 CSRF token"""
        try:
            csrf_cookie_name = api_config.get('csrf_cookie')
            if csrf_cookie_name:
                cookies = page.context.cookies()
                for cookie in cookies:
                    if cookie['name'] == csrf_cookie_name:
                        return cookie['value']
        except Exception as e:
            logger.debug(f"获取 CSRF token 失败: {e}")
        return None

    def _get_nested_value(self, obj, path):
        """获取嵌套对象的值"""
        try:
            keys = path.split('.')
            value = obj
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None
            return value
        except:
            return None

    def _parse_api_item(self, item, company_name, api_config):
        """
        解析 API 返回的岗位数据
        使用 field_mapping 配置进行通用解析
        """
        try:
            field_mapping = api_config.get('field_mapping', {})

            # 通用字段提取
            job_title = self._get_nested_value(item, field_mapping.get('job_title', 'name')) or ''
            location = self._get_nested_value(item, field_mapping.get('location', 'location')) or ''
            salary = self._get_nested_value(item, field_mapping.get('salary', 'salary')) or ''
            education = self._get_nested_value(item, field_mapping.get('education', 'education')) or ''
            job_desc = self._get_nested_value(item, field_mapping.get('job_desc', 'description')) or ''
            publish_date = self._get_nested_value(item, field_mapping.get('publish_date', 'publishTime')) or ''
            job_url = self._get_nested_value(item, field_mapping.get('job_url', 'url')) or ''

            # 处理地点是数组的情况（支持字符串数组和对象数组）
            if isinstance(location, list):
                location = ' / '.join(
                    str(loc.get('name', loc)) if isinstance(loc, dict) else str(loc)
                    for loc in location if loc
                )

            # 处理描述字段
            if isinstance(job_desc, list):
                job_desc = '\n'.join(str(d) for d in job_desc if d)

            # 判断岗位类型
            job_type = 'graduate'
            title_lower = str(job_title).lower()
            if '实习' in title_lower or 'intern' in title_lower:
                job_type = 'intern'

            # 构建岗位 URL
            if not job_url:
                # 尝试用 job_url_template 构建
                url_template = api_config.get('job_url_template', '')
                if url_template:
                    # 用 item 中的字段填充模板
                    try:
                        job_url = url_template.format(**item)
                    except (KeyError, ValueError):
                        pass

            if not job_url:
                # 尝试用 id 构建
                item_id = item.get('id', item.get('positionId', item.get('jdId', '')))
                if item_id:
                    job_url = f"{api_config.get('referer', '')}/{item_id}"

            return {
                'job_title': str(job_title)[:200],
                'company_name': company_name,
                'location': str(location)[:100],
                'salary': str(salary)[:50],
                'job_type': job_type,
                'education': str(education)[:50],
                'publish_date': str(publish_date)[:20],
                'job_desc': str(job_desc)[:3000],
                'job_url': str(job_url)[:500],
                'source': SOURCE_WEBSITE,
            }
        except Exception as e:
            logger.debug(f"解析 API 数据失败: {e}")
            return None

