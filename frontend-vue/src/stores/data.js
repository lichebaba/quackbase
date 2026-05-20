import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiJson } from '../api'

export const useDataStore = defineStore('data', () => {
  const columns = ref([])
  const rows = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(50)
  const totalPages = ref(1)
  const sortCol = ref(null)
  const sortDir = ref('asc')
  const filters = ref([])
  const search = ref('')
  // 'data' | 'group' — 控制 Dashboard 主区显示原始数据表还是分组统计视图
  const viewMode = ref('data')
  // 翻页 / 改 page size 时跳过 COUNT 全表扫描；只有筛选 / 搜索 / 排序变化时才重算
  let lastCountKey = null
  function currentCountKey() {
    return JSON.stringify({
      f: filters.value,
      s: search.value,
      sc: sortCol.value,
      sd: sortDir.value,
    })
  }
  function markCountDirty() { lastCountKey = null }

  function reset() {
    page.value = 1
    sortCol.value = null
    sortDir.value = 'asc'
    filters.value = []
    search.value = ''
    viewMode.value = 'data'
    total.value = 0
    totalPages.value = 1
    lastCountKey = null
  }

  function setViewMode(mode, tableName) {
    const wasGroup = viewMode.value === 'group'
    viewMode.value = mode === 'group' ? 'group' : 'data'
    // 从分组视图切回数据视图时，分组期间筛选 / 搜索可能已变更但数据视图没有跟着刷新，
    // 这里补一次 loadData，确保表格内容与筛选条件保持一致
    if (wasGroup && viewMode.value === 'data' && tableName) {
      loadData(tableName).catch(() => {})
    }
  }

  async function loadData(tableName) {
    if (!tableName) return
    const params = new URLSearchParams({
      page: page.value,
      page_size: pageSize.value,
      sort_dir: sortDir.value,
    })
    if (sortCol.value) params.set('sort_col', sortCol.value)
    if (filters.value.length > 0) params.set('filters', JSON.stringify(filters.value))
    if (search.value) params.set('search', search.value)

    // 关键性能优化：筛选/搜索/排序没变时（即只是翻页 / 调页大小），跳过 COUNT(*) 全表扫描
    const ck = currentCountKey()
    const skipCount = lastCountKey === ck && lastCountKey !== null
    if (skipCount) params.set('skip_count', 'true')

    const data = await apiJson(`/api/table/${tableName}/data?${params}`)
    if (!data) return
    columns.value = data.columns
    rows.value = data.rows
    if (data.total !== null && data.total !== undefined) {
      total.value = data.total
      totalPages.value = data.total_pages
    }
    page.value = data.page
    lastCountKey = ck
  }

  function toggleSort(col) {
    if (sortCol.value === col) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortCol.value = col
      sortDir.value = 'asc'
    }
    page.value = 1
  }

  function addFilter(filter) {
    filters.value.push(filter)
    page.value = 1
  }

  function updateFilter(idx, filter) {
    if (idx < 0 || idx >= filters.value.length) return
    filters.value.splice(idx, 1, filter)
    page.value = 1
  }

  function removeFilter(idx) {
    filters.value.splice(idx, 1)
    page.value = 1
  }

  function clearFilters() {
    filters.value = []
    page.value = 1
  }

  function setSearch(val) {
    search.value = val
    page.value = 1
  }

  function goToPage(p) {
    page.value = Math.max(1, Math.min(p, totalPages.value))
  }

  function setPageSize(size) {
    pageSize.value = size
    page.value = 1
  }

  async function deleteRows(tableName) {
    if (!tableName) return null
    const params = new URLSearchParams()
    if (filters.value.length > 0) params.set('filters', JSON.stringify(filters.value))
    if (search.value) params.set('search', search.value)
    const qs = params.toString()
    const url = `/api/table/${tableName}/data` + (qs ? `?${qs}` : '')
    return await apiJson(url, { method: 'DELETE' })
  }

  return {
    columns, rows, total, page, pageSize, totalPages,
    sortCol, sortDir, filters, search, viewMode,
    reset, loadData, toggleSort,
    addFilter, updateFilter, removeFilter, clearFilters,
    setSearch, goToPage, setPageSize, deleteRows, setViewMode,
  }
})
