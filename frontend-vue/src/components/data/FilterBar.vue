<template>
  <div v-if="dataStore.filters.length > 0" class="filter-bar">
    <div class="filter-bar-inner">
      <div class="filter-label">筛选</div>
      <div class="filter-chips">
        <div v-for="(f, i) in dataStore.filters" :key="i" class="filter-chip">
          <span class="filter-chip-label" @click="editFilter(i)" title="点击编辑">{{ f.op === 'IS NULL' || f.op === 'IS NOT NULL' ? `${f.col} ${f.op}` : `${f.col} ${f.op} "${f.val}"` }}</span>
          <button class="filter-chip-remove" @click.stop="removeAndReload(i)" title="删除此条件">✕</button>
        </div>
      </div>
      <button class="btn-add-filter" @click="openModal">+ 添加条件</button>
    </div>
  </div>
  <div v-else-if="tablesStore.currentTable" class="filter-bar filter-bar-minimal">
    <div class="filter-bar-inner">
      <button class="btn-add-filter" @click="openModal">+ 添加筛选条件</button>
    </div>
  </div>
</template>

<script setup>
import { useDataStore } from '../../stores/data'
import { useTablesStore } from '../../stores/tables'
import { useToastStore } from '../../stores/toast'

const dataStore = useDataStore()
const tablesStore = useTablesStore()
const toast = useToastStore()

function removeAndReload(idx) {
  dataStore.removeFilter(idx)
  if (dataStore.viewMode !== 'group') {
    dataStore.loadData(tablesStore.currentTable).catch(e => toast.add(e.message || '加载数据失败', 'error'))
  }
}

function openModal() {
  window.dispatchEvent(new CustomEvent('open-filter-modal'))
}

function editFilter(idx) {
  window.dispatchEvent(new CustomEvent('open-filter-modal', { detail: { editIdx: idx } }))
}
</script>

<style scoped lang="scss">
.filter-bar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 10px 20px;
  flex-shrink: 0;

  &-minimal { padding: 8px 20px; }

  &-inner {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
}

.filter-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  white-space: nowrap;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--accent-dim);
  border: 1px solid rgba(245,200,66,0.25);
  color: var(--accent);
  font-size: 12px;
  font-family: var(--font-mono);
  padding: 3px 4px 3px 10px;
  border-radius: 20px;

  &-label {
    cursor: pointer;
    user-select: none;
    transition: opacity 0.15s;
    padding: 1px 4px 1px 0;

    &:hover {
      opacity: 0.8;
      text-decoration: underline;
      text-decoration-style: dashed;
      text-underline-offset: 3px;
    }
  }

  &-remove {
    background: none;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font-size: 12px;
    line-height: 1;
    padding: 2px 6px;
    border-radius: 50%;
    opacity: 0.7;
    transition: all 0.15s;

    &:hover {
      opacity: 1;
      background: rgba(245,200,66,0.15);
    }
  }
}

.btn-add-filter {
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 600;
  background: none;
  border: 1px dashed var(--border-light);
  color: var(--text-sub);
  padding: 4px 12px;
  border-radius: 20px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;

  &:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
}
</style>
