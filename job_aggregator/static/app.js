/**
 * 实习&校招岗位聚合站 - Vue 3 应用逻辑
 * 现代化 UI + 毛玻璃效果
 */

const { createApp, ref, reactive, computed, onMounted } = Vue;

const app = createApp({
    setup() {
        // ==================== 响应式数据 ====================

        const jobs = ref([]);
        const total = ref(0);
        const currentPage = ref(1);
        const perPage = ref(20);
        const loading = ref(false);

        const filters = reactive({
            keyword: '',
            company: '',
            location: '',
            job_type: 'all',
            salary_min: null,
            salary_max: null,
            date_from: '',
            date_to: '',
            source: '',
            industry: '',
            company_nature: '',
            education: ''
        });

        const companies = ref([]);
        const industries = ref([]);
        const stats = reactive({ total_jobs: 0, sources: {}, last_updated: '' });

        const crawlStatus = reactive({ status: 'idle', progress: '', total_new: 0, error_message: '' });
        const crawlSource = ref('all');
        const jumpPage = ref(1);
        const sidebarCollapsed = ref(false);

        let crawlPollTimer = null;
        let lastTotalNew = 0;

        const crawlOptions = [
            { value: 'all', label: '全部数据源' },
            { value: 'shixiseng', label: '实习僧' },
            { value: 'ncss', label: '国家平台' },
            { value: 'websites', label: '150+ 大厂官网' }
        ];

        // ==================== 计算属性 ====================

        const totalPages = computed(() => Math.ceil(total.value / perPage.value));

        const displayPages = computed(() => {
            const pages = [];
            const t = totalPages.value;
            const c = currentPage.value;

            if (t <= 7) {
                for (let i = 1; i <= t; i++) pages.push(i);
            } else {
                pages.push(1);
                if (c > 4) pages.push('...');
                const start = Math.max(2, c - 2);
                const end = Math.min(t - 1, c + 2);
                for (let i = start; i <= end; i++) pages.push(i);
                if (c < t - 3) pages.push('...');
                pages.push(t);
            }
            return pages;
        });

        // ==================== 方法 ====================

        async function fetchJobs() {
            loading.value = true;
            try {
                const params = new URLSearchParams();
                if (filters.keyword) params.append('keyword', filters.keyword);
                if (filters.company) params.append('company', filters.company);
                if (filters.location) params.append('location', filters.location);
                if (filters.job_type && filters.job_type !== 'all') params.append('job_type', filters.job_type);
                if (filters.salary_min) params.append('salary_min', filters.salary_min);
                if (filters.salary_max) params.append('salary_max', filters.salary_max);
                if (filters.date_from) params.append('date_from', filters.date_from);
                if (filters.date_to) params.append('date_to', filters.date_to);
                if (filters.source) params.append('source', filters.source);
                if (filters.industry) params.append('industry', filters.industry);
                if (filters.company_nature) params.append('company_nature', filters.company_nature);
                if (filters.education) params.append('education', filters.education);
                params.append('page', currentPage.value);
                params.append('per_page', perPage.value);

                const response = await fetch(`/api/jobs?${params.toString()}`);
                const data = await response.json();

                if (response.ok) {
                    jobs.value = (data.data || []).map(job => ({ ...job, _expanded: false }));
                    total.value = data.total || 0;
                    currentPage.value = data.page || 1;
                }
            } catch (error) {
                console.error('获取岗位列表失败:', error);
            } finally {
                loading.value = false;
            }
        }

        async function fetchCompanies() {
            try {
                const response = await fetch('/api/companies');
                if (response.ok) companies.value = await response.json();
            } catch (error) {
                console.error('获取公司列表失败:', error);
            }
        }

        async function fetchIndustries() {
            try {
                const response = await fetch('/api/industries');
                if (response.ok) industries.value = await response.json();
            } catch (error) {
                console.error('获取行业列表失败:', error);
            }
        }

        async function fetchStats() {
            try {
                const response = await fetch('/api/stats');
                if (response.ok) {
                    const data = await response.json();
                    stats.total_jobs = data.total_jobs || 0;
                    stats.last_updated = data.last_updated || '';
                    stats.sources = {};
                    Object.assign(stats.sources, data.sources || {});
                }
            } catch (error) {
                console.error('获取统计数据失败:', error);
            }
        }

        function searchJobs() {
            currentPage.value = 1;
            jumpPage.value = 1;
            fetchJobs();
        }

        function resetFilters() {
            Object.assign(filters, {
                keyword: '', company: '', location: '', job_type: 'all',
                salary_min: null, salary_max: null, date_from: '', date_to: '', source: '',
                industry: '', company_nature: '', education: ''
            });
            currentPage.value = 1;
            jumpPage.value = 1;
            fetchJobs();
        }

        function goToPage(page) {
            const num = parseInt(page);
            if (num >= 1 && num <= totalPages.value) {
                currentPage.value = num;
                jumpPage.value = num;
                fetchJobs();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }

        async function startCrawl() {
            try {
                const response = await fetch('/api/crawl', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source: crawlSource.value })
                });
                const data = await response.json();
                if (response.ok) {
                    lastTotalNew = 0;
                    startCrawlStatusPolling();
                } else {
                    alert(data.error || '启动爬虫失败');
                }
            } catch (error) {
                console.error('启动爬虫异常:', error);
                alert('启动爬虫失败: ' + error.message);
            }
        }

        function startCrawlStatusPolling() {
            if (crawlPollTimer) clearInterval(crawlPollTimer);

            crawlPollTimer = setInterval(async () => {
                try {
                    const response = await fetch('/api/crawl/status');
                    const data = await response.json();

                    crawlStatus.status = data.status;
                    crawlStatus.progress = data.progress;
                    crawlStatus.total_new = data.total_new;
                    crawlStatus.error_message = data.error_message;

                    if (data.total_new > lastTotalNew) {
                        lastTotalNew = data.total_new;
                        fetchJobs();
                        fetchStats();
                        fetchCompanies();
                        fetchIndustries();
                    }

                    if (data.status === 'done' || data.status === 'error') {
                        clearInterval(crawlPollTimer);
                        crawlPollTimer = null;
                        fetchJobs();
                        fetchStats();
                        fetchCompanies();
                        fetchIndustries();
                    }
                } catch (error) {
                    console.error('轮询爬虫状态失败:', error);
                }
            }, 2000);
        }

        function exportExcel() {
            const params = new URLSearchParams();
            if (filters.keyword) params.append('keyword', filters.keyword);
            if (filters.company) params.append('company', filters.company);
            if (filters.location) params.append('location', filters.location);
            if (filters.job_type && filters.job_type !== 'all') params.append('job_type', filters.job_type);
            if (filters.salary_min) params.append('salary_min', filters.salary_min);
            if (filters.salary_max) params.append('salary_max', filters.salary_max);
            if (filters.date_from) params.append('date_from', filters.date_from);
            if (filters.date_to) params.append('date_to', filters.date_to);
            if (filters.source) params.append('source', filters.source);
            window.open(`/api/export?${params.toString()}`, '_blank');
        }

        // ==================== 生命周期 ====================

        onMounted(() => {
            fetchJobs();
            fetchCompanies();
            fetchIndustries();
            fetchStats();

            fetch('/api/crawl/status')
                .then(res => res.json())
                .then(data => {
                    Object.assign(crawlStatus, data);
                    lastTotalNew = data.total_new || 0;
                    if (data.status === 'running') startCrawlStatusPolling();
                })
                .catch(err => console.error('检查爬虫状态失败:', err));
        });

        return {
            jobs, total, currentPage, perPage, loading,
            filters, companies, industries, stats, crawlStatus, crawlSource,
            jumpPage, sidebarCollapsed, crawlOptions,
            totalPages, displayPages,
            fetchJobs, fetchIndustries, searchJobs, resetFilters, goToPage,
            startCrawl, exportExcel
        };
    }
});

app.mount('#app');
