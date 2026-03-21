<template>
  <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-duck">🦆</span>
        <span class="logo-text">Quack<em>base</em></span>
      </div>
    </div>

    <!-- USER INFO -->
    <div class="user-bar">
      <div class="user-info">
        <span class="user-avatar">{{ auth.user?.username?.[0]?.toUpperCase() || '?' }}</span>
        <div class="user-detail">
          <span class="user-name">{{ auth.user?.username || '—' }}</span>
          <span class="user-role">{{ auth.user?.role || '—' }}</span>
        </div>
      </div>
      <div class="user-actions">
        <button class="icon-btn" title="修改密码" @click="showPwdModal = true">🔑</button>
        <button class="icon-btn" title="退出登录" @click="doLogout">⏻</button>
      </div>
    </div>

    <!-- UPLOAD -->
    <div v-if="auth.canUpload" class="sidebar-section">
      <div class="section-label">上传数据</div>
      <UploadZone />
      <!-- File management -->
      <div v-if="uploadedFiles.length > 0" class="file-mgmt">
        <div class="file-mgmt-header">
          <span class="file-mgmt-label">已上传文件 ({{ uploadedFiles.length }})</span>
          <button class="file-mgmt-toggle" @click="showFiles = !showFiles">{{ showFiles ? '收起' : '展开' }}</button>
        </div>
        <div v-if="showFiles" class="file-list">
          <div v-for="f in uploadedFiles" :key="f.name" class="file-item">
            <span class="file-item-name" :title="f.name">{{ f.name }}</span>
            <span class="file-item-size">{{ formatFileSize(f.size) }}</span>
            <button class="file-item-del" title="删除文件" @click="deleteFile(f.name)">✕</button>
          </div>
          <button class="clear-all-btn" @click="clearAllFiles">清除全部文件</button>
        </div>
      </div>
    </div>

    <!-- TABLE LIST -->
    <div class="sidebar-section">
      <div class="section-label">数据表 <span class="table-count">{{ tablesStore.tables.length }}</span></div>
      <div class="table-list">
        <div v-if="tablesStore.tables.length === 0" class="empty-tables">暂无数据表<br>请先上传文件</div>
        <div
          v-for="t in tablesStore.tables" :key="t.name"
          class="table-item" :class="{ active: tablesStore.currentTable === t.name }"
          @click="onSelectTable(t.name)"
        >
          <span class="table-icon">⊞</span>
          <div class="table-item-info">
            <div class="table-item-name">{{ t.name }}</div>
            <div class="table-item-meta">{{ t.row_count.toLocaleString() }} 行 · {{ t.columns.length }} 列</div>
          </div>
          <button v-if="auth.canDelete" class="table-del" title="删除" @click.stop="onDeleteTable(t.name)">✕</button>
        </div>
      </div>
    </div>

    <!-- ADMIN -->
    <div v-if="auth.isAdmin" class="sidebar-section">
      <div class="section-label">管理</div>
      <button class="menu-btn" @click="showUserMgmt">👥 用户管理</button>
    </div>

    <div class="sidebar-footer">
      <span class="db-status" :class="{ connected: dbConnected }">{{ dbConnected ? '● 已连接' : '● 未连接' }}</span>
    </div>
  </aside>

  <!-- Change password modal -->
  <ModalBase :show="showPwdModal" title="修改密码" @close="showPwdModal = false">
    <div class="form-row">
      <label>原密码</label>
      <input type="password" v-model="oldPwd" class="form-input" placeholder="输入原密码" />
    </div>
    <div class="form-row">
      <label>新密码</label>
      <input type="password" v-model="newPwd" class="form-input" placeholder="输入新密码" />
    </div>
    <div class="form-row">
      <label>确认新密码</label>
      <input type="password" v-model="confirmPwd" class="form-input" placeholder="再次输入新密码" />
    </div>
    <template #footer>
      <button class="btn btn-ghost" @click="showPwdModal = false">取消</button>
      <button class="btn btn-primary" @click="doChangePassword">确认修改</button>
    </template>
  </ModalBase>
</template>

<script setup>
import { ref, provide, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useTablesStore } from '../../stores/tables'
import { useDataStore } from '../../stores/data'
import { useToastStore } from '../../stores/toast'
import { apiJson, api } from '../../api'
import UploadZone from '../upload/UploadZone.vue'
import ModalBase from '../common/ModalBase.vue'

const router = useRouter()
const auth = useAuthStore()
const tablesStore = useTablesStore()
const dataStore = useDataStore()
const toast = useToastStore()

const sidebarCollapsed = ref(false)
const dbConnected = ref(false)
const showPwdModal = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const showFiles = ref(false)
const uploadedFiles = ref([])

provide('sidebarCollapsed', sidebarCollapsed)

onMounted(async () => {
  try {
    await tablesStore.loadTables()
    dbConnected.value = true
    await loadUploadedFiles()
  } catch {
    dbConnected.value = false
  }
  window.addEventListener('files-changed', loadUploadedFiles)
})

onUnmounted(() => {
  window.removeEventListener('files-changed', loadUploadedFiles)
})

async function loadUploadedFiles() {
  try {
    const data = await apiJson('/api/files')
    uploadedFiles.value = data?.files || []
  } catch { /* ignore */ }
}

async function deleteFile(filename) {
  if (!confirm(`确认删除文件 "${filename}"？`)) return
  try {
    await api(`/api/files/${encodeURIComponent(filename)}`, { method: 'DELETE' })
    toast.add(`文件 "${filename}" 已删除`, 'success')
    await loadUploadedFiles()
  } catch (e) {
    toast.add(e.message, 'error')
  }
}

async function clearAllFiles() {
  if (!confirm('确认清除所有已上传文件？此操作不会删除已导入的数据表。')) return
  try {
    await api('/api/files', { method: 'DELETE' })
    toast.add('所有文件已清除', 'success')
    uploadedFiles.value = []
    showFiles.value = false
  } catch (e) {
    toast.add(e.message, 'error')
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function onSelectTable(name) {
  tablesStore.selectTable(name)
  dataStore.reset()
  await dataStore.loadData(name)
}

async function onDeleteTable(name) {
  if (!confirm(`确认删除表 "${name}"？`)) return
  try {
    await tablesStore.deleteTable(name)
    toast.add(`表 "${name}" 已删除`, 'success')
  } catch (e) {
    toast.add(e.message, 'error')
  }
}

function doLogout() {
  auth.logout()
  router.push('/login')
}

async function doChangePassword() {
  if (!oldPwd.value || !newPwd.value) { toast.add('请填写完整', 'error'); return }
  if (newPwd.value !== confirmPwd.value) { toast.add('两次密码不一致', 'error'); return }
  if (newPwd.value.length < 6) { toast.add('新密码至少 6 位', 'error'); return }
  try {
    await auth.changePassword(oldPwd.value, newPwd.value)
    showPwdModal.value = false
    oldPwd.value = ''; newPwd.value = ''; confirmPwd.value = ''
    toast.add('密码已修改，请重新登录', 'success')
    setTimeout(() => { auth.logout(); router.push('/login') }, 1500)
  } catch (e) { toast.add(e.message, 'error') }
}

function showUserMgmt() {
  window.dispatchEvent(new Event('open-user-mgmt'))
}

defineExpose({ sidebarCollapsed })
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-w); min-width: var(--sidebar-w);
  background: var(--surface); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden;
  transition: width 0.25s ease, min-width 0.25s ease;
  position: relative; z-index: 10;
}
.sidebar.collapsed { width: 0; min-width: 0; border-right: none; }
.sidebar-header { padding: 20px 20px 16px; border-bottom: 1px solid var(--border); }
.logo { display: flex; align-items: center; gap: 10px; }
.logo-duck { font-size: 26px; line-height: 1; }
.logo-text { font-family: var(--font-ui); font-size: 15px; font-weight: 700; line-height: 1.2; letter-spacing: 0.02em; }
.logo-text em { font-style: normal; color: var(--accent); font-weight: 400; }
.sidebar-section { padding: 16px; border-bottom: 1px solid var(--border); }
.section-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px;
  display: flex; align-items: center; gap: 6px;
}
.table-count {
  background: var(--accent); color: #000; font-size: 9px; font-weight: 700;
  padding: 1px 5px; border-radius: 20px;
}
.table-list { display: flex; flex-direction: column; gap: 4px; max-height: calc(100vh - 380px); overflow-y: auto; }
.empty-tables { text-align: center; font-size: 12px; color: var(--text-muted); padding: 16px 8px; line-height: 1.6; }
.table-item {
  display: flex; align-items: center; padding: 8px 10px; border-radius: var(--radius);
  cursor: pointer; transition: background 0.15s; gap: 8px; position: relative;
}
.table-item:hover { background: var(--surface-3); }
.table-item.active { background: var(--accent-dim); }
.table-item.active::before {
  content: ''; position: absolute; left: 0; top: 4px; bottom: 4px;
  width: 3px; background: var(--accent); border-radius: 2px;
}
.table-icon { font-size: 14px; flex-shrink: 0; }
.table-item-info { flex: 1; min-width: 0; }
.table-item-name {
  font-size: 13px; font-weight: 600; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.table-item.active .table-item-name { color: var(--accent); }
.table-item-meta { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); }
.table-del {
  width: 20px; height: 20px; background: none; border: none; color: var(--text-muted);
  cursor: pointer; border-radius: 4px; display: flex; align-items: center;
  justify-content: center; font-size: 13px; opacity: 0; transition: all 0.15s; flex-shrink: 0;
}
.table-item:hover .table-del { opacity: 1; }
.table-del:hover { color: var(--danger); background: var(--danger-dim); }
.sidebar-footer { margin-top: auto; padding: 12px 16px; border-top: 1px solid var(--border); }
.db-status { font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); }
.db-status.connected { color: var(--success); }
.user-bar {
  padding: 10px 14px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
}
.user-info { display: flex; align-items: center; gap: 8px; min-width: 0; }
.user-avatar {
  width: 28px; height: 28px; background: var(--accent-dim);
  border: 1px solid rgba(245,200,66,0.3); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: var(--accent); flex-shrink: 0;
}
.user-detail { display: flex; flex-direction: column; min-width: 0; }
.user-name {
  font-size: 13px; font-weight: 700; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.user-role { font-size: 10px; font-family: var(--font-mono); color: var(--text-muted); }
.user-actions { display: flex; gap: 4px; flex-shrink: 0; }
.menu-btn {
  width: 100%; background: var(--surface-2); border: 1px solid var(--border);
  color: var(--text-sub); border-radius: var(--radius); font-family: var(--font-ui);
  font-size: 13px; font-weight: 600; padding: 8px 12px; text-align: left;
  cursor: pointer; transition: all 0.15s;
}
.menu-btn:hover { border-color: var(--accent); color: var(--accent); }

/* File management */
.file-mgmt { margin-top: 12px; }
.file-mgmt-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;
}
.file-mgmt-label { font-size: 11px; color: var(--text-muted); font-weight: 600; }
.file-mgmt-toggle {
  background: none; border: none; color: var(--accent); cursor: pointer;
  font-size: 11px; font-family: var(--font-ui); padding: 0;
}
.file-mgmt-toggle:hover { text-decoration: underline; }
.file-list { display: flex; flex-direction: column; gap: 4px; max-height: 160px; overflow-y: auto; }
.file-item {
  display: flex; align-items: center; gap: 6px; padding: 4px 8px;
  background: var(--surface-2); border-radius: 4px; font-size: 11px;
}
.file-item-name {
  flex: 1; min-width: 0; color: var(--text-sub);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.file-item-size { font-family: var(--font-mono); color: var(--text-muted); font-size: 10px; flex-shrink: 0; }
.file-item-del {
  width: 16px; height: 16px; background: none; border: none; color: var(--text-muted);
  cursor: pointer; border-radius: 3px; font-size: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; opacity: 0; transition: all 0.15s;
}
.file-item:hover .file-item-del { opacity: 1; }
.file-item-del:hover { color: var(--danger); background: var(--danger-dim); }
.clear-all-btn {
  width: 100%; margin-top: 6px; padding: 6px; background: none;
  border: 1px dashed var(--border); border-radius: 4px; color: var(--text-muted);
  font-size: 11px; font-family: var(--font-ui); cursor: pointer; transition: all 0.15s;
}
.clear-all-btn:hover { border-color: var(--danger); color: var(--danger); }
</style>
