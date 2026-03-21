import { ref } from 'vue'
import { api } from '../api'
import { useDataStore } from '../stores/data'
import { useTablesStore } from '../stores/tables'

export function useExport() {
  const exporting = ref(false)

  async function exportData(exportAll = false) {
    const tablesStore = useTablesStore()
    const dataStore = useDataStore()
    const tableName = tablesStore.currentTable
    if (!tableName) return

    exporting.value = true
    try {
      const params = new URLSearchParams({ sort_dir: dataStore.sortDir })
      if (dataStore.sortCol) params.set('sort_col', dataStore.sortCol)
      if (!exportAll) {
        if (dataStore.filters.length > 0) params.set('filters', JSON.stringify(dataStore.filters))
        if (dataStore.search) params.set('search', dataStore.search)
      }
      if (exportAll) params.set('export_all', 'true')

      const res = await api(`/api/table/${tableName}/export?${params}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${tableName}_export.csv`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      exporting.value = false
    }
  }

  return { exportData, exporting }
}
