import {emberbox} from '@emberbox/ui/vite'
import vue from '@vitejs/plugin-vue'
import {defineConfig} from 'vite'

const backend = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
    plugins: [
        vue(),
        emberbox({
            url: 'https://alarmzettel.emberbox.app',
            logo: 'alarmzettel',
            app: {name: 'Alarmzettel', description: 'Alarme für Einsatzübungen schreiben und Übungstage planen.', startUrl: '/alarme'},
            prerender: {entry: 'src/prerender.ts', paths: ['/', '/hilfe']},
        }),
    ],
    server: {
        proxy: {
            '/api': {target: backend, changeOrigin: true},
            '/tiles': {target: backend, changeOrigin: true},
        },
    },
})
