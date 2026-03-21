<template>
  <div class="upload-zone" :class="{ dragging }" @click="triggerInput" @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onDrop">
    <input ref="fileRef" type="file" accept=".csv,.xlsx" multiple hidden @change="onFileChange" />
    <div class="upload-icon">⬆</div>
    <div class="upload-hint">拖拽或点击上传</div>
    <div class="upload-sub">支持 CSV、XLSX 文件</div>
  </div>

  <!-- Import mode dialog -->
  <ModalBase :show="showModeDialog" title="选择导入方式" @close="cancelUpload">
    <div class="mode-options">
      <label class="mode-option" :class="{ active: uploadMode === 'replace' }">
        <input type="radio" v-model="uploadMode" value="replace" />
        <div class="mode-content">
          <span class="mode-label">新建表</span>
          <span class="mode-desc">每个文件创建独立的新表（同名表将被替换）</span>
        </div>
      </label>
      <label class="mode-option" :class="{ active: uploadMode === 'append' }">
        <input type="radio" v-model="uploadMode" value="append" />
        <div class="mode-content">
          <span class="mode-label">追加到已有表</span>
          <span class="mode-desc">将文件数据追加到选定的已有表中（列结构需一致）</span>
        </div>
      </label>
    </div>
    <div v-if="uploadMode === 'append'" class="form-row">
      <label>目标表</label>
      <select class="form-select" v-model="targetTable">
        <option value="">-- 请选择目标表 --</option>
        <option v-for="t in tablesStore.tables" :key="t.name" :value="t.name">
          {{ t.name }}（{{ t.row_count.toLocaleString() }} 行 · {{ t.columns.length }} 列）
        </option>
      </select>
    </div>
    <div class="pending-files">
      <div class="pending-label">待导入文件（{{ pendingFiles.length }} 个）</div>
      <div v-for="(f, i) in pendingFiles" :key="i" class="pending-file-row">
        <div class="pending-file">
          <span class="file-icon">📄</span>
          <span class="file-name">{{ f.file.name }}</span>
          <span class="file-size">{{ formatSize(f.file.size) }}</span>
          <button class="file-remove" @click="removePendingFile(i)">✕</button>
        </div>
        <div v-if="uploadMode === 'replace'" class="table-name-row">
          <label class="table-name-label">表名</label>
          <input class="table-name-input" v-model="f.tableName" placeholder="自动生成" />
        </div>
      </div>
    </div>
    <label class="comment-option">
      <input type="checkbox" v-model="skipComments" />
      <span class="comment-label">忽略注释行（以 # 开头）</span>
    </label>
    <div v-if="importing" class="import-loading">
      <div class="import-spinner"></div>
      <div class="import-loading-text">{{ importProgressText }}</div>
      <div class="import-progress-bar"><div class="import-progress-fill" :style="{ width: importProgress + '%' }"></div></div>
    </div>
    <template #footer>
      <button class="btn btn-ghost" @click="cancelUpload" :disabled="importing">取消</button>
      <button class="btn btn-primary" :disabled="!canConfirm || importing" @click="confirmUpload">
        <span v-if="importing" class="btn-loading-spinner"></span>
        {{ importing ? '导入中...' : '确认导入' }}
      </button>
    </template>
  </ModalBase>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '../../api'
import { useTablesStore } from '../../stores/tables'
import { useDataStore } from '../../stores/data'
import { useToastStore } from '../../stores/toast'
import ModalBase from '../common/ModalBase.vue'

const tablesStore = useTablesStore()
const dataStore = useDataStore()
const toast = useToastStore()

const fileRef = ref(null)
const dragging = ref(false)

// Mode dialog state
const showModeDialog = ref(false)
const uploadMode = ref('replace')
const targetTable = ref('')
const pendingFiles = ref([])
const skipComments = ref(true)
const importing = ref(false)
const importProgress = ref(0)
const importProgressText = ref('')

const canConfirm = computed(() => {
  if (pendingFiles.value.length === 0) return false
  if (uploadMode.value === 'append' && !targetTable.value) return false
  return true
})

function triggerInput() { fileRef.value?.click() }

function onDrop(e) {
  dragging.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.csv') || f.name.endsWith('.xlsx'))
  if (files.length === 0) {
    toast.add('只支持 CSV 和 XLSX 文件', 'error')
    return
  }
  openModeDialog(files)
}

function onFileChange(e) {
  const files = Array.from(e.target.files).filter(f => f.name.endsWith('.csv') || f.name.endsWith('.xlsx'))
  if (files.length > 0) openModeDialog(files)
  fileRef.value.value = ''
}

function defaultTableName(filename) {
  return filename.replace(/\.(csv|xlsx)$/i, '').replace(/[-\s]/g, '_').toLowerCase()
}

function openModeDialog(files) {
  pendingFiles.value = files.map(f => ({ file: f, tableName: defaultTableName(f.name) }))
  uploadMode.value = 'replace'
  targetTable.value = ''
  showModeDialog.value = true
}

function cancelUpload() {
  showModeDialog.value = false
  pendingFiles.value = []
}

function removePendingFile(idx) {
  pendingFiles.value = pendingFiles.value.filter((_, i) => i !== idx)
  if (pendingFiles.value.length === 0) cancelUpload()
}

async function confirmUpload() {
  const items = [...pendingFiles.value]
  const mode = uploadMode.value
  const target = targetTable.value
  const comments = skipComments.value

  importing.value = true
  importProgress.value = 0
  importProgressText.value = '准备导入...'

  try {
    for (let i = 0; i < items.length; i++) {
      const { file, tableName } = items[i]
      importProgressText.value = `正在导入 (${i + 1}/${items.length}): ${file.name}`
      importProgress.value = Math.round(((i) / items.length) * 100)
      const customName = mode === 'replace' ? tableName.trim() : ''
      await uploadSingle(file, mode, target, comments, customName)
    }
    importProgress.value = 100
    importProgressText.value = '导入完成！'
    await new Promise(r => setTimeout(r, 800))
  } finally {
    importing.value = false
    showModeDialog.value = false
    pendingFiles.value = []
  }
}

async function uploadSingle(file, mode, target, comments, customName) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', mode)
  if (comments) {
    formData.append('skip_comments', 'true')
  }
  if (mode === 'append' && target) {
    formData.append('table_name', target)
  } else if (mode === 'replace' && customName) {
    formData.append('table_name', customName)
  }

  try {
    const res = await api('/api/upload', { method: 'POST', body: formData })
    const data = await res.json()

    const action = mode === 'append' ? '追加' : '导入'
    toast.add(`已${action} "${data.table}"，共 ${data.row_count.toLocaleString()} 行`, 'success')
    await tablesStore.loadTables()
    tablesStore.selectTable(data.table)
    dataStore.reset()
    await dataStore.loadData(data.table)
    window.dispatchEvent(new Event('files-changed'))
  } catch (e) {
    toast.add(e.message, 'error')
    throw e
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.upload-zone {
  border: 1.5px dashed var(--border-light); border-radius: var(--radius);
  padding: 18px 12px; text-align: center; cursor: pointer;
  transition: all 0.2s; background: var(--surface-2);
}
.upload-zone:hover, .upload-zone.dragging { border-color: var(--accent); background: var(--accent-dim); }
.upload-icon { font-size: 22px; margin-bottom: 8px; color: var(--accent); }
.upload-hint { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 3px; }
.upload-sub { font-size: 11px; color: var(--text-muted); }
.upload-progress { margin-top: 10px; }
.progress-bar { height: 3px; background: var(--surface-3); border-radius: 2px; overflow: hidden; margin-bottom: 6px; }
.progress-fill { height: 100%; background: var(--accent); transition: width 0.3s ease; border-radius: 2px; }
.upload-progress span { font-size: 11px; color: var(--text-sub); font-family: var(--font-mono); }

/* Import loading state in modal */
.import-loading {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 16px 0 8px;
}
.import-spinner {
  width: 28px; height: 28px; border: 3px solid var(--border-light);
  border-top-color: var(--accent); border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.import-loading-text {
  font-size: 12px; color: var(--text-muted); text-align: center;
}
.import-progress-bar {
  width: 100%; height: 4px; background: var(--surface-3);
  border-radius: 2px; overflow: hidden;
}
.import-progress-fill {
  height: 100%; background: var(--accent); transition: width 0.3s ease; border-radius: 2px;
}
.btn-loading-spinner {
  display: inline-block; width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
  border-radius: 50%; animation: spin 0.8s linear infinite;
  margin-right: 6px; vertical-align: middle;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Mode dialog */
.mode-options { display: flex; flex-direction: column; gap: 8px; }
.mode-option {
  display: flex; align-items: flex-start; gap: 10px; padding: 12px;
  border: 1px solid var(--border); border-radius: var(--radius);
  cursor: pointer; transition: all 0.15s;
}
.mode-option:hover { border-color: var(--border-light); }
.mode-option.active { border-color: var(--accent); background: var(--accent-dim); }
.mode-option input[type="radio"] { margin-top: 2px; accent-color: var(--accent); }
.mode-content { display: flex; flex-direction: column; gap: 2px; }
.mode-label { font-size: 13px; font-weight: 600; color: var(--text); }
.mode-desc { font-size: 11px; color: var(--text-muted); line-height: 1.5; }

.pending-files { display: flex; flex-direction: column; gap: 6px; }
.pending-label { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); }
.pending-file {
  display: flex; align-items: center; gap: 8px; padding: 6px 10px;
  background: var(--surface-2); border-radius: var(--radius); font-size: 12px;
}
.file-icon { font-size: 14px; flex-shrink: 0; }
.file-name { flex: 1; color: var(--text); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); flex-shrink: 0; }
.file-remove {
  width: 18px; height: 18px; background: none; border: none; color: var(--text-muted);
  cursor: pointer; border-radius: 4px; font-size: 11px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.file-remove:hover { color: var(--danger); background: var(--danger-dim); }

.pending-file-row { display: flex; flex-direction: column; gap: 4px; }
.table-name-row {
  display: flex; align-items: center; gap: 8px; padding: 0 10px 4px;
}
.table-name-label {
  font-size: 11px; color: var(--text-muted); flex-shrink: 0; white-space: nowrap;
}
.table-name-input {
  flex: 1; height: 26px; padding: 0 8px; font-size: 12px;
  border: 1px solid var(--border); border-radius: 4px;
  background: var(--surface-1); color: var(--text);
  outline: none; transition: border-color 0.15s;
}
.table-name-input:focus { border-color: var(--accent); }
.table-name-input::placeholder { color: var(--text-muted); }

.comment-option {
  display: flex; align-items: center; gap: 8px; padding: 8px 0;
  cursor: pointer; font-size: 12px;
}
.comment-option input[type="checkbox"] { accent-color: var(--accent); }
.comment-label { color: var(--text-muted); }
</style>
