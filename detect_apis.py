# -*- coding: utf-8 -*-
"""
自动化 API 检测脚本
打开各大厂招聘网页，监听网络请求，自动识别岗位数据 API
"""

import json
import time
import sys
import io
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 岗位相关的关键词
JOB_KEYWORDS_IN_URL = [
    'job', 'position', 'career', 'recruit', 'campus', 'intern',
    'search', 'list', 'query', 'v1', 'v2', 'api'
]

JOB_KEYWORDS_IN_DATA = [
    'title', 'name', 'position', 'job', 'city', 'location',
    'salary', 'degree', 'education', 'department', 'company',
    'workCity', 'jobTitle', 'positionName', 'jobName'
]


def is_job_api(url, method, response_data):
    """
    判断是否为岗位相关的 API

    Args:
        url: 请求 URL
        method: 请求方法
        response_data: 响应数据（dict 或 list）

    Returns:
        (bool, str): (是否为岗位 API, 原因)
    """
    url_lower = url.lower()

    # 排除明显的非岗位 API
    exclude_patterns = [
        '.css', '.js', '.png', '.jpg', '.gif', '.svg', '.ico', '.woff',
        'analytics', 'tracking', 'log', 'stat', 'beacon',
        'captcha', 'verify', 'auth', 'login', 'logout',
        'config', 'setting', 'preference',
        'chat', 'message', 'notification',
        'payment', 'order', 'cart',
    ]
    for pattern in exclude_patterns:
        if pattern in url_lower:
            return False, f"排除: {pattern}"

    # 检查 URL 是否包含岗位关键词
    url_has_keyword = any(kw in url_lower for kw in JOB_KEYWORDS_IN_URL)

    # 检查响应数据
    data_str = json.dumps(response_data, ensure_ascii=False).lower()

    # 统计数据中出现的岗位关键词数量
    keyword_count = sum(1 for kw in JOB_KEYWORDS_IN_DATA if kw in data_str)

    # 判断逻辑
    if keyword_count >= 3:
        return True, f"数据包含 {keyword_count} 个岗位关键词"

    if url_has_keyword and keyword_count >= 2:
        return True, f"URL+数据匹配 (关键词: {keyword_count})"

    # 检查是否是列表数据且每项都有类似结构
    if isinstance(response_data, dict):
        # 查找可能的数据字段
        for key in ['data', 'content', 'result', 'list', 'records', 'items', 'datas']:
            value = response_data.get(key)
            if isinstance(value, list) and len(value) >= 2:
                # 检查列表项是否包含岗位字段
                item_str = json.dumps(value[0], ensure_ascii=False).lower()
                item_keywords = sum(1 for kw in JOB_KEYWORDS_IN_DATA if kw in item_str)
                if item_keywords >= 2:
                    return True, f"列表数据 [{key}] 包含 {item_keywords} 个岗位关键词"

    return False, "不匹配"


def extract_api_info(response_data):
    """
    从响应数据中提取岗位列表和字段映射

    Returns:
        dict: {
            'data_path': 数据路径,
            'total_count': 总数,
            'sample_fields': 样本字段,
            'field_mapping': 建议的字段映射
        }
    """
    info = {
        'data_path': '',
        'total_count': 0,
        'sample_fields': [],
        'field_mapping': {}
    }

    # 查找数据列表
    if isinstance(response_data, list):
        info['data_path'] = '(root)'
        if response_data:
            info['sample_fields'] = list(response_data[0].keys())[:20]
            info['total_count'] = len(response_data)
            info['field_mapping'] = guess_field_mapping(response_data[0])
        return info

    if isinstance(response_data, dict):
        # 查找可能的数据字段
        for key in ['data', 'content', 'result', 'list', 'records', 'items', 'datas', 'rows']:
            value = response_data.get(key)
            if isinstance(value, list) and len(value) >= 1:
                info['data_path'] = key
                info['sample_fields'] = list(value[0].keys())[:20]
                info['total_count'] = len(value)
                info['field_mapping'] = guess_field_mapping(value[0])

                # 检查是否有总数字段
                for count_key in ['total', 'totalCount', 'count', 'totalNum', 'totalItems']:
                    if count_key in response_data:
                        info['total_count'] = response_data[count_key]
                        break

                return info

            # 有些 API 数据在嵌套对象中
            if isinstance(value, dict):
                for inner_key in ['list', 'records', 'items', 'datas', 'rows']:
                    inner_value = value.get(inner_key)
                    if isinstance(inner_value, list) and len(inner_value) >= 1:
                        info['data_path'] = f"{key}.{inner_key}"
                        info['sample_fields'] = list(inner_value[0].keys())[:20]
                        info['total_count'] = len(inner_value)
                        info['field_mapping'] = guess_field_mapping(inner_value[0])

                        for count_key in ['total', 'totalCount', 'count']:
                            if count_key in value:
                                info['total_count'] = value[count_key]
                                break

                        return info

    return info


def guess_field_mapping(sample_item):
    """
    根据样本数据猜测字段映射

    Returns:
        dict: {'job_title': 'name', 'location': 'city', ...}
    """
    mapping = {}
    fields = sample_item.keys()

    # 岗位名称
    for key in ['name', 'title', 'jobTitle', 'positionName', 'jobName', 'position_title']:
        if key in fields:
            mapping['job_title'] = key
            break

    # 工作地点
    for key in ['workLocations', 'city', 'location', 'workCity', 'work_city', 'address']:
        if key in fields:
            mapping['location'] = key
            break

    # 薪资
    for key in ['salary', 'salaryDesc', 'salary_desc', 'pay', 'wage', 'compensation']:
        if key in fields:
            mapping['salary'] = key
            break

    # 学历
    for key in ['education', 'degree', 'eduReq', 'edu_req', '学历']:
        if key in fields:
            mapping['education'] = key
            break

    # 岗位描述
    for key in ['description', 'desc', 'jobDesc', 'job_desc', 'content', 'requirement']:
        if key in fields:
            mapping['job_desc'] = key
            break

    # 岗位链接
    for key in ['url', 'detailUrl', 'link', 'href', 'positionUrl', 'jobUrl']:
        if key in fields:
            mapping['job_url'] = key
            break

    # 发布日期
    for key in ['publishTime', 'createTime', 'updateTime', 'date', 'publishDate']:
        if key in fields:
            mapping['publish_date'] = key
            break

    return mapping


def detect_api_for_company(page, company_name, url, timeout=10):
    """
    检测单个公司的 API

    Returns:
        list: 检测到的 API 列表
    """
    print(f"\n{'='*60}")
    print(f"检测: {company_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    detected_apis = []
    all_responses = []

    def handle_response(response):
        """监听网络响应"""
        try:
            content_type = response.headers.get('content-type', '')
            if 'json' not in content_type:
                return
            if response.status != 200:
                return

            resp_url = response.url
            method = response.request.method

            # 排除一些明显的资源请求
            if any(ext in resp_url for ext in ['.js', '.css', '.png', '.jpg']):
                return

            try:
                body = response.json()
                all_responses.append({
                    'url': resp_url,
                    'method': method,
                    'body': body,
                    'post_data': response.request.post_data,
                })
            except:
                pass
        except:
            pass

    page.on('response', handle_response)

    try:
        # 访问页面
        page.goto(url, wait_until='domcontentloaded', timeout=15000)

        # 等待页面加载和 API 请求
        time.sleep(3)

        # 滚动页面触发更多 API
        for i in range(3):
            page.evaluate(f'window.scrollBy(0, {300 + i * 200})')
            time.sleep(1)

        # 再等待一下可能的延迟请求
        time.sleep(1)

        print(f"\n捕获到 {len(all_responses)} 个 JSON 响应")

        # 分析每个响应
        for resp in all_responses:
            is_job, reason = is_job_api(resp['url'], resp['method'], resp['body'])
            if is_job:
                api_info = extract_api_info(resp['body'])

                detected = {
                    'url': resp['url'],
                    'method': resp['method'],
                    'post_data': resp['post_data'],
                    'reason': reason,
                    'data_path': api_info['data_path'],
                    'total_count': api_info['total_count'],
                    'sample_fields': api_info['sample_fields'],
                    'field_mapping': api_info['field_mapping'],
                }
                detected_apis.append(detected)

                print(f"\n  [OK] 发现岗位 API!")
                print(f"       URL: {resp['url'][:80]}...")
                print(f"       方法: {resp['method']}")
                print(f"       原因: {reason}")
                print(f"       数据路径: {api_info['data_path']}")
                print(f"       字段: {api_info['sample_fields'][:10]}")
                print(f"       字段映射: {api_info['field_mapping']}")

        if not detected_apis:
            print(f"\n  [X] 未发现岗位 API")
            # 打印所有捕获的 API 供参考
            if all_responses:
                print(f"\n  所有捕获的 JSON 响应:")
                for i, resp in enumerate(all_responses[:10]):
                    print(f"    {i+1}. {resp['method']} {resp['url'][:80]}...")

    except Exception as e:
        print(f"\n  [X] 检测失败: {e}")
    finally:
        page.remove_listener('response', handle_response)

    return detected_apis


def main():
    """主函数"""
    # 加载公司配置
    with open('config/company_urls.json', 'r', encoding='utf-8') as f:
        companies = json.load(f)

    print(f"共加载 {len(companies)} 家公司")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检测所有公司
    test_companies = companies

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )

        stealth = Stealth()
        page = context.new_page()
        stealth.apply_stealth_sync(page)

        for idx, company in enumerate(test_companies):
            name = company['name']
            url = company['url']

            print(f"\n\n[{idx+1}/{len(test_companies)}] {name}")

            apis = detect_api_for_company(page, name, url)

            result = {
                'name': name,
                'url': url,
                'apis_found': len(apis),
                'apis': apis,
            }
            all_results.append(result)

            # 公司间延迟
            if idx < len(test_companies) - 1:
                time.sleep(2)

        browser.close()

    # 保存结果
    output_file = 'config/api_detection_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # 打印汇总
    print(f"\n\n{'='*60}")
    print(f"检测完成！结果已保存到: {output_file}")
    print(f"{'='*60}")

    print(f"\n汇总:")
    found = [r for r in all_results if r['apis_found'] > 0]
    not_found = [r for r in all_results if r['apis_found'] == 0]

    print(f"\n  发现 API 的公司 ({len(found)}):")
    for r in found:
        print(f"    - {r['name']}: {r['apis_found']} 个 API")
        for api in r['apis']:
            print(f"      {api['method']} {api['url'][:60]}...")

    print(f"\n  未发现 API 的公司 ({len(not_found)}):")
    for r in not_found:
        print(f"    - {r['name']}")

    # 生成 API 配置代码
    print(f"\n\n{'='*60}")
    print("生成的 API 配置代码（可直接复制到 api_crawler.py）:")
    print(f"{'='*60}")

    for r in found:
        for api in r['apis']:
            if api['field_mapping'].get('job_title'):
                print(f'\n        "{r["name"]}": {{')
                print(f'            "api_url": "{api["url"].split("?")[0]}",')
                print(f'            "method": "{api["method"]}",')
                print(f'            "headers": {{')
                print(f'                "Content-Type": "application/json",')
                print(f'                "Accept": "application/json",')
                print(f'            }},')
                if api['post_data']:
                    try:
                        payload = json.loads(api['post_data'])
                        print(f'            "payload": {json.dumps(payload, ensure_ascii=False)},')
                    except:
                        print(f'            "payload": {{}},')
                else:
                    print(f'            "payload": {{}},')
                print(f'            "referer": "{r["url"]}",')
                print(f'            "data_path": "{api["data_path"]}",')
                print(f'            "field_mapping": {json.dumps(api["field_mapping"], ensure_ascii=False)},')
                print(f'        }},')


if __name__ == '__main__':
    main()
