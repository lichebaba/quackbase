<template>
  <div class="pagination">
    <button class="pg-btn" :disabled="dataStore.page <= 1" @click="go(1)">«</button>
    <button class="pg-btn" :disabled="dataStore.page <= 1" @click="go(dataStore.page - 1)">‹</button>
    <div class="pg-info">
      第 {{ start }}–{{ end }} 行 /
      <template v-if="isFiltered">筛选 {{ dataStore.total.toLocaleString() }} 行 · </template>
      共 {{ realTotal.toLocaleString() }} 行
      ({{ dataStore.page }}/{{ dataStore.totalPages }} 页)
    </div>
    <button class="pg-btn" :disabled="dataStore.page >= dataStore.totalPages" @click="go(dataStore.page + 1)">›</button>
    <button class="pg-btn" :disabled="dataStore.page >= dataStore.totalPages" @click="go(dataStore.totalPages)">»</button>
    <select class="pg-size" :value="dataStore.pageSize" @change="onSizeChange">
      <option :value="25">25 行</option>
      <option :value="50">50 行</option>
      <option :value="100">100 行</option>
      <option :value="200">200 行</option>
    </select>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDataStore } from '../../stores/data'
import { useTablesStore } from '../../stores/tables'

const dataStore = useDataStore()
const tablesStore = useTablesStore()

const start = computed(() => Math.min((dataStore.page - 1) * dataStore.pageSize + 1, dataStore.total))
const end = computed(() => Math.min(dataStore.page * dataStore.pageSize, dataStore.total))

const realTotal = computed(() => {
  const t = tablesStore.tables.find(t => t.name === tablesStore.currentTable)
  return t ? t.row_count : dataStore.total
})
const isFiltered = computed(() => dataStore.filters.length > 0 || dataStore.search)

function go(p) {
  dataStore.goToPage(p)
  dataStore.loadData(tablesStore.currentTable)
}

function onSizeChange(e) {
  dataStore.setPageSize(Number(e.target.value))
  dataStore.loadData(tablesStore.currentTable)
}
</script>

<style scoped>
.pagination {
  display: flex; align-items: center; gap: 6px; padding: 10px 16px;
  border-top: 1px solid var(--border); background: var(--surface); flex-shrink: 0;
}
.pg-btn {
  width: 32px; height: 32px; background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text-sub); border-radius: 6px; cursor: pointer; font-size: 14px;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.pg-btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.pg-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.pg-info { font-size: 12px; font-family: var(--font-mono); color: var(--text-sub); padding: 0 8px; flex: 1; text-align: center; }
.pg-size {
  font-family: var(--font-mono); font-size: 12px; background: var(--surface-2);
  border: 1px solid var(--border); color: var(--text-sub); padding: 4px 8px;
  border-radius: 6px; cursor: pointer;
}
.pg-size:focus { outline: none; border-color: var(--accent); }
</style>
