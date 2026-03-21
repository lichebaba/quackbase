<template>
  <div class="table-scroll">
    <table class="data-table">
      <thead>
        <tr>
          <th style="width:44px"><div class="th-inner">#</div></th>
          <th v-for="c in dataStore.columns" :key="c.name"
              :class="{ sorted: dataStore.sortCol === c.name }"
          >
            <div class="th-inner" @click="dataStore.toggleSort(c.name); reload()">
              <span class="th-name">{{ c.name }}</span>
              <span class="th-type">{{ formatType(c.type) }}</span>
              <span class="sort-icon">{{ dataStore.sortCol === c.name ? (dataStore.sortDir === 'asc' ? '↑' : '↓') : '↕' }}</span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="dataStore.rows.length === 0">
          <td :colspan="dataStore.columns.length + 1" style="text-align:center;padding:32px;color:var(--text-muted)">暂无数据</td>
        </tr>
        <tr v-for="(row, i) in dataStore.rows" :key="i">
          <td class="row-num">{{ (dataStore.page - 1) * dataStore.pageSize + i + 1 }}</td>
          <td v-for="c in dataStore.columns" :key="c.name"
              :class="{ 'null-val': row[c.name] === null || row[c.name] === undefined, 'num-val': isNumericType(c.type) && row[c.name] !== null }"
              :title="String(row[c.name] ?? '')"
          >
            {{ row[c.name] === null || row[c.name] === undefined ? 'NULL' : row[c.name] }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { useDataStore } from '../../stores/data'
import { useTablesStore } from '../../stores/tables'

const dataStore = useDataStore()
const tablesStore = useTablesStore()

function reload() {
  dataStore.loadData(tablesStore.currentTable)
}

function formatType(t) {
  const map = { VARCHAR:'text', INTEGER:'int', BIGINT:'bigint', DOUBLE:'float', FLOAT:'float', BOOLEAN:'bool', DATE:'date', TIMESTAMP:'ts', DECIMAL:'dec' }
  const key = Object.keys(map).find(k => t.toUpperCase().startsWith(k))
  return key ? map[key] : t.toLowerCase().slice(0, 6)
}

function isNumericType(t) {
  return /INT|FLOAT|DOUBLE|DECIMAL|NUMERIC|REAL/.test(t.toUpperCase())
}
</script>

<style scoped>
.table-scroll { flex: 1; overflow: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: var(--font-mono); }
.data-table thead { position: sticky; top: 0; z-index: 5; }
.data-table th {
  background: var(--surface); border-bottom: 2px solid var(--border);
  border-right: 1px solid var(--border); padding: 0; white-space: nowrap;
  font-family: var(--font-ui); font-size: 11px; font-weight: 700;
  letter-spacing: 0.05em; text-transform: uppercase; color: var(--text-sub);
}
.data-table th:last-child { border-right: none; }
.th-inner {
  display: flex; align-items: center; gap: 6px; padding: 10px 14px;
  cursor: pointer; transition: background 0.15s; user-select: none;
}
.th-inner:hover { background: var(--surface-3); }
.th-name { flex: 1; }
.th-type { font-size: 9px; font-family: var(--font-mono); color: var(--text-muted); font-weight: 400; text-transform: lowercase; letter-spacing: 0; }
.sort-icon { font-size: 10px; color: var(--text-muted); transition: color 0.15s; }
.data-table th.sorted .sort-icon { color: var(--accent); }
.data-table th.sorted .th-name { color: var(--accent); }
.data-table tbody tr { border-bottom: 1px solid var(--border); transition: background 0.1s; }
.data-table tbody tr:hover { background: var(--surface-2); }
.data-table td {
  padding: 9px 14px; border-right: 1px solid var(--border); color: var(--text);
  max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.data-table td:last-child { border-right: none; }
.data-table td.null-val { color: var(--text-muted); font-style: italic; }
.data-table td.num-val { color: #7dd3fc; text-align: right; }
.row-num {
  padding: 9px 12px; color: var(--text-muted); font-size: 11px;
  text-align: right; border-right: 1px solid var(--border); min-width: 44px; user-select: none;
}
</style>
