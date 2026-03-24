<template>
  <header class="topbar">
    <div class="topbar-left">
      <button class="sidebar-toggle" @click="toggleSidebar">☰</button>
      <div class="breadcrumb">
        <span>{{ tablesStore.currentTable || '— 请选择数据表 —' }}</span>
      </div>
    </div>
    <div class="topbar-right">
      <span v-if="tablesStore.currentTable && isFiltered" class="row-count">筛选 {{ dataStore.total.toLocaleString() }} / 共 {{ realTotal.toLocaleString() }} 行</span>
      <span v-else-if="tablesStore.currentTable" class="row-count">{{ realTotal.toLocaleString() }} 行</span>
      <button v-if="dataStore.filters.length > 0" class="btn btn-ghost" @click="doClearFilters">✕ 清除筛选</button>

      <!-- Delete button -->
      <button v-if="tablesStore.currentTable && authStore.canDelete"
              class="btn btn-danger" :disabled="deleting"
              @click="doDelete">
        <template v-if="deleting"><span class="spinner spinner-light"></span> 删除中...</template>
        <template v-else>{{ isFiltered ? '✕ 删除筛选数据' : '✕ 清空表数据' }}</template>
      </button>

      <!-- Export dropdown -->
      <div v-if="tablesStore.currentTable" class="export-dropdown" ref="dropdownRef">
        <button class="btn btn-primary" :disabled="exporting" @click="!exporting && (exportOpen = !exportOpen)">
          <template v-if="exporting"><span class="spinner"></span> 导出中...</template>
          <template v-else>↓ 导出 CSV</template>
        </button>
        <div v-if="exportOpen && !exporting" class="export-menu">
          <button class="export-option" @click="doExport(false)">导出筛选数据</button>
          <button class="export-option" @click="doExport(true)">导出全部数据</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, inject, computed, onMounted, onUnmounted } from 'vue'
import { useTablesStore } from '../../stores/tables'
import { useDataStore } from '../../stores/data'
import { useAuthStore } from '../../stores/auth'
import { useToastStore } from '../../stores/toast'
import { useExport } from '../../composables/useExport'

const tablesStore = useTablesStore()
const dataStore = useDataStore()
const authStore = useAuthStore()
const toast = useToastStore()
const { exportData, exporting } = useExport()

const sidebarCollapsed = inject('sidebarCollapsed')
const exportOpen = ref(false)
const dropdownRef = ref(null)
const deleting = ref(false)

const realTotal = computed(() => {
  const t = tablesStore.tables.find(t => t.name === tablesStore.currentTable)
  return t ? t.row_count : 0
})
const isFiltered = computed(() => dataStore.filters.length > 0 || dataStore.search)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

function doClearFilters() {
  dataStore.clearFilters()
  dataStore.loadData(tablesStore.currentTable)
}

async function doDelete() {
  const msg = isFiltered.value
    ? `确认删除筛选出的 ${dataStore.total} 条数据？此操作不可撤销。`
    : `确认清空表 "${tablesStore.currentTable}" 的全部数据？此操作不可撤销。`
  if (!confirm(msg)) return
  deleting.value = true
  try {
    const res = await dataStore.deleteRows(tablesStore.currentTable)
    toast.add(`已删除 ${res.deleted_count} 条数据`, 'success')
    await tablesStore.loadTables()
    await dataStore.loadData(tablesStore.currentTable)
  } catch (e) {
    toast.add(e.message, 'error')
  } finally {
    deleting.value = false
  }
}

async function doExport(all) {
  exportOpen.value = false
  try {
    await exportData(all)
    toast.add('CSV 导出成功', 'success')
  } catch (e) {
    toast.add(e.message, 'error')
  }
}

function onClickOutside(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    exportOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.topbar {
  height: var(--topbar-h); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; background: var(--surface); flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.sidebar-toggle {
  background: none; border: 1px solid var(--border); color: var(--text-sub);
  width: 32px; height: 32px; border-radius: 6px; cursor: pointer;
  font-size: 14px; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.sidebar-toggle:hover { border-color: var(--accent); color: var(--accent); }
.breadcrumb { font-size: 15px; font-weight: 700; color: var(--text-sub); letter-spacing: 0.01em; }
.breadcrumb span { color: var(--text); }
.topbar-right { display: flex; align-items: center; gap: 10px; }
.row-count {
  font-size: 12px; font-family: var(--font-mono); color: var(--text-muted);
  background: var(--surface-2); padding: 3px 10px; border-radius: 20px;
  border: 1px solid var(--border);
}
.export-dropdown { position: relative; }
.export-menu {
  position: absolute; right: 0; top: 100%; margin-top: 4px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow);
  min-width: 160px; z-index: 50; overflow: hidden;
}
.export-option {
  display: block; width: 100%; padding: 10px 16px;
  background: none; border: none; color: var(--text);
  font-family: var(--font-ui); font-size: 13px; text-align: left;
  cursor: pointer; transition: background 0.15s;
}
.export-option:hover { background: var(--surface-3); }
.export-option + .export-option { border-top: 1px solid var(--border); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-danger {
  background: var(--danger); color: #fff; border: none;
  padding: 6px 14px; border-radius: var(--radius); font-family: var(--font-ui);
  font-size: 13px; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
}
.btn-danger:hover:not(:disabled) { opacity: 0.85; }
.spinner-light { border-color: rgba(255,255,255,0.3); border-top-color: #fff; }
.spinner {
  display: inline-block; width: 12px; height: 12px;
  border: 2px solid rgba(0,0,0,0.2); border-top-color: #000;
  border-radius: 50%; animation: spin 0.6s linear infinite;
  vertical-align: middle; margin-right: 4px;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
