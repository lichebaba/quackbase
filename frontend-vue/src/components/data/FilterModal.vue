<template>
  <ModalBase :show="show" :title="editingIdx !== null ? '编辑筛选条件' : '添加筛选条件'" wide @close="show = false">
    <ElConfigProvider :locale="zhCn">
      <div class="form-row">
        <label>字段</label>
        <select v-model="col" class="form-select" @change="onColChange">
          <option v-for="c in dataStore.columns" :key="c.name" :value="c.name">{{ c.name }} ({{ formatType(c.type) }})</option>
        </select>
      </div>
      <div class="form-row">
        <label>运算符</label>
        <select v-model="op" class="form-select" @change="onOpChange">
          <option v-if="isDateCol" value="BETWEEN">在区间内 (BETWEEN)</option>
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
        <div class="value-input">
          <!-- 日期区间 -->
          <ElDatePicker
            v-if="isDateCol && op === 'BETWEEN'"
            v-model="dateRangeVal"
            :type="isTimestampCol ? 'datetimerange' : 'daterange'"
            :format="isTimestampCol ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD'"
            :value-format="isTimestampCol ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD'"
            range-separator=" 至 "
            start-placeholder="起始时间"
            end-placeholder="结束时间"
            clearable
            :default-time="isTimestampCol ? defaultRangeTime : undefined"
            popper-class="qb-date-popper"
            teleported
            style="width: 100%;"
          />
          <!-- 日期 / 日期时间 -->
          <ElDatePicker
            v-else-if="isDateCol"
            v-model="dateVal"
            :type="isTimestampCol ? 'datetime' : 'date'"
            :format="isTimestampCol ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD'"
            :value-format="isTimestampCol ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD'"
            :placeholder="isTimestampCol ? '选择日期与时间（精确到秒）' : '选择日期'"
            clearable
            popper-class="qb-date-popper"
            teleported
            style="width: 100%;"
          />
          <!-- 普通文本 -->
          <input
            v-else
            type="text"
            v-model="val"
            class="form-input"
            placeholder="输入筛选值..."
            @keydown.enter="apply"
          />
        </div>
      </div>
    </ElConfigProvider>
    <template #footer>
      <button class="btn btn-ghost" @click="show = false">取消</button>
      <button class="btn btn-primary" @click="apply">{{ editingIdx !== null ? '保存修改' : '应用' }}</button>
    </template>
  </ModalBase>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElDatePicker, ElConfigProvider } from 'element-plus'
// @ts-ignore — locale 包未提供 .d.ts，运行时正常
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
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
const dateVal = ref(null)
const dateRangeVal = ref(null)
// 当前是否在编辑现有条件；null 表示新建
const editingIdx = ref(null)
// 区间日期的默认时分秒：起 00:00:00、止 23:59:59
const defaultRangeTime = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const currentColType = computed(() => {
  const c = dataStore.columns.find(c => c.name === col.value)
  return (c?.type || '').toUpperCase()
})
const isTimestampCol = computed(() => {
  const t = currentColType.value
  return t.includes('TIMESTAMP') || t.startsWith('DATETIME')
})
const isDateOnlyCol = computed(() => {
  const t = currentColType.value
  return t.startsWith('DATE') && !isTimestampCol.value
})
const isDateCol = computed(() => isTimestampCol.value || isDateOnlyCol.value)

function formatType(t) {
  const map = { VARCHAR:'text', INTEGER:'int', BIGINT:'bigint', DOUBLE:'float', FLOAT:'float', BOOLEAN:'bool', DATE:'date', TIMESTAMP:'ts', DECIMAL:'dec' }
  const key = Object.keys(map).find(k => t.toUpperCase().startsWith(k))
  return key ? map[key] : t.toLowerCase().slice(0, 6)
}

function resetValues() {
  val.value = ''
  dateVal.value = null
  dateRangeVal.value = null
}

function onColChange() {
  resetValues()
  // 切到日期列，默认推荐"区间"操作（最常见的场景）
  if (isDateCol.value) {
    if (!['BETWEEN', '=', '!=', '>', '<', '>=', '<=', 'IS NULL', 'IS NOT NULL'].includes(op.value)) {
      op.value = 'BETWEEN'
    }
  } else if (op.value === 'BETWEEN') {
    // 非日期列不支持 BETWEEN，回落到 LIKE
    op.value = 'LIKE'
  }
}

function onOpChange() {
  // 在不同的输入控件之间切换时，重置已选的值，避免脏数据
  resetValues()
}

function open(payload) {
  const editIdx = payload && typeof payload.editIdx === 'number' ? payload.editIdx : null
  if (editIdx !== null && dataStore.filters[editIdx]) {
    // 编辑模式：用现有 filter 的值预填表单
    const f = dataStore.filters[editIdx]
    editingIdx.value = editIdx
    col.value = f.col
    op.value = f.op
    val.value = ''
    dateVal.value = null
    dateRangeVal.value = null
    if (isDateCol.value) {
      dateVal.value = f.val || null
    } else if (f.op !== 'IS NULL' && f.op !== 'IS NOT NULL') {
      val.value = f.val || ''
    }
  } else {
    // 新建模式
    editingIdx.value = null
    if (dataStore.columns.length > 0) col.value = dataStore.columns[0].name
    op.value = isDateCol.value ? 'BETWEEN' : 'LIKE'
    resetValues()
  }
  show.value = true
}

function apply() {
  try {
    const needsValue = op.value !== 'IS NULL' && op.value !== 'IS NOT NULL'
    const tableName = tablesStore.currentTable
    const isEdit = editingIdx.value !== null

    if (op.value === 'BETWEEN') {
      const v = dateRangeVal.value
      if (!Array.isArray(v) || !v[0] || !v[1]) {
        toast.add('请选择完整的日期区间', 'error')
        return
      }
      const [start, end] = v
      // 区间会拆成两条 filter；编辑场景下用第一条替换原 chip，第二条追加
      if (isEdit) {
        dataStore.updateFilter(editingIdx.value, { col: col.value, op: '>=', val: String(start) })
        dataStore.addFilter({ col: col.value, op: '<=', val: String(end) })
      } else {
        dataStore.addFilter({ col: col.value, op: '>=', val: String(start) })
        dataStore.addFilter({ col: col.value, op: '<=', val: String(end) })
      }
    } else if (needsValue) {
      let finalVal = ''
      if (isDateCol.value) {
        if (!dateVal.value) {
          toast.add('请选择日期', 'error')
          return
        }
        finalVal = String(dateVal.value)
      } else {
        if (val.value.trim() === '') {
          toast.add('请输入筛选值', 'error')
          return
        }
        finalVal = val.value.trim()
      }
      const newFilter = { col: col.value, op: op.value, val: finalVal }
      isEdit ? dataStore.updateFilter(editingIdx.value, newFilter) : dataStore.addFilter(newFilter)
    } else {
      const newFilter = { col: col.value, op: op.value, val: '' }
      isEdit ? dataStore.updateFilter(editingIdx.value, newFilter) : dataStore.addFilter(newFilter)
    }

    show.value = false
    editingIdx.value = null
    if (dataStore.viewMode !== 'group' && tableName) {
      dataStore.loadData(tableName).catch(e => toast.add(e.message || '加载数据失败', 'error'))
    }
  } catch (e) {
    toast.add(e?.message || '应用筛选失败', 'error')
  }
}

// 字段类型变化时，已经在 onColChange 中重置过值；不再加 watch，避免 open() 编辑模式被覆盖

function onOpen(e) { open(e?.detail) }
onMounted(() => window.addEventListener('open-filter-modal', onOpen))
onUnmounted(() => window.removeEventListener('open-filter-modal', onOpen))
</script>

<style scoped>
.value-input { width: 100%; }
</style>

<style>
/* 让 element-plus DatePicker 的输入框 / 弹层贴合应用的暗色主题 —— 必须用全局样式，
   因为 popper 通过 teleport 渲染到 body 上 */
.el-date-editor .el-input__wrapper,
.el-range-editor.el-input__wrapper {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
  color: var(--text) !important;
}
.el-date-editor .el-input__wrapper.is-focus,
.el-range-editor.el-input__wrapper.is-focus,
.el-date-editor .el-input__wrapper:hover,
.el-range-editor.el-input__wrapper:hover {
  border-color: var(--accent) !important;
  box-shadow: none !important;
}
.el-date-editor .el-input__inner,
.el-range-editor .el-range-input {
  color: var(--text) !important;
  font-family: var(--font-mono) !important;
}
.el-date-editor .el-input__inner::placeholder,
.el-range-editor .el-range-input::placeholder {
  color: var(--text-muted) !important;
}
.el-range-editor .el-range-separator { color: var(--text-sub) !important; }
.el-date-editor .el-input__prefix,
.el-range-editor .el-range__icon,
.el-range-editor .el-range__close-icon,
.el-date-editor .el-input__suffix { color: var(--text-muted) !important; }

.qb-date-popper.el-popper {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
}
.qb-date-popper .el-picker-panel,
.qb-date-popper .el-date-picker,
.qb-date-popper .el-date-range-picker {
  background: var(--surface) !important;
  color: var(--text) !important;
  border: none !important;
}
.qb-date-popper .el-picker-panel__icon-btn,
.qb-date-popper .el-date-picker__header-label,
.qb-date-popper .el-date-table th,
.qb-date-popper .el-date-range-picker__header { color: var(--text-sub) !important; }
.qb-date-popper .el-date-table td.available .el-date-table-cell { color: var(--text) !important; }
.qb-date-popper .el-date-table td.next-month .el-date-table-cell,
.qb-date-popper .el-date-table td.prev-month .el-date-table-cell { color: var(--text-muted) !important; }
.qb-date-popper .el-date-table td.today .el-date-table-cell__text { color: var(--accent) !important; font-weight: 700; }
.qb-date-popper .el-date-table td.current:not(.disabled) .el-date-table-cell__text,
.qb-date-popper .el-date-table td.start-date .el-date-table-cell__text,
.qb-date-popper .el-date-table td.end-date .el-date-table-cell__text {
  background: var(--accent) !important; color: #000 !important;
}
.qb-date-popper .el-date-table td.in-range .el-date-table-cell { background: var(--accent-dim) !important; }
.qb-date-popper .el-picker-panel__footer { background: var(--surface) !important; border-top: 1px solid var(--border) !important; }
.qb-date-popper .el-button.is-plain {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-sub) !important;
}
.qb-date-popper .el-button--primary {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #000 !important;
}
.qb-date-popper .el-time-spinner__item.is-active:not(.is-disabled) { color: var(--accent) !important; }
</style>
