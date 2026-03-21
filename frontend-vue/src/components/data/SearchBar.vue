<template>
  <div v-if="tablesStore.currentTable" class="search-bar">
    <div class="search-inner">
      <span class="search-icon">🔍</span>
      <input
        type="text"
        class="search-input"
        placeholder="全表搜索..."
        :value="dataStore.search"
        @input="onInput"
        @keydown.enter="doSearch"
      />
      <button v-if="dataStore.search" class="search-clear" @click="clearSearch">✕</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDataStore } from '../../stores/data'
import { useTablesStore } from '../../stores/tables'

const dataStore = useDataStore()
const tablesStore = useTablesStore()

let debounceTimer = null
const localVal = ref(dataStore.search)

function onInput(e) {
  localVal.value = e.target.value
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    dataStore.setSearch(localVal.value)
    dataStore.loadData(tablesStore.currentTable)
  }, 400)
}

function doSearch() {
  clearTimeout(debounceTimer)
  dataStore.setSearch(localVal.value)
  dataStore.loadData(tablesStore.currentTable)
}

function clearSearch() {
  localVal.value = ''
  dataStore.setSearch('')
  dataStore.loadData(tablesStore.currentTable)
}
</script>

<style scoped>
.search-bar {
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 8px 20px; flex-shrink: 0;
}
.search-inner {
  display: flex; align-items: center; gap: 8px;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 0 12px;
  transition: border-color 0.15s;
}
.search-inner:focus-within { border-color: var(--accent); }
.search-icon { font-size: 14px; opacity: 0.5; }
.search-input {
  flex: 1; background: none; border: none; color: var(--text);
  font-family: var(--font-mono); font-size: 13px; padding: 8px 0; outline: none;
}
.search-input::placeholder { color: var(--text-muted); }
.search-clear {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  font-size: 12px; padding: 4px; transition: color 0.15s;
}
.search-clear:hover { color: var(--text); }
</style>
