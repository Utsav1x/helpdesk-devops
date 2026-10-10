import {defineConfig} from 'vite';
// The development proxy mirrors nginx's same-origin production API route.
export default defineConfig({server: {proxy: {'/api': 'http://localhost:8000'}}});
