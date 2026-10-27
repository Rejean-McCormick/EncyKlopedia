import {defineConfig} from 'vitest/config';
import {svelte} from '@sveltejs/vite-plugin-svelte';
export default defineConfig({plugins:[svelte()],resolve:{conditions:['browser']},test:{environment:'jsdom',include:['tests/ui/**/*.test.mjs'],testTimeout:15000,hookTimeout:15000}});
