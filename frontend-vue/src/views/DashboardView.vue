<template>
  <div class="dashboard">
    <AppSidebar />
    <main class="main">
      <AppTopbar />
      <FilterBar />
      <SearchBar />

      <!-- Welcome screen -->
      <div v-if="!tablesStore.currentTable" class="welcome">
        <div class="welcome-art">
          <svg viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="20" y="40" width="160" height="100" rx="8" fill="var(--surface-2)" stroke="var(--border)" stroke-width="1.5"/>
            <rect x="20" y="40" width="160" height="28" rx="8" fill="var(--accent)" opacity="0.15"/>
            <rect x="20" y="54" width="160" height="14" fill="var(--accent)" opacity="0.15"/>
            <line x1="20" y1="68" x2="180" y2="68" stroke="var(--border)" stroke-width="1"/>
            <line x1="20" y1="86" x2="180" y2="86" stroke="var(--border)" stroke-width="1"/>
            <line x1="20" y1="104" x2="180" y2="104" stroke="var(--border)" stroke-width="1"/>
            <line x1="70" y1="40" x2="70" y2="140" stroke="var(--border)" stroke-width="1"/>
            <line x1="120" y1="40" x2="120" y2="140" stroke="var(--border)" stroke-width="1"/>
            <rect x="30" y="74" width="28" height="6" rx="3" fill="var(--text-muted)" opacity="0.4"/>
            <rect x="30" y="92" width="22" height="6" rx="3" fill="var(--text-muted)" opacity="0.4"/>
            <rect x="80" y="74" width="24" height="6" rx="3" fill="var(--accent)" opacity="0.5"/>
            <rect x="80" y="92" width="30" height="6" rx="3" fill="var(--accent)" opacity="0.5"/>
            <text x="100" y="25" text-anchor="middle" font-size="28" fill="var(--accent)">🦆</text>
          </svg>
        </div>
        <h2 class="welcome-title">Quackbase</h2>
        <p class="welcome-desc">上传 CSV/XLSX 文件，即可在浏览器中进行数据预览、筛选、排序和导出。</p>
        <div class="welcome-steps">
          <div class="step"><span class="step-num">01</span><span>左侧上传文件</span></div>
          <div class="step"><span class="step-num">02</span><span>从表列表选择数据表</span></div>
          <div class="step"><span class="step-num">03</span><span>搜索 · 筛选 · 排序 · 导出</span></div>
        </div>
      </div>

      <!-- Data table area -->
      <div v-else class="table-area">
        <DataTable />
        <PaginationBar />
      </div>
    </main>

    <!-- Modals -->
    <FilterModal />
    <UploadModeDialog />
    <UserManagement />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useTablesStore } from '../stores/tables'

import AppSidebar from '../components/layout/AppSidebar.vue'
import AppTopbar from '../components/layout/AppTopbar.vue'
import FilterBar from '../components/data/FilterBar.vue'
import SearchBar from '../components/data/SearchBar.vue'
import DataTable from '../components/data/DataTable.vue'
import PaginationBar from '../components/data/PaginationBar.vue'
import FilterModal from '../components/data/FilterModal.vue'
import UploadModeDialog from '../components/upload/UploadModeDialog.vue'
import UserManagement from '../components/admin/UserManagement.vue'

const tablesStore = useTablesStore()

onMounted(() => {
  tablesStore.loadTables()
})
</script>

<style scoped>
.dashboard { display: flex; height: 100vh; overflow: hidden; }
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }

.welcome {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 40px; gap: 20px;
}
.welcome-art svg { width: 200px; height: 160px; opacity: 0.7; }
.welcome-title { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; text-align: center; }
.welcome-desc { font-size: 14px; color: var(--text-sub); text-align: center; max-width: 380px; line-height: 1.7; }
.welcome-steps { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin-top: 8px; }
.step {
  display: flex; align-items: center; gap: 8px;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 10px 16px; font-size: 13px; color: var(--text-sub);
}
.step-num { font-family: var(--font-mono); font-size: 11px; color: var(--accent); font-weight: 500; }

.table-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
</style>
