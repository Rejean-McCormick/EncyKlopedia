import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
export default defineConfig({
  integrations: [svelte()],
  build: { inlineStylesheets: 'never' },
  vite: { server: { proxy: { '/api': { target: 'http://127.0.0.1:4322', changeOrigin: false } } } },
});
