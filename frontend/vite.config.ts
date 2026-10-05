import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '../', '')
  return {
    plugins: [react()],
    define: {
      '__DEV_API_KEY__': JSON.stringify(mode === 'development' ? env.API_KEY : '')
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8088',
          changeOrigin: true,
        }
      }
    },
    resolve: {
      alias: [
        // Mock Next.js navigation imports that nextstepjs might try to access
        {
          find: 'next/navigation',
          replacement: path.join(process.cwd(), 'src/mocks/next-navigation.ts'),
        },
      ]
    },
    ssr: {
      noExternal: ['nextstepjs', 'motion']
    },
    build: {
      chunkSizeWarningLimit: 1500
    }
  }
})
