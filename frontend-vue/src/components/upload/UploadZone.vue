<template>
  <div class="upload-zone" :class="{ dragging }" @click="triggerInput" @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onDrop">
    <input ref="fileRef" type="file" accept=".csv,.xlsx,.zip" multiple hidden @change="onFileChange" />
    <div class="upload-icon">⬆</div>
    <div class="upload-hint">拖拽或点击上传</div>
    <div class="upload-sub">支持 CSV、XLSX、ZIP 文件</div>
  </div>

  <ModalBase :show="showModeDialog" title="选择导入方式" @close="cancelUpload">
    <div v-if="isZipMode" class="zip-banner">📦 来自 ZIP：{{ zipFilename }}（{{ pendingFiles.length }} 个文件）</div>
    <div v-if="!isZipMode" class="mode-options">
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
    <div v-if="!isZipMode && uploadMode === 'append'" class="form-row">
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
          <span class="file-name">{{ f.relativePath || f.file.name }}</span>
          <span class="file-size">{{ formatSize(f.size ?? f.file?.size ?? 0) }}</span>
          <button v-if="!isZipMode" class="file-remove" @click="removePendingFile(i)">✕</button>
        </div>
        <div v-if="isZipMode || uploadMode === 'replace'" class="table-name-row">
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

  <ModalBase :show="showSheetPreviewDialog" title="多 Sheet 导入预览" @close="cancelSheetPreview" wide>
    <div class="sheet-preview-summary">
      <div class="sheet-preview-title">{{ previewFilename }}</div>
      <div class="sheet-preview-sub">相同表头的 Sheet 已自动分组；你可以选择是否导入，并修改每张表名。</div>
    </div>

    <div v-for="group in previewGroups" :key="group.group_id" class="sheet-group-card">
      <div class="sheet-group-header">
        <label class="sheet-group-check">
          <input type="checkbox" v-model="group.include" />
          <span>导入该分组</span>
        </label>
        <span class="sheet-group-meta">{{ group.sheet_names.length }} 个 Sheet · {{ group.row_count.toLocaleString() }} 行</span>
      </div>
      <div class="table-name-row sheet-table-name-row">
        <label class="table-name-label">表名</label>
        <input class="table-name-input" v-model="group.table_name" placeholder="自动生成" :disabled="!group.include" />
      </div>
      <div class="sheet-group-list">
        <div class="sheet-group-label">包含 Sheet：</div>
        <div class="sheet-chip-list">
          <span v-for="sheet in group.sheet_names" :key="sheet" class="sheet-chip">{{ sheet }}</span>
        </div>
      </div>
      <div class="sheet-group-list">
        <div class="sheet-group-label">表头：</div>
        <div class="header-chip-list">
          <span v-for="(header, idx) in group.header" :key="idx" class="header-chip">{{ header || '（空列名）' }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <button class="btn btn-ghost" @click="cancelSheetPreview" :disabled="importing">返回</button>
      <button class="btn btn-primary" :disabled="!canConfirmSheetPreview || importing" @click="confirmSheetImport">
        <span v-if="importing" class="btn-loading-spinner"></span>
        {{ importing ? '导入中...' : '确认导入这些分组' }}
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

const showModeDialog = ref(false)
const uploadMode = ref('replace')
const targetTable = ref('')
const pendingFiles = ref([])
const skipComments = ref(true)
const importing = ref(false)
const importProgress = ref(0)
const importProgressText = ref('')

const isZipMode = ref(false)
const originalZipFile = ref(null)
const zipFilename = ref('')

const showSheetPreviewDialog = ref(false)
const previewFile = ref(null)
const previewFilename = ref('')
const previewGroups = ref([])

const canConfirm = computed(() => {
  if (pendingFiles.value.length === 0) return false
  if (isZipMode.value) {
    return pendingFiles.value.every(f => f.tableName && f.tableName.trim())
  }
  if (uploadMode.value === 'append' && !targetTable.value) return false
  return true
})

const canConfirmSheetPreview = computed(() => {
  const selected = previewGroups.value.filter(g => g.include)
  return selected.length > 0 && selected.every(g => g.table_name && g.table_name.trim())
})

function triggerInput() { fileRef.value?.click() }

function onDrop(e) {
  dragging.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => /\.(csv|xlsx|zip)$/i.test(f.name))
  if (files.length === 0) {
    toast.add('只支持 CSV、XLSX、ZIP 文件', 'error')
    return
  }
  dispatchSelectedFiles(files)
}

function onFileChange(e) {
  const files = Array.from(e.target.files).filter(f => /\.(csv|xlsx|zip)$/i.test(f.name))
  if (files.length > 0) dispatchSelectedFiles(files)
  fileRef.value.value = ''
}

function dispatchSelectedFiles(files) {
  const zipFiles = files.filter(f => /\.zip$/i.test(f.name))
  const tabFiles = files.filter(f => /\.(csv|xlsx)$/i.test(f.name))
  if (zipFiles.length > 0 && (zipFiles.length > 1 || tabFiles.length > 0)) {
    toast.add('一次只能上传一个 ZIP，且不能与其他文件混合', 'error')
    return
  }
  if (zipFiles.length === 1) {
    openZipPreview(zipFiles[0])
    return
  }
  if (tabFiles.length > 0) openModeDialog(tabFiles)
}

function defaultTableName(filename) {
  return filename.replace(/\.(csv|xlsx)$/i, '').replace(/[-\s]/g, '_').toLowerCase()
}

function openModeDialog(files) {
  pendingFiles.value = files.map(f => ({ file: f, tableName: defaultTableName(f.name) }))
  uploadMode.value = 'replace'
  targetTable.value = ''
  isZipMode.value = false
  originalZipFile.value = null
  zipFilename.value = ''
  showModeDialog.value = true
}

async function openZipPreview(zipFile) {
  importing.value = true
  importProgressText.value = '正在解析 ZIP...'
  try {
    const fd = new FormData()
    fd.append('file', zipFile)
    const res = await api('/api/upload/zip-preview', { method: 'POST', body: fd })
    const data = await res.json()
    if (!data.files || data.files.length === 0) {
      toast.add('ZIP 中没有可导入的文件', 'error')
      return
    }
    pendingFiles.value = data.files.map(f => ({
      relativePath: f.relative_path,
      tableName: f.default_table_name,
      size: f.size,
    }))
    originalZipFile.value = zipFile
    zipFilename.value = data.filename
    isZipMode.value = true
    uploadMode.value = 'replace'
    targetTable.value = ''
    showModeDialog.value = true
  } catch (e) {
    toast.add(e.message, 'error')
  } finally {
    importing.value = false
    importProgressText.value = ''
  }
}

function cancelUpload() {
  showModeDialog.value = false
  pendingFiles.value = []
  isZipMode.value = false
  originalZipFile.value = null
  zipFilename.value = ''
}

function cancelSheetPreview() {
  showSheetPreviewDialog.value = false
  previewFile.value = null
  previewFilename.value = ''
  previewGroups.value = []
  importing.value = false
}

function removePendingFile(idx) {
  pendingFiles.value = pendingFiles.value.filter((_, i) => i !== idx)
  if (pendingFiles.value.length === 0) cancelUpload()
}

async function confirmUpload() {
  if (isZipMode.value) {
    await confirmZipImport()
    return
  }

  const items = [...pendingFiles.value]
  const mode = uploadMode.value
  const target = targetTable.value
  const comments = skipComments.value

  if (mode === 'replace' && items.length === 1 && items[0].file.name.endsWith('.xlsx')) {
    await previewXlsx(items[0].file)
    return
  }

  importing.value = true
  importProgress.value = 0
  importProgressText.value = '准备导入...'

  try {
    for (let i = 0; i < items.length; i++) {
      const { file, tableName } = items[i]
      importProgressText.value = `正在导入 (${i + 1}/${items.length}): ${file.name}`
      importProgress.value = Math.round((i / items.length) * 100)
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

async function confirmZipImport() {
  if (!originalZipFile.value) return
  importing.value = true
  importProgress.value = 10
  importProgressText.value = '正在导入 ZIP 内容...'
  try {
    const fd = new FormData()
    fd.append('file', originalZipFile.value)
    fd.append('plan', JSON.stringify({
      skip_comments: skipComments.value,
      items: pendingFiles.value.map(f => ({
        relative_path: f.relativePath,
        table_name: f.tableName.trim(),
      })),
    }))
    const res = await api('/api/upload/zip-import', { method: 'POST', body: fd })
    const data = await res.json()
    const ok = (data.results || []).filter(r => r.success)
    const bad = (data.results || []).filter(r => !r.success)
    for (const r of ok) toast.add(`已导入 "${r.table}"（${r.row_count.toLocaleString()} 行）`, 'success')
    for (const r of bad) toast.add(`${r.relative_path} 失败：${r.error}`, 'error')
    await tablesStore.loadTables()
    if (ok.length > 0) {
      const last = ok[ok.length - 1]
      tablesStore.selectTable(last.table)
      dataStore.reset()
      await dataStore.loadData(last.table)
    }
    window.dispatchEvent(new Event('files-changed'))
  } catch (e) {
    toast.add(e.message, 'error')
  } finally {
    importing.value = false
    importProgress.value = 0
    importProgressText.value = ''
    showModeDialog.value = false
    pendingFiles.value = []
    isZipMode.value = false
    originalZipFile.value = null
    zipFilename.value = ''
  }
}

async function previewXlsx(file) {
  importing.value = true
  importProgress.value = 20
  importProgressText.value = '正在分析多 Sheet Excel...'
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await api('/api/upload/xlsx-preview', { method: 'POST', body: formData })
    const data = await res.json()
    previewFile.value = file
    previewFilename.value = data.filename
    previewGroups.value = (data.groups || []).map(g => ({
      ...g,
      include: true,
      table_name: g.default_table_name,
    }))
    showModeDialog.value = false
    showSheetPreviewDialog.value = true
  } catch (e) {
    toast.add(e.message, 'error')
  } finally {
    importing.value = false
    importProgress.value = 0
    importProgressText.value = ''
  }
}

async function confirmSheetImport() {
  if (!previewFile.value) return
  importing.value = true
  importProgress.value = 10
  importProgressText.value = '正在导入多 Sheet 分组...'
  try {
    const formData = new FormData()
    formData.append('file', previewFile.value)
    formData.append('mode', 'replace')
    formData.append('skip_comments', skipComments.value ? 'true' : 'false')
    formData.append('plan', JSON.stringify(previewGroups.value.map(g => ({
      group_id: g.group_id,
      table_name: g.table_name.trim(),
      sheet_names: g.sheet_names,
      include: g.include,
    }))))
    const res = await api('/api/upload/xlsx-import', { method: 'POST', body: formData })
    const data = await res.json()
    const results = data.results || []
    for (const item of results) {
      toast.add(`已导入 "${item.table}"，共 ${item.row_count.toLocaleString()} 行`, 'success')
    }
    await tablesStore.loadTables()
    if (results.length > 0) {
      const last = results[results.length - 1]
      tablesStore.selectTable(last.table)
      dataStore.reset()
      await dataStore.loadData(last.table)
    }
    window.dispatchEvent(new Event('files-changed'))
    showSheetPreviewDialog.value = false
    pendingFiles.value = []
  } catch (e) {
    toast.add(e.message, 'error')
    throw e
  } finally {
    importing.value = false
    importProgress.value = 0
    importProgressText.value = ''
    previewFile.value = null
    previewFilename.value = ''
    previewGroups.value = []
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
.mode-options { display: flex; flex-direction: column; gap: 8px; }
.zip-banner {
  padding: 10px 12px; border-radius: var(--radius);
  background: var(--accent-dim); border: 1px solid var(--accent);
  color: var(--text); font-size: 12px; margin-bottom: 12px;
}
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
.pending-files { margin: 14px 0 12px; display: flex; flex-direction: column; gap: 10px; }
.pending-label { font-size: 11px; color: var(--text-sub); font-weight: 600; }
.pending-file-row { display: flex; flex-direction: column; gap: 8px; }
.pending-file { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: var(--surface-2); border: 1px solid var(--border-light); border-radius: var(--radius); }
.file-icon { font-size: 14px; }
.file-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; color: var(--text); }
.file-size { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }
.file-remove { border: none; background: transparent; color: var(--text-muted); cursor: pointer; padding: 0 2px; }
.file-remove:hover { color: var(--danger); }
.table-name-row, .form-row { display: flex; flex-direction: column; gap: 6px; }
.table-name-label, .form-row label { font-size: 11px; color: var(--text-sub); font-weight: 600; }
.table-name-input, .form-select {
  width: 100%; padding: 8px 10px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--surface-1); color: var(--text);
}
.comment-option { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.comment-label { font-size: 12px; color: var(--text-muted); }
.sheet-preview-summary { margin-bottom: 14px; }
.sheet-preview-title { font-size: 13px; font-weight: 700; color: var(--text); }
.sheet-preview-sub { margin-top: 4px; font-size: 11px; color: var(--text-muted); }
.sheet-group-card { border: 1px solid var(--border); border-radius: var(--radius); padding: 12px; margin-bottom: 12px; background: var(--surface-2); }
.sheet-group-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.sheet-group-check { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text); }
.sheet-group-meta { font-size: 11px; color: var(--text-muted); }
.sheet-group-list { margin-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.sheet-group-label { font-size: 11px; color: var(--text-sub); font-weight: 600; }
.sheet-chip-list, .header-chip-list { display: flex; flex-wrap: wrap; gap: 6px; }
.sheet-chip, .header-chip { padding: 4px 8px; border-radius: 999px; background: var(--surface-1); border: 1px solid var(--border-light); font-size: 11px; color: var(--text); }
.sheet-table-name-row { margin-top: 10px; }
</style>

