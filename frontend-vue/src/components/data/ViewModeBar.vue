<template>
  <div v-if="tablesStore.currentTable" class="view-mode-bar">
    <ElSegmented
      v-model="mode"
      :options="options"
      size="default"
      @change="onChange"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElSegmented } from 'element-plus'
import { useDataStore } from '../../stores/data'
import { useTablesStore } from '../../stores/tables'

const dataStore = useDataStore()
const tablesStore = useTablesStore()

const options = [
  { label: '📋 数据', value: 'data' },
  { label: '📊 分组统计', value: 'group' },
]

const mode = computed({
  get: () => (dataStore.viewMode === 'group' ? 'group' : 'data'),
  set: () => {},
})

function onChange(val) {
  dataStore.setViewMode(val, tablesStore.currentTable)
}
</script>

<style scoped lang="scss">
.view-mode-bar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 8px 20px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.el-segmented) {
  --el-segmented-bg-color: var(--surface-2);
  --el-segmented-color: var(--text-sub);
  --el-segmented-hover-color: var(--text);
  --el-segmented-item-selected-color: #000;
  --el-segmented-item-selected-bg-color: var(--accent);
  --el-border-radius-base: 999px;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px;
}

:deep(.el-segmented__item) {
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 600;
  border-radius: 999px;
  padding: 0 14px;
  transition: all 0.15s;
}
</style>
