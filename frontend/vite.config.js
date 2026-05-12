import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const API_CANDIDATES = [
  'http://localhost:8000',
  'http://localhost:8001',
]

async function resolveApiTarget(mode) {
  const env = loadEnv(mode, process.cwd(), '')

  if (env.VITE_API_TARGET) {
    return env.VITE_API_TARGET
  }

  for (const candidate of API_CANDIDATES) {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 1000)
      const response = await fetch(`${candidate}/health`, {
        signal: controller.signal,
      })
      clearTimeout(timeout)

      if (response.ok) {
        return candidate
      }
    } catch {
      // Try the next candidate port.
    }
  }

  return API_CANDIDATES[0]
}

export default defineConfig(async ({ mode }) => {
  const apiTarget = await resolveApiTarget(mode)

  console.log(`[vite] proxying /api to ${apiTarget}`)

  return {
    plugins: [vue()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
