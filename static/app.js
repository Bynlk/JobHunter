/**
 * JobHunter - Vue 3 应用逻辑
 * 模糊搜索 + 地区层级多选 + Toast 通知 + 骨架屏
 */

// ==================== 工具函数 ====================

function debounce(fn, delay) {
    let timer = null;
    const debounced = function (...args) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
            fn.apply(this, args);
            timer = null;
        }, delay);
    };
    debounced.cancel = function () {
        if (timer) { clearTimeout(timer); timer = null; }
    };
    return debounced;
}

// ==================== 中国省市数据 ====================

const PROVINCE_CITY_MAP = {
    '北京': ['北京市'],
    '天津': ['天津市'],
    '上海': ['上海市'],
    '重庆': ['重庆市'],
    '广东': ['广州', '深圳', '珠海', '汕头', '佛山', '东莞', '中山', '惠州', '江门', '湛江', '茂名', '肇庆', '梅州', '揭阳', '清远', '韶关', '河源', '潮州', '阳江', '云浮', '汕尾'],
    '浙江': ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水'],
    '江苏': ['南京', '苏州', '无锡', '常州', '南通', '徐州', '盐城', '扬州', '镇江', '泰州', '淮安', '连云港', '宿迁'],
    '山东': ['济南', '青岛', '烟台', '潍坊', '临沂', '淄博', '济宁', '泰安', '聊城', '威海', '德州', '枣庄', '日照', '菏泽', '滨州', '东营'],
    '四川': ['成都', '绵阳', '德阳', '宜宾', '南充', '达州', '泸州', '乐山', '内江', '自贡', '遂宁', '眉山', '广安', '攀枝花', '广元', '资阳', '雅安', '巴中'],
    '湖北': ['武汉', '宜昌', '襄阳', '荆州', '黄冈', '十堰', '孝感', '荆门', '鄂州', '黄石', '咸宁', '随州', '恩施'],
    '湖南': ['长沙', '株洲', '湘潭', '衡阳', '岳阳', '常德', '邵阳', '益阳', '郴州', '永州', '怀化', '娄底', '张家界', '湘西'],
    '河南': ['郑州', '洛阳', '南阳', '许昌', '周口', '新乡', '信阳', '商丘', '驻马店', '焦作', '平顶山', '安阳', '开封', '濮阳', '鹤壁', '漯河', '三门峡'],
    '河北': ['石家庄', '唐山', '保定', '邯郸', '沧州', '廊坊', '邢台', '衡水', '承德', '张家口', '秦皇岛'],
    '福建': ['福州', '厦门', '泉州', '漳州', '莆田', '龙岩', '三明', '南平', '宁德'],
    '安徽': ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山', '阜阳', '宿州', '滁州', '六安', '亳州', '池州', '宣城'],
    '辽宁': ['沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛'],
    '江西': ['南昌', '赣州', '九江', '宜春', '上饶', '吉安', '抚州', '景德镇', '萍乡', '新余', '鹰潭'],
    '陕西': ['西安', '咸阳', '宝鸡', '渭南', '汉中', '延安', '安康', '榆林', '商洛', '铜川'],
    '黑龙江': ['哈尔滨', '大庆', '齐齐哈尔', '牡丹江', '绥化', '佳木斯', '鸡西', '双鸭山', '鹤岗', '黑河', '伊春', '七台河'],
    '广西': ['南宁', '柳州', '桂林', '玉林', '梧州', '北海', '贵港', '百色', '河池', '钦州', '防城港', '贺州', '来宾', '崇左'],
    '云南': ['昆明', '曲靖', '大理', '玉溪', '红河', '昭通', '文山', '楚雄', '普洱', '保山', '临沧', '丽江'],
    '贵州': ['贵阳', '遵义', '毕节', '黔南', '黔东南', '铜仁', '安顺', '六盘水', '黔西南'],
    '山西': ['太原', '大同', '临汾', '运城', '长治', '晋城', '忻州', '晋中', '朔州', '阳泉', '吕梁'],
    '吉林': ['长春', '吉林', '四平', '通化', '松原', '延边', '白城', '白山', '辽源'],
    '甘肃': ['兰州', '天水', '酒泉', '庆阳', '平凉', '白银', '武威', '张掖', '定西', '陇南', '金昌', '嘉峪关'],
    '内蒙古': ['呼和浩特', '包头', '鄂尔多斯', '赤峰', '通辽', '呼伦贝尔', '乌兰察布', '巴彦淖尔', '乌海'],
    '新疆': ['乌鲁木齐', '昌吉', '伊犁', '阿克苏', '喀什', '哈密', '吐鲁番', '巴音郭楞', '塔城', '克拉玛依'],
    '海南': ['海口', '三亚', '儋州'],
    '宁夏': ['银川', '石嘴山', '吴忠', '固原', '中卫'],
    '青海': ['西宁', '海东', '海西', '海南州', '海北州'],
    '西藏': ['拉萨', '日喀则', '林芝', '昌都', '山南', '那曲'],
    '台湾': ['台北', '高雄', '台中', '台南', '新北', '桃园'],
    '香港': ['香港'],
    '澳门': ['澳门'],
};

// ==================== Vue 应用 ====================

const { createApp, ref, reactive, computed, onMounted, watch, nextTick } = Vue;

const app = createApp({
    setup() {
        // ---------- Toast 通知系统 ----------
        const toasts = ref([]);
        let toastIdCounter = 0;

        function showToast(message, type = 'info', duration = 3000) {
            const id = ++toastIdCounter;
            toasts.value.push({ id, message, type, visible: true });
            setTimeout(() => {
                const idx = toasts.value.findIndex(t => t.id === id);
                if (idx !== -1) toasts.value[idx].visible = false;
                setTimeout(() => {
                    toasts.value = toasts.value.filter(t => t.id !== id);
                }, 300);
            }, duration);
        }

        // ---------- 核心数据 ----------
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

        // ---------- 搜索建议 ----------
        const searchKeyword = ref('');
        const searchSuggestions = ref([]);
        const showSuggestions = ref(false);
        const isSearching = ref(false);
        const DEBOUNCE_DELAY = 300;

        const debouncedSearch = debounce(async (keyword) => {
            if (!keyword || keyword.trim().length === 0) {
                searchSuggestions.value = [];
                showSuggestions.value = false;
                return;
            }
            isSearching.value = true;
            try {
                const params = new URLSearchParams();
                params.append('keyword', keyword.trim());
                params.append('page', '1');
                params.append('per_page', '10');
                const response = await fetch(`/api/jobs?${params.toString()}`);
                if (response.ok) {
                    const data = await response.json();
                    searchSuggestions.value = data.data || [];
                    showSuggestions.value = true;
                }
            } catch (e) {
                console.error('搜索建议失败:', e);
            } finally {
                isSearching.value = false;
            }
        }, DEBOUNCE_DELAY);

        watch(searchKeyword, (val) => {
            debouncedSearch(val);
        });

        function selectSuggestion(s) {
            filters.keyword = s.job_title;
            searchKeyword.value = s.job_title;
            showSuggestions.value = false;
            searchJobs();
        }

        // ---------- 地区层级选择器 ----------
        const selectedLocations = ref([]);
        const locationPickerOpen = ref(false);
        const expandedProvinces = ref(new Set());
        const dbLocations = ref([]);

        async function fetchLocations() {
            try {
                const response = await fetch('/api/locations');
                if (response.ok) dbLocations.value = await response.json();
            } catch (e) {
                console.error('获取地点列表失败:', e);
            }
        }

        const locationTree = computed(() => {
            const dbLocSet = new Set(dbLocations.value);
            const tree = [];
            for (const [province, cities] of Object.entries(PROVINCE_CITY_MAP)) {
                const provinceInDb = dbLocSet.has(province);
                const matchingCities = cities.filter(city => dbLocSet.has(city));
                if (provinceInDb || matchingCities.length > 0) {
                    tree.push({
                        province,
                        provinceInDb,
                        cities: matchingCities,
                        totalCount: (provinceInDb ? 1 : 0) + matchingCities.length,
                    });
                }
            }
            return tree;
        });

        function toggleProvince(province) {
            const s = new Set(expandedProvinces.value);
            if (s.has(province)) s.delete(province);
            else s.add(province);
            expandedProvinces.value = s;
        }

        function isProvinceSelected(province, cities) {
            const selSet = new Set(selectedLocations.value);
            const allItems = cities.slice();
            // 不把省份本身加入全选判断，除非省份在DB中
            // 全选 = 所有城市都被选中
            if (allItems.length === 0) return selSet.has(province);
            return allItems.every(c => selSet.has(c));
        }

        function selectAllProvince(province, cities, provinceInDb) {
            const toAdd = [...cities];
            if (provinceInDb) toAdd.push(province);
            const selSet = new Set(selectedLocations.value);
            const allSelected = toAdd.length > 0 && toAdd.every(loc => selSet.has(loc));
            if (allSelected) {
                toAdd.forEach(loc => selSet.delete(loc));
            } else {
                toAdd.forEach(loc => selSet.add(loc));
            }
            selectedLocations.value = Array.from(selSet);
        }

        function toggleLocation(loc) {
            const selSet = new Set(selectedLocations.value);
            if (selSet.has(loc)) selSet.delete(loc);
            else selSet.add(loc);
            selectedLocations.value = Array.from(selSet);
        }

        function isLocationSelected(loc) {
            return selectedLocations.value.includes(loc);
        }

        function clearLocations() {
            selectedLocations.value = [];
        }

        function getLocationParam() {
            return selectedLocations.value.join(',');
        }

        // ---------- 筛选标签 ----------
        const activeFilterTags = computed(() => {
            const tags = [];
            if (filters.keyword) tags.push({ key: 'keyword', label: `关键词: ${filters.keyword}`, icon: 'bi-search' });
            if (filters.company) tags.push({ key: 'company', label: `公司: ${filters.company}`, icon: 'bi-building' });
            if (selectedLocations.value.length > 0) {
                const label = selectedLocations.value.length <= 3
                    ? selectedLocations.value.join(', ')
                    : `${selectedLocations.value.length} 个地点`;
                tags.push({ key: 'location', label: `地点: ${label}`, icon: 'bi-geo-alt' });
            }
            if (filters.job_type && filters.job_type !== 'all') {
                tags.push({ key: 'job_type', label: filters.job_type === 'intern' ? '实习' : '校招', icon: 'bi-briefcase' });
            }
            if (filters.salary_min || filters.salary_max) {
                const min = filters.salary_min || '0';
                const max = filters.salary_max || '∞';
                tags.push({ key: 'salary', label: `薪资: ${min}-${max}K`, icon: 'bi-cash' });
            }
            if (filters.source) tags.push({ key: 'source', label: `来源: ${filters.source}`, icon: 'bi-tag' });
            if (filters.industry) tags.push({ key: 'industry', label: `行业: ${filters.industry}`, icon: 'bi-diagram-3' });
            if (filters.company_nature) tags.push({ key: 'company_nature', label: `性质: ${filters.company_nature}`, icon: 'bi-building' });
            if (filters.education) tags.push({ key: 'education', label: `学历: ${filters.education}`, icon: 'bi-mortarboard' });
            if (filters.date_from || filters.date_to) {
                tags.push({ key: 'date', label: `日期: ${filters.date_from || '...'} ~ ${filters.date_to || '...'}`, icon: 'bi-calendar' });
            }
            return tags;
        });

        function removeFilter(key) {
            if (key === 'keyword') { filters.keyword = ''; searchKeyword.value = ''; }
            else if (key === 'location') { selectedLocations.value = []; }
            else if (key === 'salary') { filters.salary_min = null; filters.salary_max = null; }
            else if (key === 'date') { filters.date_from = ''; filters.date_to = ''; }
            else { filters[key] = ''; }
            searchJobs();
        }

        // ---------- 骨架屏 ----------
        const showSkeleton = computed(() => loading.value && jobs.value.length > 0);

        // ---------- 爬虫状态 ----------
        const crawlStatus = reactive({ status: 'idle', progress: '', total_new: 0, error_message: '' });
        const crawlSource = ref('all');
        const jumpPage = ref(1);
        const sidebarCollapsed = ref(false);
        const filtersExpanded = ref(false);

        const crawlOptions = [
            { value: 'all', label: '全部数据源' },
            { value: 'shixiseng', label: '实习僧' },
            { value: 'ncss', label: '国家平台' },
            { value: 'websites', label: '大厂官网' },
            { value: 'api', label: 'API接口' }
        ];

        // ---------- 公司弹窗 ----------
        const showCompanyModal = ref(false);
        const companyList = ref([]);
        const companySearch = ref('');
        const companyIndustryFilter = ref('');

        // ---------- 定向抓取弹窗 ----------
        const showTargetedModal = ref(false);
        const targetedFilters = reactive({
            companies: [],
            industries: [],
            locations: []
        });
        const targetedIndustries = ref([]);
        const targetedCompanies = ref([]);
        const targetedCompanySearch = ref('');
        const targetedSource = ref('all');
        const targetedLocationPickerOpen = ref(false);
        const targetedExpandedProvinces = ref(new Set());

        // 定向抓取弹窗打开时加载数据
        watch(showTargetedModal, (val) => {
            if (val) {
                Promise.all([
                    fetch('/api/crawl/industries'),
                    fetch('/api/crawl/companies')
                ]).then(([indRes, compRes]) => {
                    if (indRes.ok) indRes.json().then(d => targetedIndustries.value = d);
                    if (compRes.ok) compRes.json().then(d => targetedCompanies.value = d);
                }).catch(e => console.error('加载定向抓取数据失败:', e));
            }
        });

        const filteredTargetedCompanies = computed(() => {
            if (!targetedCompanySearch.value.trim()) return targetedCompanies.value;
            const q = targetedCompanySearch.value.trim().toLowerCase();
            return targetedCompanies.value.filter(c => c.toLowerCase().includes(q));
        });

        const targetedIndustryCounts = computed(() => {
            const counts = {};
            targetedCompanies.value.forEach(() => {});
            return counts;
        });

        function openTargetedModal() {
            showTargetedModal.value = true;
            // 加载行业和公司列表
            Promise.all([
                fetch('/api/crawl/industries'),
                fetch('/api/crawl/companies')
            ]).then(([indRes, compRes]) => {
                if (indRes.ok) indRes.json().then(d => targetedIndustries.value = d);
                if (compRes.ok) compRes.json().then(d => targetedCompanies.value = d);
            }).catch(e => console.error('加载定向抓取数据失败:', e));
        }

        function toggleTargetedIndustry(ind) {
            const idx = targetedFilters.industries.indexOf(ind);
            if (idx === -1) targetedFilters.industries.push(ind);
            else targetedFilters.industries.splice(idx, 1);
        }

        function isTargetedIndustrySelected(ind) {
            return targetedFilters.industries.includes(ind);
        }

        function toggleTargetedCompany(name) {
            const idx = targetedFilters.companies.indexOf(name);
            if (idx === -1) targetedFilters.companies.push(name);
            else targetedFilters.companies.splice(idx, 1);
        }

        function isTargetedCompanySelected(name) {
            return targetedFilters.companies.includes(name);
        }

        function clearTargetedCompanies() {
            targetedFilters.companies = [];
        }

        function clearTargetedIndustries() {
            targetedFilters.industries = [];
        }

        function clearTargetedLocations() {
            targetedFilters.locations = [];
        }

        function toggleTargetedProvince(province) {
            const s = new Set(targetedExpandedProvinces.value);
            if (s.has(province)) s.delete(province);
            else s.add(province);
            targetedExpandedProvinces.value = s;
        }

        function isTargetedProvinceSelected(province, cities) {
            const selSet = new Set(targetedFilters.locations);
            if (cities.length === 0) return selSet.has(province);
            return cities.every(c => selSet.has(c));
        }

        function selectAllTargetedProvince(province, cities, provinceInDb) {
            const toAdd = [...cities];
            if (provinceInDb) toAdd.push(province);
            const selSet = new Set(targetedFilters.locations);
            const allSelected = toAdd.length > 0 && toAdd.every(loc => selSet.has(loc));
            if (allSelected) {
                toAdd.forEach(loc => selSet.delete(loc));
            } else {
                toAdd.forEach(loc => selSet.add(loc));
            }
            targetedFilters.locations = Array.from(selSet);
        }

        function toggleTargetedLocation(loc) {
            const selSet = new Set(targetedFilters.locations);
            if (selSet.has(loc)) selSet.delete(loc);
            else selSet.add(loc);
            targetedFilters.locations = Array.from(selSet);
        }

        function isTargetedLocationSelected(loc) {
            return targetedFilters.locations.includes(loc);
        }

        async function startTargetedCrawl() {
            if (targetedFilters.companies.length === 0 && targetedFilters.industries.length === 0 && targetedFilters.locations.length === 0) {
                showToast('请至少选择一个定向条件', 'warning');
                return;
            }
            try {
                const response = await fetch('/api/crawl', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        source: targetedSource.value,
                        filters: {
                            companies: targetedFilters.companies,
                            industries: targetedFilters.industries,
                            locations: targetedFilters.locations
                        }
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    lastTotalNew = 0;
                    startCrawlStatusPolling();
                    showTargetedModal.value = false;
                    showToast('定向抓取任务已启动', 'success');
                } else {
                    showToast(data.error || '启动定向抓取失败', 'error');
                }
            } catch (error) {
                console.error('启动定向抓取异常:', error);
                showToast('启动定向抓取失败: ' + error.message, 'error');
            }
        }

        // ---------- 设置弹窗 ----------
        const showSettingsModal = ref(false);
        const defaultConfig = {
            shixiseng: { max_pages: 100, max_count: -1, min_delay: 2, max_delay: 5, max_retries: 3, timeout: 60000 },
            ncss: { max_pages: 100, max_count: -1, min_delay: 2, max_delay: 5, max_retries: 3, timeout: 60000 },
            website: { max_count: -1, min_delay: 3, max_delay: 8, max_retries: 2, timeout: 60000 },
        };
        const crawlerConfig = ref(JSON.parse(JSON.stringify(defaultConfig)));

        let crawlPollTimer = null;
        let lastTotalNew = 0;

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

        const companyIndustries = computed(() => {
            const counts = {};
            companyList.value.forEach(c => { counts[c.industry] = (counts[c.industry] || 0) + 1; });
            return Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
        });

        const companyIndustryCounts = computed(() => {
            const counts = {};
            companyList.value.forEach(c => { counts[c.industry] = (counts[c.industry] || 0) + 1; });
            return counts;
        });

        const filteredCompanies = computed(() => {
            let list = companyList.value;
            if (companyIndustryFilter.value) {
                list = list.filter(c => c.industry === companyIndustryFilter.value);
            }
            if (companySearch.value.trim()) {
                const q = companySearch.value.trim().toLowerCase();
                list = list.filter(c => c.name.toLowerCase().includes(q) || c.url.toLowerCase().includes(q));
            }
            return list;
        });

        // ==================== API 方法 ====================

        async function fetchJobs() {
            loading.value = true;
            try {
                const params = new URLSearchParams();
                if (filters.keyword) params.append('keyword', filters.keyword);
                if (filters.company) params.append('company', filters.company);
                const locationParam = getLocationParam();
                if (locationParam) params.append('location', locationParam);
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
                } else {
                    showToast(data.error || '获取数据失败', 'error');
                }
            } catch (error) {
                console.error('获取岗位列表失败:', error);
                showToast('网络错误，请稍后重试', 'error');
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

        // ==================== 搜索与筛选 ====================

        function searchJobs() {
            showSuggestions.value = false;
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
            searchKeyword.value = '';
            selectedLocations.value = [];
            expandedProvinces.value = new Set();
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

        // ==================== 爬虫控制 ====================

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
                    showToast('爬虫任务已启动', 'success');
                } else {
                    showToast(data.error || '启动爬虫失败', 'error');
                }
            } catch (error) {
                console.error('启动爬虫异常:', error);
                showToast('启动爬虫失败: ' + error.message, 'error');
            }
        }

        async function stopCrawl() {
            try {
                const response = await fetch('/api/crawl/stop', { method: 'POST' });
                const data = await response.json();
                if (!response.ok) {
                    showToast(data.error || '停止失败', 'error');
                }
            } catch (error) {
                console.error('停止爬虫异常:', error);
            }
        }

        async function clearAllJobs() {
            if (!confirm('确定要清空所有岗位数据吗？此操作不可恢复！')) return;
            if (!confirm('再次确认：真的要删除全部数据吗？')) return;
            try {
                const response = await fetch('/api/jobs/clear', { method: 'POST' });
                const data = await response.json();
                if (response.ok) {
                    showToast(data.message, 'success');
                    fetchJobs();
                    fetchStats();
                    fetchCompanies();
                    fetchIndustries();
                    fetchLocations();
                } else {
                    showToast(data.error || '清空失败', 'error');
                }
            } catch (error) {
                console.error('清空数据异常:', error);
                showToast('清空失败: ' + error.message, 'error');
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
                        fetchLocations();
                    }

                    if (data.status === 'done' || data.status === 'error' || data.status === 'stopped') {
                        clearInterval(crawlPollTimer);
                        crawlPollTimer = null;
                        fetchJobs();
                        fetchStats();
                        fetchCompanies();
                        fetchIndustries();
                        fetchLocations();
                        if (data.status === 'done') showToast('抓取完成！', 'success');
                        if (data.status === 'error') showToast('抓取出错: ' + (data.error_message || ''), 'error');
                        if (data.status === 'stopped') showToast('抓取已停止', 'warning');
                    }
                } catch (error) {
                    console.error('轮询爬虫状态失败:', error);
                }
            }, 2000);
        }

        // ==================== 导出 ====================

        function exportExcel() {
            const params = new URLSearchParams();
            if (filters.keyword) params.append('keyword', filters.keyword);
            if (filters.company) params.append('company', filters.company);
            const locationParam = getLocationParam();
            if (locationParam) params.append('location', locationParam);
            if (filters.job_type && filters.job_type !== 'all') params.append('job_type', filters.job_type);
            if (filters.salary_min) params.append('salary_min', filters.salary_min);
            if (filters.salary_max) params.append('salary_max', filters.salary_max);
            if (filters.date_from) params.append('date_from', filters.date_from);
            if (filters.date_to) params.append('date_to', filters.date_to);
            if (filters.source) params.append('source', filters.source);
            if (filters.industry) params.append('industry', filters.industry);
            if (filters.company_nature) params.append('company_nature', filters.company_nature);
            if (filters.education) params.append('education', filters.education);
            window.open(`/api/export?${params.toString()}`, '_blank');
        }

        // ==================== 设置弹窗 ====================

        async function fetchConfig() {
            try {
                const res = await fetch('/api/config');
                if (res.ok) {
                    const data = await res.json();
                    const merged = JSON.parse(JSON.stringify(defaultConfig));
                    for (const source of Object.keys(merged)) {
                        if (data[source]) Object.assign(merged[source], data[source]);
                    }
                    crawlerConfig.value = merged;
                }
            } catch (e) {
                console.error('获取爬虫配置失败:', e);
            }
        }

        function openSettings() {
            fetchConfig();
            showSettingsModal.value = true;
        }

        async function saveConfig() {
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(crawlerConfig.value),
                });
                if (res.ok) {
                    showSettingsModal.value = false;
                    showToast('保存成功！下次启动爬虫时生效。', 'success');
                } else {
                    const data = await res.json();
                    showToast(data.error || '保存失败', 'error');
                }
            } catch (e) {
                showToast('保存失败: ' + e.message, 'error');
            }
        }

        function resetConfig() {
            crawlerConfig.value = JSON.parse(JSON.stringify(defaultConfig));
        }

        async function fetchCompanyList() {
            try {
                const res = await fetch('/api/companies/config');
                if (res.ok) {
                    const data = await res.json();
                    if (Array.isArray(data)) companyList.value = data;
                }
            } catch (e) {
                console.error('获取公司配置失败:', e);
            }
        }

        // ==================== 生命周期 ====================

        onMounted(() => {
            fetchJobs();
            fetchCompanies();
            fetchIndustries();
            fetchStats();
            fetchCompanyList();
            fetchLocations();

            fetch('/api/crawl/status')
                .then(res => res.json())
                .then(data => {
                    Object.assign(crawlStatus, data);
                    lastTotalNew = data.total_new || 0;
                    if (data.status === 'running') startCrawlStatusPolling();
                })
                .catch(err => console.error('检查爬虫状态失败:', err));
        });

        // ==================== 返回 ====================

        return {
            // 核心数据
            jobs, total, currentPage, perPage, loading,
            filters, companies, industries, stats,
            // Toast
            toasts, showToast,
            // 搜索建议
            searchKeyword, searchSuggestions, showSuggestions, isSearching, selectSuggestion,
            // 地区选择器
            selectedLocations, locationPickerOpen, expandedProvinces, dbLocations,
            locationTree, toggleProvince, isProvinceSelected, selectAllProvince,
            toggleLocation, isLocationSelected, clearLocations, getLocationParam,
            // 筛选标签
            activeFilterTags, removeFilter,
            // 骨架屏
            showSkeleton,
            // 爬虫
            crawlStatus, crawlSource, crawlOptions,
            // 弹窗
            showCompanyModal, companyList, companySearch, companyIndustryFilter,
            companyIndustries, companyIndustryCounts, filteredCompanies,
            showSettingsModal, crawlerConfig,
            // 定向抓取
            showTargetedModal, targetedFilters, targetedIndustries, targetedCompanies,
            targetedCompanySearch, targetedSource, filteredTargetedCompanies,
            targetedLocationPickerOpen, targetedExpandedProvinces,
            openTargetedModal, toggleTargetedIndustry, isTargetedIndustrySelected,
            toggleTargetedCompany, isTargetedCompanySelected,
            clearTargetedCompanies, clearTargetedIndustries, clearTargetedLocations,
            toggleTargetedProvince, isTargetedProvinceSelected, selectAllTargetedProvince,
            toggleTargetedLocation, isTargetedLocationSelected, startTargetedCrawl,
            // 侧边栏
            jumpPage, sidebarCollapsed, filtersExpanded,
            // 分页
            totalPages, displayPages,
            // 方法
            fetchJobs, fetchIndustries, searchJobs, resetFilters, goToPage,
            startCrawl, stopCrawl, clearAllJobs, exportExcel,
            openSettings, saveConfig, resetConfig
        };
    }
});

app.mount('#app');
