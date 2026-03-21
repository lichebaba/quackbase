<template>
  <ModalBase :show="show" title="👥 用户管理" wide @close="show = false">
    <div class="user-mgmt-toolbar">
      <button class="btn btn-primary" @click="showNewForm = true">+ 新建用户</button>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>
    <table v-else class="user-table">
      <thead>
        <tr><th>用户名</th><th>角色</th><th>创建时间</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td style="font-weight:600">{{ u.username }}</td>
          <td>
            <span v-if="u.id === auth.user?.id" class="role-badge" :class="u.role">{{ u.role }}</span>
            <select v-else class="role-select" :value="u.role" @change="changeRole(u.id, $event.target.value)">
              <option value="viewer">viewer</option>
              <option value="editor">editor</option>
              <option value="admin">admin</option>
            </select>
          </td>
          <td>{{ u.created_at ? u.created_at.slice(0, 16) : '—' }}</td>
          <td>
            <button v-if="u.id !== auth.user?.id" class="btn-del-user" @click="deleteUser(u)">删除</button>
            <span v-else style="color:var(--text-muted);font-size:11px">（当前用户）</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- New user form -->
    <div v-if="showNewForm" class="new-user-form">
      <div style="font-size:13px;font-weight:700;color:var(--text-sub);margin-bottom:12px;">新建用户</div>
      <div class="form-row-inline">
        <input type="text" v-model="newUsername" class="form-input" placeholder="用户名" style="flex:1" />
        <input type="password" v-model="newPassword" class="form-input" placeholder="密码" style="flex:1" />
        <select v-model="newRole" class="form-select" style="width:120px">
          <option value="viewer">viewer</option>
          <option value="editor" selected>editor</option>
          <option value="admin">admin</option>
        </select>
        <button class="btn btn-primary" @click="createUser">创建</button>
        <button class="btn btn-ghost" @click="showNewForm = false">取消</button>
      </div>
    </div>
  </ModalBase>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { apiJson, api } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { useToastStore } from '../../stores/toast'
import ModalBase from '../common/ModalBase.vue'

const auth = useAuthStore()
const toast = useToastStore()

const show = ref(false)
const loading = ref(false)
const users = ref([])
const showNewForm = ref(false)
const newUsername = ref('')
const newPassword = ref('')
const newRole = ref('editor')

async function loadUsers() {
  loading.value = true
  try {
    const data = await apiJson('/api/admin/users')
    users.value = data?.users || []
  } catch (e) {
    toast.add(e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function changeRole(userId, role) {
  try {
    await api(`/api/admin/users/${userId}/role`, {
      method: 'PATCH', body: JSON.stringify({ role }),
    })
    toast.add('角色已更新', 'success')
  } catch (e) { toast.add(e.message, 'error'); await loadUsers() }
}

async function deleteUser(u) {
  if (!confirm(`确认删除用户 "${u.username}"？其数据将一并删除。`)) return
  try {
    await api(`/api/admin/users/${u.id}`, { method: 'DELETE' })
    toast.add('用户已删除', 'success')
    await loadUsers()
  } catch (e) { toast.add(e.message, 'error') }
}

async function createUser() {
  if (!newUsername.value || !newPassword.value) { toast.add('请填写用户名和密码', 'error'); return }
  if (newPassword.value.length < 6) { toast.add('密码至少 6 位', 'error'); return }
  try {
    await api('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username: newUsername.value, password: newPassword.value, role: newRole.value }),
    })
    newUsername.value = ''; newPassword.value = ''
    showNewForm.value = false
    toast.add(`用户 "${newUsername.value || '新用户'}" 已创建`, 'success')
    await loadUsers()
  } catch (e) { toast.add(e.message, 'error') }
}

function onOpen() { show.value = true; showNewForm.value = false; loadUsers() }
onMounted(() => window.addEventListener('open-user-mgmt', onOpen))
onUnmounted(() => window.removeEventListener('open-user-mgmt', onOpen))
</script>

<style scoped>
.user-mgmt-toolbar { margin-bottom: 14px; }
.user-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.user-table th {
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--text-muted); padding: 8px 12px;
  border-bottom: 1px solid var(--border); text-align: left;
}
.user-table td {
  padding: 10px 12px; border-bottom: 1px solid var(--border);
  color: var(--text); font-family: var(--font-mono); font-size: 12px;
}
.user-table tr:last-child td { border-bottom: none; }
.role-select {
  font-family: var(--font-mono); font-size: 11px; background: var(--surface-3);
  border: 1px solid var(--border); color: var(--text); padding: 3px 8px;
  border-radius: 6px; cursor: pointer;
}
.role-select:focus { outline: none; border-color: var(--accent); }
.btn-del-user {
  background: none; border: 1px solid var(--border); color: var(--text-muted);
  border-radius: 6px; padding: 3px 10px; font-size: 12px; cursor: pointer;
  font-family: var(--font-ui); transition: all 0.15s;
}
.btn-del-user:hover { border-color: var(--danger); color: var(--danger); background: var(--danger-dim); }
.new-user-form { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border); }
</style>
