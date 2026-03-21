<template>
  <ModalBase :show="show" title="添加筛选条件" @close="show = false">
    <div class="form-row">
      <label>字段</label>
      <select v-model="col" class="form-select">
        <option v-for="c in dataStore.columns" :key="c.name" :value="c.name">{{ c.name }} ({{ formatType(c.type) }})</option>
      </select>
    </div>
    <div class="form-row">
      <label>运算符</label>
      <select v-model="op" class="form-select">
        <option value="LIKE">包含 (LIKE)</option>
        <option value="=">=  等于</option>
        <option value="!=">≠  不等于</option>
        <option value=">">>  大于</option>
        <option value="<">&lt;  小于</option>
        <option value=">=">>= 大于等于</option>
        <option value="<=">&lt;= 小于等于</option>
        <option value="IS NULL">为空</option>
        <option value="IS NOT NULL">不为空</option>
      </select>
    </div>
    <div v-if="op !== 'IS NULL' && op !== 'IS NOT NULL'" class="form-row">
      <label>值</label>
      <input type="text" v-model="val" class="form-input" placeholder="输入筛选值..." @keydown.enter="apply" />
    </div>
    <template #footer>
      <button class="btn btn-ghost" @click="show = false">取消</button>
      <button class="btn btn-primary" @click="apply">应用</button>
    </template>
  </ModalBase>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useDataStore } from '../../stores/data'
import { useTablesStore } from '../../stores/tables'
import { useToastStore } from '../../stores/toast'
import ModalBase from '../common/ModalBase.vue'

const dataStore = useDataStore()
const tablesStore = useTablesStore()
const toast = useToastStore()

const show = ref(false)
const col = ref('')
const op = ref('LIKE')
const val = ref('')

function formatType(t) {
  const map = { VARCHAR:'text', INTEGER:'int', BIGINT:'bigint', DOUBLE:'float', FLOAT:'float', BOOLEAN:'bool', DATE:'date', TIMESTAMP:'ts', DECIMAL:'dec' }
  const key = Object.keys(map).find(k => t.toUpperCase().startsWith(k))
  return key ? map[key] : t.toLowerCase().slice(0, 6)
}

function open() {
  if (dataStore.columns.length > 0) col.value = dataStore.columns[0].name
  op.value = 'LIKE'
  val.value = ''
  show.value = true
}

function apply() {
  if (op.value !== 'IS NULL' && op.value !== 'IS NOT NULL' && val.value.trim() === '') {
    toast.add('请输入筛选值', 'error')
    return
  }
  dataStore.addFilter({ col: col.value, op: op.value, val: val.value.trim() })
  show.value = false
  dataStore.loadData(tablesStore.currentTable)
}

function onOpen() { open() }
onMounted(() => window.addEventListener('open-filter-modal', onOpen))
onUnmounted(() => window.removeEventListener('open-filter-modal', onOpen))
</script>
