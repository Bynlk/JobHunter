# -*- coding: utf-8 -*-
"""
数据库模型模块
负责 SQLite 数据库的初始化、建表以及 CRUD 操作
"""

import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager

from config import DATABASE_PATH

# 配置日志
logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """
    获取数据库连接的上下文管理器
    自动处理连接的打开和关闭，以及事务的提交和回滚
    """
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
    conn.execute("PRAGMA journal_mode=WAL")  # 启用 WAL 模式提高并发性能
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"数据库操作失败: {e}")
        raise
    finally:
        conn.close()


def init_database():
    """
    初始化数据库，创建必要的表和索引
    在 Flask 应用启动时调用
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 创建岗位表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                location TEXT DEFAULT '',
                salary TEXT DEFAULT '',
                job_type TEXT DEFAULT '',
                education TEXT DEFAULT '',
                publish_date TEXT DEFAULT '',
                job_desc TEXT DEFAULT '',
                job_url TEXT NOT NULL UNIQUE,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_job_url ON jobs(job_url)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company_name ON jobs(company_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source ON jobs(source)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_job_type ON jobs(job_type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_publish_date ON jobs(publish_date)
        ''')

        # 迁移：新增行业、公司性质、公司规模、福利列
        for col in ['industry', 'company_nature', 'company_size', 'welfare']:
            try:
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col} TEXT DEFAULT ''")
                logger.info(f"数据库迁移：新增列 {col}")
            except sqlite3.OperationalError:
                pass  # 列已存在

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_industry ON jobs(industry)
        ''')

        logger.info("数据库初始化完成")


def insert_job(job_data):
    """
    插入单条岗位数据
    如果 job_url 已存在，则更新该记录
    
    Args:
        job_data: 包含岗位信息的字典
    
    Returns:
        int: 插入或更新的记录 ID
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute('SELECT id FROM jobs WHERE job_url = ?', (job_data.get('job_url', ''),))
        existing = cursor.fetchone()
        
        if existing:
            # 更新已存在的记录
            cursor.execute('''
                UPDATE jobs SET
                    job_title = ?,
                    company_name = ?,
                    location = ?,
                    salary = ?,
                    job_type = ?,
                    education = ?,
                    publish_date = ?,
                    job_desc = ?,
                    source = ?,
                    industry = CASE WHEN ? != '' THEN ? ELSE industry END,
                    company_nature = CASE WHEN ? != '' THEN ? ELSE company_nature END,
                    company_size = CASE WHEN ? != '' THEN ? ELSE company_size END,
                    welfare = CASE WHEN ? != '' THEN ? ELSE welfare END,
                    updated_at = ?
                WHERE job_url = ?
            ''', (
                job_data.get('job_title', ''),
                job_data.get('company_name', ''),
                job_data.get('location', ''),
                job_data.get('salary', ''),
                job_data.get('job_type', ''),
                job_data.get('education', ''),
                job_data.get('publish_date', ''),
                job_data.get('job_desc', ''),
                job_data.get('source', ''),
                job_data.get('industry', ''), job_data.get('industry', ''),
                job_data.get('company_nature', ''), job_data.get('company_nature', ''),
                job_data.get('company_size', ''), job_data.get('company_size', ''),
                job_data.get('welfare', ''), job_data.get('welfare', ''),
                now,
                job_data.get('job_url', '')
            ))
            logger.debug(f"更新岗位: {job_data.get('job_title', '')} - {job_data.get('company_name', '')}")
            return existing['id']
        else:
            # 插入新记录
            cursor.execute('''
                INSERT INTO jobs (
                    job_title, company_name, location, salary, job_type,
                    education, publish_date, job_desc, job_url, source,
                    industry, company_nature, company_size, welfare,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data.get('job_title', ''),
                job_data.get('company_name', ''),
                job_data.get('location', ''),
                job_data.get('salary', ''),
                job_data.get('job_type', ''),
                job_data.get('education', ''),
                job_data.get('publish_date', ''),
                job_data.get('job_desc', ''),
                job_data.get('job_url', ''),
                job_data.get('source', ''),
                job_data.get('industry', ''),
                job_data.get('company_nature', ''),
                job_data.get('company_size', ''),
                job_data.get('welfare', ''),
                now,
                now
            ))
            logger.debug(f"插入岗位: {job_data.get('job_title', '')} - {job_data.get('company_name', '')}")
            return cursor.lastrowid


def batch_insert_jobs(jobs_list):
    """
    批量插入岗位数据（使用单个连接和事务）

    Args:
        jobs_list: 岗位数据字典的列表

    Returns:
        tuple: (新增数量, 更新数量)
    """
    inserted_count = 0
    updated_count = 0
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for job_data in jobs_list:
            try:
                cursor.execute('SELECT id FROM jobs WHERE job_url = ?', (job_data.get('job_url', ''),))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute('''
                        UPDATE jobs SET
                            job_title = ?,
                            company_name = ?,
                            location = ?,
                            salary = ?,
                            job_type = ?,
                            education = ?,
                            publish_date = ?,
                            job_desc = ?,
                            source = ?,
                            industry = CASE WHEN ? != '' THEN ? ELSE industry END,
                            company_nature = CASE WHEN ? != '' THEN ? ELSE company_nature END,
                            company_size = CASE WHEN ? != '' THEN ? ELSE company_size END,
                            welfare = CASE WHEN ? != '' THEN ? ELSE welfare END,
                            updated_at = ?
                        WHERE job_url = ?
                    ''', (
                        job_data.get('job_title', ''),
                        job_data.get('company_name', ''),
                        job_data.get('location', ''),
                        job_data.get('salary', ''),
                        job_data.get('job_type', ''),
                        job_data.get('education', ''),
                        job_data.get('publish_date', ''),
                        job_data.get('job_desc', ''),
                        job_data.get('source', ''),
                        job_data.get('industry', ''), job_data.get('industry', ''),
                        job_data.get('company_nature', ''), job_data.get('company_nature', ''),
                        job_data.get('company_size', ''), job_data.get('company_size', ''),
                        job_data.get('welfare', ''), job_data.get('welfare', ''),
                        now,
                        job_data.get('job_url', '')
                    ))
                    updated_count += 1
                else:
                    cursor.execute('''
                        INSERT INTO jobs (
                            job_title, company_name, location, salary, job_type,
                            education, publish_date, job_desc, job_url, source,
                            industry, company_nature, company_size, welfare,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job_data.get('job_title', ''),
                        job_data.get('company_name', ''),
                        job_data.get('location', ''),
                        job_data.get('salary', ''),
                        job_data.get('job_type', ''),
                        job_data.get('education', ''),
                        job_data.get('publish_date', ''),
                        job_data.get('job_desc', ''),
                        job_data.get('job_url', ''),
                        job_data.get('source', ''),
                        job_data.get('industry', ''),
                        job_data.get('company_nature', ''),
                        job_data.get('company_size', ''),
                        job_data.get('welfare', ''),
                        now,
                        now
                    ))
                    inserted_count += 1
            except Exception as e:
                logger.error(f"插入岗位数据失败: {job_data.get('job_title', '未知')} - {e}")
                continue

    logger.info(f"批量插入完成: 新增 {inserted_count} 条, 更新 {updated_count} 条")
    return inserted_count, updated_count


def query_jobs(keyword=None, company=None, location=None, job_type=None,
               salary_min=None, salary_max=None, date_from=None, date_to=None,
               source=None, industry=None, company_nature=None, education=None,
               page=1, per_page=20):
    """
    查询岗位列表，支持多条件筛选和分页

    Args:
        keyword: 岗位关键词
        company: 公司名称
        location: 工作地点
        job_type: 岗位类型 (intern/graduate/all)
        salary_min: 最低薪资
        salary_max: 最高薪资
        date_from: 开始日期
        date_to: 结束日期
        source: 数据来源（逗号分隔的多个值）
        industry: 行业筛选
        company_nature: 公司性质（国企/民企/外企）
        education: 学历要求
        page: 页码
        per_page: 每页条数

    Returns:
        dict: { data: [...], total: 总条数, page: 当前页, per_page: 每页条数 }
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if keyword:
            conditions.append("(job_title LIKE ? OR company_name LIKE ? OR job_desc LIKE ?)")
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        if company:
            conditions.append("company_name LIKE ?")
            params.append(f'%{company}%')
        
        if location:
            location_list = [loc.strip() for loc in location.split(',') if loc.strip()]
            if location_list:
                loc_conditions = []
                for loc in location_list:
                    loc_conditions.append("location LIKE ?")
                    params.append(f'%{loc}%')
                conditions.append(f"({' OR '.join(loc_conditions)})")
        
        if job_type and job_type != 'all':
            conditions.append("job_type = ?")
            params.append(job_type)
        
        if salary_min:
            # 从薪资字符串中提取最低薪资数字，如 "15K-25K" → 15
            conditions.append("""
                CASE
                    WHEN salary LIKE '%K-%' THEN CAST(REPLACE(SUBSTR(salary, 1, INSTR(salary, '-') - 1), 'K', '') AS INTEGER)
                    WHEN salary LIKE '%k-%' THEN CAST(REPLACE(SUBSTR(salary, 1, INSTR(salary, '-') - 1), 'k', '') AS INTEGER)
                    ELSE 0
                END >= ?
            """)
            params.append(salary_min)

        if salary_max:
            # 从薪资字符串中提取最高薪资数字，如 "15K-25K" → 25
            conditions.append("""
                CASE
                    WHEN salary LIKE '%K-%' THEN CAST(REPLACE(SUBSTR(salary, INSTR(salary, '-') + 1, INSTR(SUBSTR(salary, INSTR(salary, '-') + 1), 'K') - 1), 'K', '') AS INTEGER)
                    WHEN salary LIKE '%k-%' THEN CAST(REPLACE(SUBSTR(salary, INSTR(salary, '-') + 1, INSTR(SUBSTR(salary, INSTR(salary, '-') + 1), 'k') - 1), 'k', '') AS INTEGER)
                    ELSE 999999
                END <= ?
            """)
            params.append(salary_max)
        
        if date_from:
            conditions.append("publish_date >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("publish_date <= ?")
            params.append(date_to)
        
        if source:
            # 支持多个来源，用逗号分隔
            source_list = [s.strip() for s in source.split(',')]
            placeholders = ','.join(['?' for _ in source_list])
            conditions.append(f"source IN ({placeholders})")
            params.extend(source_list)

        if industry:
            conditions.append("industry LIKE ?")
            params.append(f'%{industry}%')

        if company_nature:
            conditions.append("company_nature = ?")
            params.append(company_nature)

        if education:
            conditions.append("education LIKE ?")
            params.append(f'%{education}%')

        # 构建 WHERE 子句
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM jobs WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询分页数据
        offset = (page - 1) * per_page
        query_sql = f"""
            SELECT id, job_title, company_name, location, salary, job_type,
                   education, publish_date, job_desc, job_url, source,
                   industry, company_nature, company_size, welfare,
                   created_at, updated_at
            FROM jobs
            WHERE {where_clause}
            ORDER BY publish_date DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query_sql, params + [per_page, offset])
        rows = cursor.fetchall()

        # 转换为字典列表
        data = []
        for row in rows:
            data.append({
                'id': row['id'],
                'job_title': row['job_title'],
                'company_name': row['company_name'],
                'location': row['location'],
                'salary': row['salary'],
                'job_type': row['job_type'],
                'education': row['education'],
                'publish_date': row['publish_date'],
                'job_desc': row['job_desc'],
                'job_url': row['job_url'],
                'source': row['source'],
                'industry': row['industry'],
                'company_nature': row['company_nature'],
                'company_size': row['company_size'],
                'welfare': row['welfare'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
            })
        
        return {
            'data': data,
            'total': total,
            'page': page,
            'per_page': per_page
        }


def get_job_by_id(job_id):
    """
    根据 ID 获取单个岗位的完整信息
    
    Args:
        job_id: 岗位 ID
    
    Returns:
        dict: 岗位信息字典，不存在则返回 None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'job_title': row['job_title'],
                'company_name': row['company_name'],
                'location': row['location'],
                'salary': row['salary'],
                'job_type': row['job_type'],
                'education': row['education'],
                'publish_date': row['publish_date'],
                'job_desc': row['job_desc'],
                'job_url': row['job_url'],
                'source': row['source'],
                'industry': row['industry'],
                'company_nature': row['company_nature'],
                'company_size': row['company_size'],
                'welfare': row['welfare'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
            }
        return None


def get_all_companies():
    """
    获取数据库中所有不重复的公司名称列表
    
    Returns:
        list: 公司名称列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT company_name FROM jobs ORDER BY company_name')
        rows = cursor.fetchall()
        return [row['company_name'] for row in rows]


def get_stats():
    """
    获取数据库统计信息
    
    Returns:
        dict: 包含总数、各来源数量、最后更新时间
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 总数
        cursor.execute('SELECT COUNT(*) as total FROM jobs')
        total = cursor.fetchone()['total']
        
        # 各来源数量
        cursor.execute('SELECT source, COUNT(*) as count FROM jobs GROUP BY source')
        sources = {}
        for row in cursor.fetchall():
            sources[row['source']] = row['count']
        
        # 最后更新时间
        cursor.execute('SELECT MAX(updated_at) as last_updated FROM jobs')
        result = cursor.fetchone()
        last_updated = result['last_updated'] if result else ''
        
        return {
            'total_jobs': total,
            'sources': sources,
            'last_updated': last_updated
        }


def clear_all_jobs():
    """
    清空所有岗位数据

    Returns:
        int: 被删除的记录数
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as cnt FROM jobs')
        count = cursor.fetchone()['cnt']
        cursor.execute('DELETE FROM jobs')
        logger.info(f"已清空 {count} 条岗位数据")
        return count


def export_jobs(keyword=None, company=None, location=None, job_type=None,
                salary_min=None, salary_max=None, date_from=None, date_to=None,
                source=None, industry=None, company_nature=None, education=None):
    """
    导出岗位数据（不分页，返回所有符合条件的数据）
    复用 query_jobs 的筛选逻辑，使用大分页获取全部数据
    """
    result = query_jobs(
        keyword=keyword, company=company, location=location, job_type=job_type,
        salary_min=salary_min, salary_max=salary_max, date_from=date_from, date_to=date_to,
        source=source, industry=industry, company_nature=company_nature, education=education,
        page=1, per_page=100000
    )
    return result['data']


def get_all_industries():
    """
    获取数据库中所有不重复的行业列表

    Returns:
        list: 行业名称列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT industry FROM jobs WHERE industry != '' ORDER BY industry")
        rows = cursor.fetchall()
        return [row['industry'] for row in rows]


def get_all_locations():
    """
    获取数据库中所有不重复的工作地点列表

    Returns:
        list: 地点名称列表
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT location FROM jobs WHERE location != '' ORDER BY location")
        rows = cursor.fetchall()
        return [row['location'] for row in rows]
