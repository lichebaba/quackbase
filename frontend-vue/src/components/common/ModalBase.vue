<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal" :class="{ 'modal-wide': wide }">
        <div class="modal-header">
          <span class="modal-title">{{ title }}</span>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="modal-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { watch, onUnmounted } from 'vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: '' },
  wide: Boolean,
})

defineEmits(['close'])

function onEsc(e) {
  if (e.key === 'Escape' && props.show) {
    // emit close handled by parent
  }
}
watch(() => props.show, (v) => {
  if (v) document.addEventListener('keydown', onEsc)
  else document.removeEventListener('keydown', onEsc)
})
onUnmounted(() => document.removeEventListener('keydown', onEsc))
</script>
