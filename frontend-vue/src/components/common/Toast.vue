<template>
  <Teleport to="body">
    <div class="toast-container">
      <div v-for="t in toastStore.toasts" :key="t.id" class="toast" :class="t.type">
        <span class="toast-icon">{{ icons[t.type] || 'ℹ' }}</span>
        <span class="toast-msg">{{ t.msg }}</span>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { useToastStore } from '../../stores/toast'

const toastStore = useToastStore()
const icons = { success: '✓', error: '✗', info: 'ℹ' }
</script>

<style scoped>
.toast-container {
  position: fixed; bottom: 24px; right: 24px; z-index: 200;
  display: flex; flex-direction: column; gap: 8px; align-items: flex-end;
}
.toast {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 18px; font-size: 13px;
  color: var(--text); box-shadow: var(--shadow); max-width: 320px;
  animation: toast-in 0.2s ease; display: flex; align-items: center; gap: 10px;
}
.toast.success { border-color: rgba(62,207,142,0.3); }
.toast.error { border-color: rgba(244,85,74,0.3); }
.toast .toast-icon { font-size: 16px; }
.toast .toast-msg { flex: 1; line-height: 1.4; }
@keyframes toast-in {
  from { opacity: 0; transform: translateX(16px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>
