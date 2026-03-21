import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiJson } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('qb_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('qb_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role || 'viewer')
  const canUpload = computed(() => role.value === 'admin' || role.value === 'editor')
  const canDelete = computed(() => role.value === 'admin' || role.value === 'editor')
  const isAdmin = computed(() => role.value === 'admin')

  async function login(username, password) {
    const data = await apiJson('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('qb_token', data.access_token)
    localStorage.setItem('qb_user', JSON.stringify(data.user))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('qb_token')
    localStorage.removeItem('qb_user')
  }

  async function changePassword(oldPassword, newPassword) {
    await apiJson('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    })
  }

  return { token, user, isLoggedIn, role, canUpload, canDelete, isAdmin, login, logout, changePassword }
})
