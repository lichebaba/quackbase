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

  function reset() {
    page.value = 1
    sortCol.value = null
    sortDir.value = 'asc'
    filters.value = []
    search.value = ''
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

    const data = await apiJson(`/api/table/${tableName}/data?${params}`)
    if (!data) return
    columns.value = data.columns
    rows.value = data.rows
    total.value = data.total
    totalPages.value = data.total_pages
    page.value = data.page
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
    sortCol, sortDir, filters, search,
    reset, loadData, toggleSort,
    addFilter, removeFilter, clearFilters,
    setSearch, goToPage, setPageSize, deleteRows,
  }
})
