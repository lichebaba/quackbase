import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiJson, api } from '../api'

export const useTablesStore = defineStore('tables', () => {
  const tables = ref([])
  const currentTable = ref(null)

  async function loadTables() {
    const data = await apiJson('/api/tables')
    tables.value = data?.tables || []
  }

  function selectTable(name) {
    currentTable.value = name
  }

  async function deleteTable(name) {
    await api(`/api/table/${name}`, { method: 'DELETE' })
    if (currentTable.value === name) currentTable.value = null
    await loadTables()
  }

  return { tables, currentTable, loadTables, selectTable, deleteTable }
})
