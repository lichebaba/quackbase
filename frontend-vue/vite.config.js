import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  return {
    base: env.VITE_BASE_PATH || '/',
    plugins: [vue()],
    css: {
      preprocessorOptions: {
        // 切到 modern-compiler 避免 dart-sass 2.0 即将移除的 legacy JS API 警告
        scss: { api: 'modern-compiler' },
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
