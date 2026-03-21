<template>
  <div class="login-page">
    <div class="card">
      <div class="logo">
        <span class="logo-duck">🦆</span>
        <span class="logo-text">Quack<em>base</em></span>
      </div>

      <div class="form-group">
        <label>用户名</label>
        <input type="text" v-model="username" class="form-input" placeholder="输入用户名" autocomplete="username" @keydown.enter="doLogin" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input type="password" v-model="password" class="form-input" placeholder="输入密码" autocomplete="current-password" @keydown.enter="doLogin" />
      </div>

      <button class="btn-login" :disabled="loading" @click="doLogin">
        {{ loading ? '登录中...' : '登 录' }}
      </button>
      <div v-if="error" class="error-msg">{{ error }}</div>

      <!-- <div class="hint">默认管理员账号<br><span>admin</span> / <span>admin123</span>（首次登录后请修改）</div> -->
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function doLogin() {
  if (!username.value || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.login-page::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(var(--border) 1px, transparent 1px),
    linear-gradient(90deg, var(--border) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.3;
  pointer-events: none;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  position: relative;
  box-shadow: 0 24px 64px rgba(0,0,0,0.5);
}
.card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 17px;
  background: linear-gradient(135deg, rgba(245,200,66,0.2), transparent 50%);
  pointer-events: none;
}
.logo { display: flex; align-items: center; gap: 12px; margin-bottom: 32px; }
.logo-duck { font-size: 32px; }
.logo-text { font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }
.logo-text em { font-style: normal; color: var(--accent); }
.form-group { margin-bottom: 18px; }
.form-group label {
  display: block; font-size: 11px; font-weight: 700;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 7px;
}
.form-input {
  width: 100%; background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text); font-family: var(--font-mono);
  font-size: 14px; padding: 11px 14px; outline: none; transition: border-color 0.15s;
}
.form-input:focus { border-color: var(--accent); }
.btn-login {
  width: 100%; background: var(--accent); color: #000; border: none;
  border-radius: 8px; font-family: var(--font-ui); font-size: 14px;
  font-weight: 700; padding: 13px; cursor: pointer; margin-top: 8px;
  transition: all 0.15s; letter-spacing: 0.02em;
}
.btn-login:hover { background: #f7d25e; transform: translateY(-1px); }
.btn-login:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.error-msg {
  background: rgba(244,85,74,0.1); border: 1px solid rgba(244,85,74,0.3);
  border-radius: 8px; color: #f4554a; font-size: 13px; padding: 10px 14px; margin-top: 14px;
}
.hint {
  margin-top: 20px; padding-top: 18px; border-top: 1px solid var(--border);
  font-size: 12px; color: var(--text-muted); font-family: var(--font-mono); line-height: 1.6;
}
.hint span { color: var(--accent); }
</style>
