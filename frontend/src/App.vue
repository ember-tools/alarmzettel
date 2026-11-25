<script setup lang="ts">
import {AppFooter, AppHeader, EmberboxApp} from '@emberbox/ui'
import {useHead} from '@unhead/vue'
import {computed, ref} from 'vue'
import {RouterLink, RouterView, useRoute} from 'vue-router'
import {t} from './i18n'
import {jetztAbgleichen, verbindung} from './store/sync'
import {neueSitzung, sitzung, sitzungVergessen, sitzungWechseln} from './store/sitzung'
import {arbeitsmappe} from './store/arbeitsmappe'
import {lesetoken} from './api/sitzung'
import {personenplan} from './scripts/ablauf'
import {plandaten} from './store/planung'

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

const wechsler = ref(false)
const arbeitet = ref(false)
const teiler = ref(false)
const nurLesenToken = ref<string | null>(null)
const kopiert = ref<string | null>(null)

/** Ein Link auf diese Sitzung, so wie dieser Browser sie erreicht. */
function linkAuf(token: string | null): string {
  return token ? `${window.location.origin}/sitzung/${token}` : ''
}

/**
 * Teilen heißt hier: den Link weitergeben. Vorher wird abgeglichen, damit der andere den Stand
 * sieht, den alle haben. Der Lesen-Link entsteht beim ersten Öffnen dieses Menüs und bleibt
 * danach derselbe — wer eine Sitzung nur ansieht, kann keinen erzeugen und braucht auch keinen.
 */
async function teilen() {
  teiler.value = !teiler.value
  kopiert.value = null
  if (!teiler.value || !sitzung.token || sitzung.nurLesen) return
  await jetztAbgleichen()
  try {
    nurLesenToken.value = await lesetoken(sitzung.token)
  } catch {
    nurLesenToken.value = null
  }
}

/**
 * Ein Link je Zettel: wer ihn bekommt, sieht seinen Tag und sonst nichts. Aufgeführt wird, wer
 * auch ein Blatt bekäme — jede Person mit einem Plan und jedes Fahrzeug mit einer Kette.
 */
const blaetter = computed(() => {
  const token = nurLesenToken.value ?? (sitzung.nurLesen ? sitzung.token : null)
  if (!token || !arbeitsmappe.planung.aktiv) return []
  const daten = plandaten()
  const zeilen: {name: string, link: string}[] = []
  for (const person of arbeitsmappe.kataloge.personen) {
    if (person.blatt === false || !personenplan(daten, person.id).length) continue
    zeilen.push({name: person.name || t('ablauf.ohneName'),
                 link: `${window.location.origin}/blatt/${token}/person/${person.id}`})
  }
  for (const fahrzeug of arbeitsmappe.kataloge.fahrzeuge) {
    const kette = arbeitsmappe.planung.laeufe.find(lauf => lauf.fahrzeugId === fahrzeug.id)
    if (!kette?.schritte.length) continue
    zeilen.push({name: fahrzeug.funkrufname || t('ablauf.ohneName'),
                 link: `${window.location.origin}/blatt/${token}/fahrzeug/${fahrzeug.id}`})
  }
  return zeilen
})

const blattliste = computed(() =>
    blaetter.value.map(blatt => `${blatt.name} — ${blatt.link}`).join('\n'))

async function kopieren(link: string) {
  try {
    await navigator.clipboard.writeText(link)
    kopiert.value = link
  } catch { /* ein Browser ohne Zwischenablage zeigt den Link zum Markieren */ }
}

/** Der Tag, an dem diese Sitzung verschwindet, wenn sie niemand öffnet. */
function laeuftAb(): string {
  return sitzung.laeuftAb ? new Date(sitzung.laeuftAb).toLocaleDateString('de-DE') : ''
}

async function tun(was: () => Promise<void>) {
  arbeitet.value = true
  try {
    await was()
    wechsler.value = false
  } finally {
    arbeitet.value = false
  }
}
</script>

<template>
  <EmberboxApp>
    <AppHeader :name="t('app.name')" :subtitle="t('app.untertitel')" :home="isPublic ? '/info' : '/'"
               logo="/favicon.svg">
      <template #nav>
        <template v-if="isPublic">
          <RouterLink to="/info" class="nav-link">{{ t('nav.info') }}</RouterLink>
          <RouterLink to="/hilfe" class="nav-link">{{ t('nav.hilfe') }}</RouterLink>
        </template>
        <template v-else-if="sitzung.nurLesen">
          <RouterLink to="/ansicht" class="nav-link">{{ t('nav.ansicht') }}</RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/" class="nav-link">{{ t('nav.alarme') }}</RouterLink>
          <RouterLink to="/kataloge" class="nav-link">{{ t('nav.kataloge') }}</RouterLink>
        </template>
        <RouterLink v-if="!isPublic && arbeitsmappe.planung.aktiv" to="/ablauf" class="nav-link">
          {{ t('nav.planung') }}
        </RouterLink>
      </template>

      <template #actions>
        <UButton v-if="isPublic" to="/" size="sm" icon="i-lucide-arrow-right" trailing :label="t('nav.zurApp')"/>
        <template v-else>
          <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-plus" :loading="arbeitet"
                   :title="t('sitzung.neuTitel')" @click="tun(neueSitzung)">
            <span class="hidden md:inline">{{ t('sitzung.neu') }}</span>
          </UButton>

          <UPopover :open="teiler" @update:open="(isOpen: boolean) => isOpen ? teilen() : (teiler = false)">
            <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-share-2" :title="t('freigabe.teilenTitel')">
              <span class="hidden md:inline">{{ t('freigabe.teilen') }}</span>
            </UButton>
            <template #content>
              <div class="grid w-[min(24rem,90vw)] gap-3 p-3">
                <UFormField v-if="!sitzung.nurLesen" :label="t('freigabe.zumMitarbeiten')">
                  <UFieldGroup class="w-full">
                    <UInput class="w-full" size="sm" readonly :model-value="linkAuf(sitzung.token)"
                            @focus="($event.target as HTMLInputElement).select()"/>
                    <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-copy"
                             :aria-label="t('freigabe.kopieren')" @click="kopieren(linkAuf(sitzung.token))"/>
                  </UFieldGroup>
                </UFormField>

                <UFormField :label="t('freigabe.zumAnsehen')" :help="t('freigabe.zumAnsehenHinweis')">
                  <UFieldGroup class="w-full">
                    <UInput class="w-full" size="sm" readonly
                            :model-value="sitzung.nurLesen ? linkAuf(sitzung.token) : (nurLesenToken ? linkAuf(nurLesenToken) : '…')"
                            @focus="($event.target as HTMLInputElement).select()"/>
                    <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-copy"
                             :aria-label="t('freigabe.kopieren')" :disabled="!sitzung.nurLesen && !nurLesenToken"
                             @click="kopieren(linkAuf(sitzung.nurLesen ? sitzung.token : nurLesenToken))"/>
                  </UFieldGroup>
                </UFormField>

                <div v-if="blaetter.length" class="border-t border-default pt-3">
                  <UFormField :label="t('blatt.titel')" :help="t('blatt.hinweisLinks')">
                    <UTextarea class="tabular w-full" size="sm" :rows="4" readonly :model-value="blattliste"
                               @focus="($event.target as HTMLTextAreaElement).select()"/>
                  </UFormField>
                  <UButton class="mt-2" size="sm" color="neutral" variant="outline" icon="i-lucide-copy"
                           :label="t('blatt.kopieren')" @click="kopieren(blattliste)"/>
                </div>

                <p v-if="kopiert" class="m-0 text-[12px]">{{ t('freigabe.kopiert') }}</p>
              </div>
            </template>
          </UPopover>

          <UPopover v-model:open="wechsler">
            <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-refresh-cw">
              <span class="hidden md:inline">{{ t('sitzung.wechseln') }}</span>
            </UButton>
            <template #content>
              <ul class="m-0 grid w-[min(22rem,90vw)] list-none gap-0.5 p-1" role="listbox">
                <li v-if="!sitzung.bekannt.length" class="px-2 py-1.5 text-sm text-muted">{{ t('sitzung.keine') }}</li>
                <li v-for="eintrag in sitzung.bekannt" :key="eintrag.token" role="option"
                    :aria-selected="eintrag.token === sitzung.token"
                    class="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-elevated"
                    :class="eintrag.token === sitzung.token ? 'font-semibold' : ''">
                  <button type="button" class="grow cursor-pointer text-left" @click="tun(() => sitzungWechseln(eintrag.token))">
                    {{ eintrag.beschriftung }}
                  </button>
                  <UButton size="xs" color="neutral" variant="ghost" icon="i-lucide-x" :aria-label="t('sitzung.entfernen')"
                           @click.stop="sitzungVergessen(eintrag.token)"/>
                </li>
                <li v-if="sitzung.laeuftAb" class="px-2 py-1.5 text-[12px] text-muted">
                  {{ t('sitzung.laeuftAb', {datum: laeuftAb()}) }}
                </li>
              </ul>
            </template>
          </UPopover>
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

    <AppFooter tool="Alarmplaner" source="https://github.com/ember-tools/alarmzettel" license="AGPL-3.0"
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
