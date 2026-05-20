import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiJson } from '../api'
import { useDataStore } from './data'

/**
 * 分组统计 store。
 * 复用 data store 的 filters / search，使分组结果与列表展示口径一致。
 */
export const useGroupStatsStore = defineStore('groupStats', () => {
  const groupBy = ref('')
  // 每个聚合项：{ op: 'COUNT'|'SUM'|'AVG'|'MIN'|'MAX', col: string, alias: string }
  const aggs = ref([{ op: 'COUNT', col: '*', alias: 'count' }])

  const columns = ref([])
  const rows = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(50)
  const totalPages = ref(1)
  const sortCol = ref(null)
  const sortDir = ref('desc')

  const loading = ref(false)
  const lastError = ref('')
  const hasResult = computed(() => columns.value.length > 0)
  // 翻页 / 改 page size 时跳过 COUNT 全表扫描；只有配置 / filters / search 变化时才重算
  let lastCountKey = null
  function _currentCountKey(tableName) {
    const dataStore = useDataStore()
    return JSON.stringify({
      t: tableName,
      gb: groupBy.value,
      a: aggs.value.map(a => ({ op: a.op, col: a.col, alias: a.alias })),
      f: dataStore.filters,
      s: dataStore.search,
    })
  }

  function reset() {
    groupBy.value = ''
    aggs.value = [{ op: 'COUNT', col: '*', alias: 'count' }]
    columns.value = []
    rows.value = []
    total.value = 0
    page.value = 1
    totalPages.value = 1
    sortCol.value = null
    sortDir.value = 'desc'
    lastError.value = ''
    lastCountKey = null
  }

  function addAgg() {
    aggs.value.push({ op: 'COUNT', col: '*', alias: '' })
  }

  function removeAgg(idx) {
    aggs.value.splice(idx, 1)
    if (aggs.value.length === 0) addAgg()
  }

  function setSort(col) {
    if (sortCol.value === col) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortCol.value = col
      sortDir.value = 'desc'
    }
    page.value = 1
  }

  function goToPage(p) {
    page.value = Math.max(1, Math.min(p, totalPages.value))
  }

  function setPageSize(size) {
    pageSize.value = size
    page.value = 1
  }

  async function loadStats(tableName) {
    if (!tableName) return
    if (!groupBy.value) {
      lastError.value = '请先选择分组字段'
      return
    }
    const dataStore = useDataStore()

    const validAggs = aggs.value
      .filter(a => a.op)
      .map(a => ({
        op: a.op,
        col: a.col || (a.op === 'COUNT' ? '*' : ''),
        alias: a.alias || undefined,
      }))
    if (validAggs.length === 0) {
      lastError.value = '至少要配置一个聚合项'
      return
    }
    // 非 COUNT 必须有列
    const invalid = validAggs.find(a => a.op !== 'COUNT' && (!a.col || a.col === '*'))
    if (invalid) {
      lastError.value = `${invalid.op} 必须选择目标列`
      return
    }

    const params = new URLSearchParams({
      group_by: groupBy.value,
      aggs: JSON.stringify(validAggs),
      page: page.value,
      page_size: pageSize.value,
      sort_dir: sortDir.value,
    })
    if (sortCol.value) params.set('sort_col', sortCol.value)
    if (dataStore.filters.length > 0) params.set('filters', JSON.stringify(dataStore.filters))
    if (dataStore.search) params.set('search', dataStore.search)

    // 翻页 / 改 page size / 改排序 时筛选 + 聚合配置都没变，跳过 distinct group count 扫描
    const ck = _currentCountKey(tableName)
    const skipCount = lastCountKey === ck && lastCountKey !== null
    if (skipCount) params.set('skip_count', 'true')

    loading.value = true
    lastError.value = ''
    try {
      const data = await apiJson(`/api/table/${tableName}/group-stats?${params}`)
      if (!data) return
      columns.value = data.columns
      rows.value = data.rows
      if (data.total !== null && data.total !== undefined) {
        total.value = data.total
        totalPages.value = data.total_pages
      }
      page.value = data.page
      lastCountKey = ck
    } catch (e) {
      lastError.value = e.message || '加载分组统计失败'
      columns.value = []
      rows.value = []
      total.value = 0
      lastCountKey = null
    } finally {
      loading.value = false
    }
  }

  return {
    groupBy, aggs,
    columns, rows, total, page, pageSize, totalPages, sortCol, sortDir,
    loading, lastError, hasResult,
    reset, addAgg, removeAgg, setSort, goToPage, setPageSize, loadStats,
  }
})
