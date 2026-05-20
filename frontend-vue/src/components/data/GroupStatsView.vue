<template>
  <div class="group-stats">
    <!-- 统计配置 card -->
    <section class="qb-card config-card">
      <header class="qb-card-header">
        <span class="qb-card-title">📊 统计配置</span>
        <div class="config-card-actions">
          <span v-if="usingFilters" class="hint">已应用 {{ filterDesc }}</span>
          <span v-else class="hint">未应用任何筛选 / 搜索</span>
          <button class="btn btn-ghost" :disabled="!groupStore.hasResult" @click="exportStats">↓ 导出 CSV</button>
          <button class="btn btn-primary" :disabled="!canRun || groupStore.loading" @click="run">
            <template v-if="groupStore.loading">统计中...</template>
            <template v-else>应用统计</template>
          </button>
        </div>
      </header>
      <div class="qb-card-body config-panel">
        <div class="config-row">
          <label class="config-label">分组字段</label>
          <select :value="groupBy0" class="form-select compact" :disabled="dataStore.columns.length === 0" @change="onGroupChange(0, $event.target.value)">
            <option value="" disabled>— 选择主分组列 —</option>
            <option v-for="c in dataStore.columns" :key="c.name" :value="c.name">{{ c.name }} ({{ formatType(c.type) }})</option>
          </select>
          <select :value="groupBy1" class="form-select compact" :disabled="!groupBy0 || dataStore.columns.length === 0" @change="onGroupChange(1, $event.target.value)">
            <option value="">— 次级分组（可选）—</option>
            <option v-for="c in secondaryColOptions" :key="c.name" :value="c.name">{{ c.name }} ({{ formatType(c.type) }})</option>
          </select>
        </div>

        <div class="aggs-block">
          <label class="config-label">聚合项</label>
          <div class="agg-list">
            <div v-for="(agg, idx) in groupStore.aggs" :key="idx" class="agg-row">
              <select v-model="agg.op" class="form-select compact agg-op">
                <option value="COUNT">COUNT 计数</option>
                <option value="SUM">SUM 求和</option>
                <option value="AVG">AVG 平均值</option>
                <option value="MIN">MIN 最小值</option>
                <option value="MAX">MAX 最大值</option>
              </select>
              <select v-model="agg.col" class="form-select compact agg-col">
                <option v-if="agg.op === 'COUNT'" value="*">* (所有行)</option>
                <option v-for="c in colOptions(agg.op)" :key="c.name" :value="c.name">{{ c.name }}</option>
              </select>
              <input v-model="agg.alias" type="text" class="form-input compact agg-alias" :placeholder="defaultAlias(agg)" />
              <button class="icon-btn" :disabled="groupStore.aggs.length === 1" title="删除此聚合项" @click="groupStore.removeAgg(idx)">✕</button>
            </div>
          </div>
          <button class="btn-add-agg" @click="groupStore.addAgg">+ 添加聚合项</button>
        </div>

        <div v-if="groupStore.lastError" class="error-banner">{{ groupStore.lastError }}</div>
      </div>
    </section>

    <!-- 统计结果 card -->
    <section class="qb-card result-card">
      <header class="qb-card-header">
        <span class="qb-card-title">📈 统计结果</span>
        <span v-if="groupStore.hasResult" class="result-meta">共 {{ groupStore.total.toLocaleString() }} 个分组</span>
      </header>
      <div class="result-area">
        <div v-if="!groupStore.hasResult && !groupStore.loading" class="empty-tip">
          选择分组字段与聚合项后，点击「应用统计」生成结果。
        </div>
        <div v-else-if="groupStore.loading" class="empty-tip">统计中...</div>
        <div v-else class="result-scroll">
          <table class="data-table" :style="{ width: tableWidth }">
            <colgroup>
              <col style="width:44px" />
              <col v-for="c in groupStore.columns" :key="c.name" :style="{ width: colWidth(c.name) }" />
            </colgroup>
            <thead>
              <tr>
                <th><div class="th-inner">#</div></th>
                <th v-for="c in groupStore.columns" :key="c.name" :class="{ sorted: groupStore.sortCol === c.name }">
                  <div class="th-inner" @click="onSort(c.name)">
                    <span class="th-name">{{ c.name }}</span>
                    <span class="th-type">{{ formatType(c.type) }}</span>
                    <span class="sort-icon">{{ groupStore.sortCol === c.name ? (groupStore.sortDir === 'asc' ? '↑' : '↓') : '↕' }}</span>
                  </div>
                  <div class="col-resizer"
                       :class="{ active: resizingCol === c.name }"
                       @mousedown.stop.prevent="startResize($event, c.name)"
                       @dblclick.stop.prevent="resetColWidth(c.name)"
                       title="拖动调整列宽，双击重置"></div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="groupStore.rows.length === 0">
                <td :colspan="groupStore.columns.length + 1" class="empty-cell">暂无分组数据</td>
              </tr>
              <tr v-for="(row, i) in groupStore.rows" :key="i">
                <td class="row-num">{{ (groupStore.page - 1) * groupStore.pageSize + i + 1 }}</td>
                <td v-for="c in groupStore.columns" :key="c.name"
                    :class="{ 'null-val': row[c.name] === null || row[c.name] === undefined, 'num-val': isNumericType(c.type) && row[c.name] !== null }"
                    :title="String(row[c.name] ?? '')">
                  {{ formatCell(row[c.name], c.type) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="groupStore.hasResult" class="pagination">
        <button class="pg-btn" :disabled="groupStore.page <= 1" @click="goPage(1)">«</button>
        <button class="pg-btn" :disabled="groupStore.page <= 1" @click="goPage(groupStore.page - 1)">‹</button>
        <div class="pg-info">
          共 {{ groupStore.total.toLocaleString() }} 个分组 ({{ groupStore.page }}/{{ groupStore.totalPages }} 页)
        </div>
        <button class="pg-btn" :disabled="groupStore.page >= groupStore.totalPages" @click="goPage(groupStore.page + 1)">›</button>
        <button class="pg-btn" :disabled="groupStore.page >= groupStore.totalPages" @click="goPage(groupStore.totalPages)">»</button>
        <select class="pg-size" :value="groupStore.pageSize" @change="onSizeChange">
          <option :value="25">25 行</option>
          <option :value="50">50 行</option>
          <option :value="100">100 行</option>
          <option :value="200">200 行</option>
        </select>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, reactive, watch } from 'vue'
import { useDataStore } from '../../stores/data'
import { useTablesStore } from '../../stores/tables'
import { useGroupStatsStore } from '../../stores/groupStats'
import { useToastStore } from '../../stores/toast'

const dataStore = useDataStore()
const tablesStore = useTablesStore()
const groupStore = useGroupStatsStore()
const toast = useToastStore()

const NUMERIC_RE = /INT|FLOAT|DOUBLE|DECIMAL|NUMERIC|REAL/

// ----- 列宽（可拖拽）-----
const DEFAULT_WIDTH = 180
const MIN_WIDTH = 60
const MAX_WIDTH = 800
// 按列名记宽度，切换聚合时同名列宽度保留
const colWidths = reactive({})
const resizingCol = ref(null)

function colWidth(name) {
  return (colWidths[name] || DEFAULT_WIDTH) + 'px'
}
const tableWidth = computed(() => {
  const sum = groupStore.columns.reduce((acc, c) => acc + (colWidths[c.name] || DEFAULT_WIDTH), 0)
  return (44 + sum) + 'px'
})
function startResize(e, name) {
  const startX = e.clientX
  const startW = colWidths[name] || DEFAULT_WIDTH
  resizingCol.value = name
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  function onMove(ev) {
    const next = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startW + (ev.clientX - startX)))
    colWidths[name] = next
  }
  function onUp() {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    resizingCol.value = null
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}
function resetColWidth(name) {
  delete colWidths[name]
}

function isNumericType(t) {
  return NUMERIC_RE.test((t || '').toUpperCase())
}
function formatType(t) {
  const map = { VARCHAR:'text', INTEGER:'int', BIGINT:'bigint', DOUBLE:'float', FLOAT:'float', BOOLEAN:'bool', DATE:'date', TIMESTAMP:'ts', DECIMAL:'dec' }
  const key = Object.keys(map).find(k => (t || '').toUpperCase().startsWith(k))
  return key ? map[key] : (t || '').toLowerCase().slice(0, 6)
}

function colOptions(op) {
  if (op === 'COUNT') return dataStore.columns
  if (op === 'SUM' || op === 'AVG') return dataStore.columns.filter(c => isNumericType(c.type))
  // MIN / MAX 对所有类型都允许
  return dataStore.columns
}

function defaultAlias(agg) {
  if (agg.op === 'COUNT') return agg.col && agg.col !== '*' ? `count_${agg.col}` : 'count'
  if (!agg.col || agg.col === '*') return agg.op.toLowerCase()
  return `${agg.op.toLowerCase()}_${agg.col}`
}

const canRun = computed(() => {
  if (!groupStore.groupBy || groupStore.groupBy.length === 0) return false
  if (groupStore.aggs.length === 0) return false
  return groupStore.aggs.every(a => a.op === 'COUNT' || (a.col && a.col !== '*'))
})

const groupBy0 = computed(() => groupStore.groupBy[0] || '')
const groupBy1 = computed(() => groupStore.groupBy[1] || '')
const secondaryColOptions = computed(() =>
  dataStore.columns.filter(c => c.name !== groupBy0.value)
)

function onGroupChange(idx, value) {
  groupStore.setGroupByAt(idx, value)
}

const usingFilters = computed(() => dataStore.filters.length > 0 || !!dataStore.search)
const filterDesc = computed(() => {
  const parts = []
  if (dataStore.filters.length > 0) parts.push(`${dataStore.filters.length} 个筛选条件`)
  if (dataStore.search) parts.push('全局搜索')
  return parts.join(' + ')
})

function formatCell(v, type) {
  if (v === null || v === undefined) return 'NULL'
  if (typeof v !== 'number') return v
  if (!Number.isFinite(v)) return String(v)
  const T = (type || '').toUpperCase()
  // 整数类（COUNT / BIGINT / INTEGER）：千分位、不显示小数
  if (T.includes('INT')) {
    return v.toLocaleString('en-US', { maximumFractionDigits: 0 })
  }
  // 浮点：千分位、最多 2 位小数，去掉尾部多余 0
  return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function run() {
  groupStore.page = 1
  groupStore.sortCol = null
  await groupStore.loadStats(tablesStore.currentTable)
  if (groupStore.lastError) toast.add(groupStore.lastError, 'error')
}

function onSort(colName) {
  groupStore.setSort(colName)
  groupStore.loadStats(tablesStore.currentTable)
}

function goPage(p) {
  groupStore.goToPage(p)
  groupStore.loadStats(tablesStore.currentTable)
}
function onSizeChange(e) {
  groupStore.setPageSize(Number(e.target.value))
  groupStore.loadStats(tablesStore.currentTable)
}

function exportStats() {
  if (!groupStore.hasResult) return
  const cols = groupStore.columns.map(c => c.name)
  const escape = (v) => {
    if (v === null || v === undefined) return ''
    const s = String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const lines = [cols.join(',')]
  for (const row of groupStore.rows) {
    lines.push(cols.map(c => escape(row[c])).join(','))
  }
  const bom = '﻿'
  const blob = new Blob([bom + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${tablesStore.currentTable || 'group'}_stats.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  toast.add('分组结果已导出（当前页）', 'success')
}

// 切表时清空分组状态
watch(() => tablesStore.currentTable, () => {
  groupStore.reset()
  for (const k in colWidths) delete colWidths[k]
})
</script>

<style scoped lang="scss">
.group-stats {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  min-height: 0;
  padding-bottom: 12px;
}

.config-card {
  flex-shrink: 0;
}

.result-card {
  flex: 1;
  min-height: 0;
}

.config-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;

  .hint {
    font-size: 11px;
    color: var(--text-muted);
    margin-right: 4px;
  }
}

.config {
  &-panel {
    /* qb-card-body 已提供基础布局 */
  }

  &-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  &-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    min-width: 72px;
  }
}

.form-select.compact, .form-input.compact {
  padding: 6px 10px;
  font-size: 12px;
}

.aggs-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agg {
  &-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  &-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  &-op { flex: 0 0 140px; }
  &-col { flex: 1 1 180px; }
  &-alias { flex: 0 0 160px; }
}

.btn-add-agg {
  align-self: flex-start;
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 600;
  background: none;
  border: 1px dashed var(--border-light);
  color: var(--text-sub);
  padding: 4px 12px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
}

.hint {
  font-size: 12px;
  color: var(--text-muted);
}

.result-meta {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.error-banner {
  font-size: 12px;
  color: var(--danger);
  background: var(--danger-dim);
  border: 1px solid rgba(244,85,74,0.3);
  padding: 6px 10px;
  border-radius: var(--radius);
}

.result-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.empty-tip {
  padding: 32px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.result-scroll {
  flex: 1;
  overflow: auto;
}

.data-table {
  border-collapse: collapse;
  font-size: 13px;
  font-family: var(--font-mono);
  table-layout: fixed;

  thead {
    position: sticky;
    top: 0;
    z-index: 5;
  }

  th {
    position: relative;
    background: var(--surface);
    border-bottom: 2px solid var(--border);
    border-right: 1px solid var(--border);
    padding: 0;
    white-space: nowrap;
    font-family: var(--font-ui);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-sub);

    &:last-child { border-right: none; }

    &.sorted {
      .sort-icon { color: var(--accent); }
      .th-name { color: var(--accent); }
    }
  }

  tbody tr {
    border-bottom: 1px solid var(--border);
    transition: background 0.1s;

    &:hover { background: var(--surface-2); }
  }

  td {
    padding: 9px 14px;
    border-right: 1px solid var(--border);
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    &:last-child { border-right: none; }

    &.null-val {
      color: var(--text-muted);
      font-style: italic;
    }

    &.num-val {
      color: #7dd3fc;
      text-align: right;
    }
  }
}

.th-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
  overflow: hidden;

  &:hover { background: var(--surface-3); }
}

.th-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.th-type {
  font-size: 9px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-weight: 400;
  text-transform: lowercase;
  letter-spacing: 0;
}

.sort-icon {
  font-size: 10px;
  color: var(--text-muted);
  transition: color 0.15s;
}

.col-resizer {
  position: absolute;
  top: 0;
  right: -3px;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 10;
  background: transparent;
  transition: background 0.15s;

  &:hover, &.active {
    background: var(--accent);
  }
}

.empty-cell {
  text-align: center;
  padding: 32px;
  color: var(--text-muted);
}

.row-num {
  padding: 9px 12px;
  color: var(--text-muted);
  font-size: 11px;
  text-align: right;
  border-right: 1px solid var(--border);
  min-width: 44px;
  user-select: none;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}

.pg {
  &-btn {
    width: 32px;
    height: 32px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    color: var(--text-sub);
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;

    &:hover:not(:disabled) {
      border-color: var(--accent);
      color: var(--accent);
    }

    &:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }
  }

  &-info {
    font-size: 12px;
    font-family: var(--font-mono);
    color: var(--text-sub);
    padding: 0 8px;
    flex: 1;
    text-align: center;
  }

  &-size {
    font-family: var(--font-mono);
    font-size: 12px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    color: var(--text-sub);
    padding: 4px 8px;
    border-radius: 6px;
    cursor: pointer;

    &:focus {
      outline: none;
      border-color: var(--accent);
    }
  }
}
</style>
