<script setup lang="ts">
import {AppFooter, AppHeader, EmberboxApp} from '@emberbox/ui'
import {useHead} from '@unhead/vue'
import {computed} from 'vue'
import {RouterLink, RouterView, useRoute} from 'vue-router'
import {t} from './i18n'
import SessionMenu from './components/session/SessionMenu.vue'
import ShareMenu from './components/session/ShareMenu.vue'
import {verbindung} from './store/sync'
import {sitzung} from './store/sitzung'
import {arbeitsmappe} from './store/arbeitsmappe'

const route = useRoute()

/** Public pages are prerendered and must not depend on the browser's session or workbook. */
const isPublic = computed(() => route.meta.public === true)

useHead({
  title: () => {
    if (isPublic.value) return undefined
    const key = route.meta.titleKey as string | undefined
    return key ? `${t(key)} | ${t('app.name')}` : t('app.name')
  },
  meta: () => isPublic.value ? [] : [{name: 'robots', content: 'noindex, nofollow'}],
})
</script>

<template>
  <EmberboxApp>
    <AppHeader :name="t('app.name')" :subtitle="t('app.untertitel')" :home="isPublic ? '/' : '/alarme'"
               logo="/favicon.svg">
      <template #nav>
        <template v-if="isPublic">
          <RouterLink to="/" class="nav-link">{{ t('nav.info') }}</RouterLink>
          <RouterLink to="/hilfe" class="nav-link">{{ t('nav.hilfe') }}</RouterLink>
        </template>
        <template v-else-if="sitzung.nurLesen">
          <RouterLink to="/ansicht" class="nav-link">{{ t('nav.ansicht') }}</RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/alarme" class="nav-link">{{ t('nav.alarme') }}</RouterLink>
          <RouterLink to="/kataloge" class="nav-link">{{ t('nav.kataloge') }}</RouterLink>
        </template>
        <RouterLink v-if="!isPublic && arbeitsmappe.planung.aktiv" to="/ablauf" class="nav-link">
          {{ t('nav.planung') }}
        </RouterLink>
      </template>

      <template #actions>
        <UButton v-if="isPublic" to="/alarme" size="sm" icon="i-lucide-arrow-right" trailing :label="t('nav.zurApp')"/>
        <template v-else>
          <SessionMenu>
            <ShareMenu/>
          </SessionMenu>
        </template>
      </template>
    </AppHeader>

    <template v-if="!isPublic">
      <div v-if="verbindung.fehler" class="mx-auto w-full max-w-[1560px] px-4 py-2 md:px-6">
        <span class="text-[13px] text-(--eb-signal-text)">{{ t('freigabe.abgleichFehler') }}</span>
      </div>
      <div v-if="sitzung.nurLesen" class="mx-auto flex w-full max-w-[1560px] flex-wrap items-center gap-3 px-4 py-2 md:px-6">
        <span class="eyebrow text-(--eb-signal-text)">{{ t('freigabe.nurLesen') }}</span>
        <span class="text-[13px] text-muted">{{ t('freigabe.nurLesenHinweis') }}</span>
      </div>
    </template>

    <main class="mx-auto w-full max-w-[1560px] grow px-4 py-6 md:px-6">
      <RouterView/>
    </main>

    <AppFooter tool="Alarmzettel" source="https://github.com/ember-tools/alarmzettel" license="AGPL-3.0"
               help="/hilfe"/>
  </EmberboxApp>
</template>

<style scoped>
.nav-link {
  color: var(--ui-text-muted);
  font-size: 15px;
  padding-bottom: 3px;
  border-bottom: 2px solid transparent;
  transition: color 0.15s;
}

.nav-link:hover {
  color: var(--ui-text-highlighted);
}

.nav-link.router-link-active {
  color: var(--ui-text-highlighted);
  font-weight: 600;
  border-bottom-color: var(--ui-signal);
}
</style>
