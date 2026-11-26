import type {RouteLocation} from 'vue-router'
import {createRouter, type RouteRecordRaw, type RouterHistory} from 'vue-router'
import {sitzung} from '../store/sitzung'

/**
 * The tool's routes. A sheet (`/blatt/…`) hangs off its own link and reads the session without
 * switching into it. `/planung`, `/freigabe/…` and `/info` are old addresses kept as redirects, so links that
 * were already passed around still land somewhere sensible. `/` is the public start page, the alarm list
 * is `/alarme`.
 */
const routes: RouteRecordRaw[] = [
    {path: '/', name: 'Info', component: () => import('../views/InfoView.vue'), meta: {public: true}},
    {path: '/info', redirect: '/'},
    {path: '/hilfe', name: 'Hilfe', component: () => import('../views/HelpView.vue'), meta: {public: true}},
    {path: '/alarme', name: 'Alarme', component: () => import('../views/AlarmeView.vue'),
        meta: {titleKey: 'routes.alarme'}},
    {path: '/alarm/:id', name: 'Alarm', component: () => import('../views/AlarmView.vue'),
        meta: {titleKey: 'routes.alarm'}},
    {path: '/ablauf', name: 'Ablauf', component: () => import('../views/AblaufView.vue'),
        meta: {titleKey: 'routes.ablauf'}},
    {path: '/ansicht', name: 'Ansicht', component: () => import('../views/AnsichtView.vue'),
        meta: {titleKey: 'routes.ansicht'}},
    {path: '/blatt/:token/:art(person|fahrzeug)/:id', name: 'Blatt',
        component: () => import('../views/BlattView.vue'), meta: {titleKey: 'routes.blatt'}},
    {path: '/planung', redirect: '/kataloge'},
    {path: '/sitzung/:token', name: 'Sitzung', component: () => import('../views/FreigabeView.vue'),
        meta: {titleKey: 'routes.freigabe'}},
    {path: '/freigabe/:token', redirect: (ziel: RouteLocation) => `/sitzung/${ziel.params.token}`},
    {path: '/kataloge', name: 'Kataloge', component: () => import('../views/KatalogeView.vue'),
        meta: {titleKey: 'routes.kataloge'}},
    {path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFoundView.vue'),
        meta: {titleKey: 'routes.notFound'}},
]

const READ_ONLY_ROUTES = ['Ansicht', 'Ablauf', 'Sitzung', 'Blatt', 'NotFound', 'Info', 'Hilfe']

/**
 * The tool's router, with web history in the browser and memory history when prerendering.
 *
 * Whoever only watches lands in the overview instead of an editor. The fields would change nothing
 * anyway, since the server takes no change from a read token, and a form that can be filled in to
 * no effect is worse than none.
 */
export function createAppRouter(history: RouterHistory) {
    const router = createRouter({history, routes})
    router.beforeEach((target) => {
        if (!sitzung.nurLesen || READ_ONLY_ROUTES.includes(String(target.name))) return true
        return {name: 'Ansicht'}
    })
    return router
}
