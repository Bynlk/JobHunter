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
            "data_path": "data",
            "field_mapping": {
                "job_title": "title",
                "location": "location",
                "job_desc": "desc",
            },
        },
        "字节跳动": {
            "api_url": "https://jobs.bytedance.com/api/v1/search/job/posts",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "keyword": "",
                "limit": 10,
                "offset": 0,
                "job_category_id_list": [],
                "city_code_list": [],
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
            },
        },
        "京东": {
            "api_url": "https://campus.jd.com/api/wx/position/page",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "type": "present",
                "pageNo": 1,
                "pageSize": 20,
            },
            "referer": "https://campus.jd.com/#/jobs",
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
            "data_path": "data",
            "field_mapping": {
                "job_title": "title",
                "location": "city",
                "job_desc": "desc",
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
            "api_url": "https://campus.163.com/api/campuspc/position/getJobList",
            "method": "GET",
            "headers": {
                "Accept": "application/json",
            },
            "params": {
                "pageIndex": 1,
                "pageSize": 20,
            },
            "referer": "https://campus.163.com/web/job/list",
            "data_path": "data.list",
            "total_key": "data.total",
            "field_mapping": {
                "job_title": "name",
                "location": "workCity",
                "job_desc": "requirement",
                "publish_date": "publishTime",
            },
        },
        "哔哩哔哩": {
            "api_url": "https://jobs.bilibili.com/api/campus/position/positionList",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "pageNo": 1,
                "pageSize": 20,
            },
            "referer": "https://jobs.bilibili.com",
            "data_path": "data.list",
            "field_mapping": {
                "job_title": "name",
                "location": "city",
                "job_desc": "desc",
                "publish_date": "publishTime",
            },
        },
        "百度": {
            "api_url": "https://talent.baidu.com/baidu/api/job/list",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {
                "pageNo": 1,
                "pageSize": 20,
                "workPlace": "",
                "postType": "",
                "deptCode": "",
                "keyword": "",
            },
            "referer": "https://talent.baidu.com/jobs/list",
            "data_path": "data",
            "field_mapping": {
                "job_title": "name",
                "location": "workPlace",
                "job_desc": "desc",
            },
        },
        "快手": {
            "api_url": "https://zhaopin.kuaishou.cn/recruit/e/api/campus/job-list",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "payload": {},
            "referer": "https://zhaopin.kuaishou.cn/recruit/e/#/campus/job-list",
            "data_path": "data",
            "field_mapping": {
                "job_title": "name",
                "location": "city",
                "job_desc": "desc",
            },
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
        self.config_file = WEBSITE_CONFIG['config_file']
        self.companies = []

    def load_companies(self):
        """加载公司配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.companies = json.load(f)
            logger.info(f"成功加载 {len(self.companies)} 家公司配置")
            return self.companies
        except Exception as e:
            logger.error(f"加载公司配置失败: {e}")
            return []

    def crawl(self, filters=None):
        """
        执行 API 抓取
        """
        all_jobs = []

        # 加载公司配置
        companies = self.load_companies()
        if not companies:
            return all_jobs

        # 按过滤条件筛选
        if filters:
            filtered = []
            for c in companies:
                name = c.get('name', '')
                industry = c.get('industry', '')
                if filters.get('companies') and name not in filters['companies']:
                    continue
                if filters.get('industries') and industry not in filters['industries']:
                    continue
                filtered.append(c)
            companies = filtered

        total = len(companies)

        for idx, company in enumerate(companies, 1):
            if self.should_stop():
                break

            name = company.get('name', '')
            url = company.get('url', '')

            if not url:
                continue

            logger.info(f"[{idx}/{total}] 开始抓取: {name}")
            self.report_progress(f"[{idx}/{total}] 正在抓取: {name}", len(all_jobs))

            try:
                # 检查是否有 API 配置
                if name in self.API_CONFIGS:
                    jobs = self._crawl_by_api(name, company)
                else:
                    # 尝试自动检测 API
                    jobs = self._try_detect_api(name, company)

                if jobs:
                    all_jobs.extend(jobs)
                    self.emit_jobs(jobs)
                    logger.info(f"[{idx}/{total}] {name} 抓取到 {len(jobs)} 条岗位")
                else:
                    logger.info(f"[{idx}/{total}] {name} 未抓取到岗位")
            except Exception as e:
                logger.error(f"[{idx}/{total}] {name} 抓取异常: {e}")
                continue

            # 随机延迟
            if idx < total:
                self.random_delay()

        logger.info(f"API 爬虫完成，共抓取 {len(all_jobs)} 条岗位")
        return all_jobs

    def _crawl_by_api(self, company_name, company_config):
        """
        使用已知 API 配置抓取，支持分页，支持 GET 和 POST
        """
        api_config = self.API_CONFIGS[company_name]
        jobs = []

        page = self.create_page()

        try:
            # 先访问页面获取 Cookie 和 CSRF token
            referer = api_config.get('referer', company_config['url'])
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

            # 处理地点是数组的情况
            if isinstance(location, list):
                location = ' / '.join(str(loc) for loc in location if loc)

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

    def _try_detect_api(self, company_name, company_config):
        """
        尝试自动检测 API 接口
        监听网络请求，捕获响应数据，自动识别岗位 API 并提取数据
        """
        jobs = []
        page = self.create_page()

        captured_responses = []

        # 岗位相关关键词
        JOB_KEYWORDS = [
            'title', 'name', 'position', 'job', 'city', 'location',
            'salary', 'degree', 'education', 'department', 'workCity',
            'jobTitle', 'positionName', 'jobName', 'workPlace',
        ]

        # 排除的 URL 模式
        EXCLUDE_PATTERNS = [
            '.css', '.js', '.png', '.jpg', '.gif', '.svg', '.ico',
            'analytics', 'tracking', 'log', 'stat', 'beacon',
            'captcha', 'verify', 'auth', 'login', 'logout',
            'config', 'setting', 'preference', 'chat', 'message',
        ]

        def handle_response(response):
            try:
                url = response.url
                content_type = response.headers.get('content-type', '')

                if 'json' not in content_type or response.status != 200:
                    return

                # 排除非岗位 API
                url_lower = url.lower()
                if any(p in url_lower for p in EXCLUDE_PATTERNS):
                    return

                # 只关注可能包含岗位数据的 URL
                if not any(kw in url_lower for kw in ['search', 'list', 'job', 'position', 'api', 'query', 'page']):
                    return

                try:
                    body = response.json()
                    captured_responses.append({
                        'url': url,
                        'method': response.request.method,
                        'body': body,
                    })
                except:
                    pass
            except:
                pass

        page.on('response', handle_response)

        try:
            # 访问页面
            if not self.safe_goto(page, company_config['url']):
                return jobs

            # 等待页面加载和 API 请求
            time.sleep(5)

            # 滚动页面触发更多 API
            for _ in range(3):
                page.evaluate('window.scrollBy(0, 500)')
                time.sleep(1)

            time.sleep(2)

            logger.info(f"{company_name} 捕获到 {len(captured_responses)} 个 JSON 响应")

            # 分析每个响应，查找岗位数据
            for resp in captured_responses:
                body = resp['body']
                data_str = json.dumps(body, ensure_ascii=False).lower()

                # 统计岗位关键词
                keyword_count = sum(1 for kw in JOB_KEYWORDS if kw in data_str)
                if keyword_count < 3:
                    continue

                logger.info(f"  [检测] {resp['method']} {resp['url'][:80]}... 包含 {keyword_count} 个岗位关键词")

                # 尝试提取数据列表
                data_list = self._find_data_list(body)
                if not data_list or len(data_list) < 1:
                    continue

                # 尝试解析岗位数据
                parsed_jobs = []
                for item in data_list[:50]:  # 限制最多50条
                    job = self._auto_parse_job(item, company_name)
                    if job and job.get('job_title'):
                        parsed_jobs.append(job)

                if parsed_jobs:
                    jobs.extend(parsed_jobs)
                    logger.info(f"  [成功] 自动提取到 {len(parsed_jobs)} 条岗位")
                    break  # 找到一个有效的 API 就够了

        except Exception as e:
            logger.error(f"API 检测失败: {e}")
        finally:
            page.close()

        return jobs

    def _find_data_list(self, response_data):
        """
        从 API 响应中查找数据列表
        支持常见的数据结构：直接列表、嵌套在 data/content/result 等字段中
        """
        # 直接是列表
        if isinstance(response_data, list) and len(response_data) >= 1:
            return response_data

        if isinstance(response_data, dict):
            # 在常见字段中查找列表
            for key in ['data', 'content', 'result', 'list', 'records', 'items', 'datas', 'rows']:
                value = response_data.get(key)
                if isinstance(value, list) and len(value) >= 1:
                    return value
                # 嵌套一层
                if isinstance(value, dict):
                    for inner_key in ['list', 'records', 'items', 'datas', 'rows', 'data']:
                        inner_value = value.get(inner_key)
                        if isinstance(inner_value, list) and len(inner_value) >= 1:
                            return inner_value

        return None

    def _auto_parse_job(self, item, company_name):
        """
        自动解析岗位数据，尝试从常见字段名中提取信息
        """
        if not isinstance(item, dict):
            return None

        # 岗位名称候选字段
        title_keys = ['name', 'title', 'jobTitle', 'positionName', 'jobName', 'position_title', 'job_name']
        # 地点候选字段
        location_keys = ['workLocations', 'city', 'location', 'workCity', 'work_city', 'workArea', 'address', 'workplace']
        # 描述候选字段
        desc_keys = ['description', 'desc', 'jobDesc', 'job_desc', 'content', 'requirement', 'duty', 'responsibility']
        # 薪资候选字段
        salary_keys = ['salary', 'salaryDesc', 'salary_desc', 'pay', 'wage', 'compensation']
        # 学历候选字段
        edu_keys = ['education', 'degree', 'eduReq', 'edu_req']
        # 日期候选字段
        date_keys = ['publishTime', 'createTime', 'updateTime', 'date', 'publishDate', 'refreshTime', 'createdate']
        # URL候选字段
        url_keys = ['url', 'detailUrl', 'link', 'href', 'positionUrl', 'jobUrl']

        def find_value(keys):
            for key in keys:
                if key in item:
                    return item[key]
            return None

        job_title = find_value(title_keys) or ''
        location = find_value(location_keys) or ''
        job_desc = find_value(desc_keys) or ''
        salary = find_value(salary_keys) or ''
        education = find_value(edu_keys) or ''
        publish_date = find_value(date_keys) or ''
        job_url = find_value(url_keys) or ''

        # 处理地点是数组的情况
        if isinstance(location, list):
            location = ' / '.join(str(loc) for loc in location if loc)

        # 处理描述字段
        if isinstance(job_desc, list):
            job_desc = '\n'.join(str(d) for d in job_desc if d)

        # 判断岗位类型
        job_type = 'graduate'
        title_lower = str(job_title).lower()
        if '实习' in title_lower or 'intern' in title_lower:
            job_type = 'intern'

        if not job_title:
            return None

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


def run_api_crawler():
    """运行 API 爬虫"""
    crawler = ApiCrawler()
    return crawler.run()
