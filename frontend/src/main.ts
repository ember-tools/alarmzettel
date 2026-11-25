import {createToolApp, emberboxUi} from '@emberbox/ui'
import {createWebHistory} from 'vue-router'
import App from './App.vue'
import {i18n} from './i18n'
import {createAppRouter} from './router'
import {sitzungStarten} from './store/sitzung'
import './style.css'

void sitzungStarten()

const router = createAppRouter(createWebHistory())
const app = createToolApp(App).use(router).use(i18n).use(emberboxUi)
void router.isReady().then(() => app.mount('#app'))
