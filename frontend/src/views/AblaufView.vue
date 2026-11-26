<script setup lang="ts">
import {CollapsibleSection} from '@emberbox/ui'
import {computed, defineAsyncComponent, ref, watch} from 'vue'
import LagenAnsicht from '../components/planung/LagenAnsicht.vue'
import LaufKette from '../components/planung/LaufKette.vue'
import TagesPlan from '../components/planung/TagesPlan.vue'
import OrtsSicht from '../components/planung/OrtsSicht.vue'
import PersonenPlan from '../components/planung/PersonenPlan.vue'
import {t} from '../i18n'
import {fehlertext, renderAblaufplan, renderAblaufplanZip, renderAlle} from '../api/render'
import {arbeitsmappe} from '../store/arbeitsmappe'
import {alleOrte, entfernen, laufAnlegen, laufVon, personName, punkteLaden} from '../store/planung'
import {jetztAbgleichen} from '../store/sync'
import {sitzung} from '../store/sitzung'

watch(() => alleOrte().map(ort => Object.values(ort.adresse).join()).join('|'),
    () => punkteLaden(), {immediate: true})

/** Ein Fahrzeug oder eine Person bekommt eine Kette, sobald es eingeplant wird. */
function einplanen(fuer: {fahrzeugId?: string, personId?: string}) {
  if (!laufVon(fuer)) laufAnlegen(fuer)
}

function beschriftung(lauf: {fahrzeugId: string, personId: string}): string {
  if (lauf.fahrzeugId) {
    return arbeitsmappe.kataloge.fahrzeuge.find(v => v.id === lauf.fahrzeugId)?.funkrufname
        || t('ablauf.ohneName')
  }
  return personName(lauf.personId) || t('ablauf.ohneName')
}

function offen(fuer: {fahrzeugId?: string, personId?: string}): boolean {
  return !laufVon(fuer)
}

/** Geplant wird in den Ketten; die drei anderen Ansichten sind dieselben Daten von anderer Seite. */
/**
 * Bild und Karte bringen ihre Zeichenbibliotheken mit und werden deshalb erst geladen, wenn
 * jemand sie auch aufschlägt – der Rest der Seite soll davon nichts merken.
 */
const BewegungsBild = defineAsyncComponent(
    () => import('../components/planung/BewegungsBild.vue'))
const LageKarte = defineAsyncComponent(() => import('../components/planung/LageKarte.vue'))

const ANSICHTEN = ['tag', 'ketten', 'bewegung', 'karte', 'personen', 'orte', 'lagen'] as const
type Ansicht = typeof ANSICHTEN[number]

const SPEICHER = 'alarmplaner_ablaufansicht'

/**
 * Dieselben Daten von sieben Seiten; keine ist die richtige. Womit jemand arbeitet, merkt sich
 * der Browser – es gehört zu ihm und nicht zur Arbeitsmappe, so wie das Farbthema.
 */
function gemerkteAnsicht(): Ansicht {
  const gemerkt = localStorage.getItem(SPEICHER) as Ansicht | null
  return gemerkt && ANSICHTEN.includes(gemerkt) ? gemerkt : 'tag'
}

const ansicht = ref<Ansicht>(gemerkteAnsicht())

/** Wer nur zusieht, bekommt die Ketten nicht – dort wird gearbeitet, nicht gelesen. */
const reiter = computed<readonly Ansicht[]>(() =>
    sitzung.nurLesen ? ANSICHTEN.filter(name => name !== 'ketten') : ANSICHTEN)

watch(reiter, liste => {
  if (!liste.includes(ansicht.value)) ansicht.value = liste[0] ?? 'tag'
}, {immediate: true})

watch(ansicht, gewaehlt => {
  try {
    localStorage.setItem(SPEICHER, gewaehlt)
  } catch { /* ein Browser ohne Speicher fängt eben jedes Mal beim Tagesplan an */ }
})
const fehler = ref<string | null>(null)

/**
 * Vor dem Drucken abgleichen, damit die Blätter den Stand tragen, den alle haben, und nicht den,
 * den dieser Browser vor ein paar Sekunden gesehen hat.
 */
async function drucken(holen: () => Promise<Blob>, name: string) {
  fehler.value = null
  try {
    await jetztAbgleichen()
    const url = URL.createObjectURL(await holen())
    const link = document.createElement('a')
    link.href = url
    link.download = name
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    fehler.value = await fehlertext(error)
  }
}
</script>

<template>
  <div class="grid gap-5">
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div class="min-w-0">
        <h1 class="headline text-2xl">{{ t('ablauf.titel') }}</h1>
        <p class="text-muted text-sm mt-1">{{ t('ablauf.beschreibung') }}</p>
      </div>
      <div class="flex gap-2 flex-wrap">
        <UButton size="sm" color="neutral" variant="outline"
                 @click="drucken(renderAblaufplan, 'ablaufplan.pdf')">
          <UIcon name="i-lucide-file-text"/>
          {{ t('ablauf.drucken') }}
        </UButton>
        <UButton size="sm" color="neutral" variant="outline" :title="t('ablauf.archivHinweis')"
                 @click="drucken(renderAblaufplanZip, 'ablaufplan.zip')">
          <UIcon name="i-lucide-file-archive"/>
          {{ t('ablauf.archiv') }}
        </UButton>
        <UButton size="sm" color="neutral" variant="outline" :title="t('ablauf.zettelHinweis')"
                 :disabled="!arbeitsmappe.alarme.length"
                 @click="drucken(renderAlle, 'alarmzettel.pdf')">
          <UIcon name="i-lucide-file-text"/>
          {{ t('ablauf.zettel') }}
        </UButton>
        <UButton size="sm" color="neutral" variant="outline" to="/kataloge">{{ t('ablauf.stammdaten') }}</UButton>
      </div>
    </div>

    <p v-if="fehler" class="text-(--eb-signal-text) text-sm">{{ fehler }}</p>

    <div class="flex flex-wrap gap-2">
      <UButton size="sm" v-for="name in reiter" :key="name"
               :color="ansicht === name ? 'primary' : 'neutral'" :variant="ansicht === name ? 'solid' : 'outline'" @click="ansicht = name">
        {{ t(`ablauf.ansicht.${name}`) }}
      </UButton>
    </div>

    <TagesPlan v-if="ansicht === 'tag'"/>
    <BewegungsBild v-else-if="ansicht === 'bewegung'"/>
    <LageKarte v-else-if="ansicht === 'karte'"/>
    <PersonenPlan v-else-if="ansicht === 'personen'"/>
    <OrtsSicht v-else-if="ansicht === 'orte'"/>
    <LagenAnsicht v-else-if="ansicht === 'lagen'"/>

    <template v-else>
    <section v-if="alleOrte().length < 2" class="panel">
      <p class="text-muted text-sm">{{ t('ablauf.ersteOrte') }}</p>
    </section>

    <section class="panel">
      <h2 class="section-title">{{ t('ablauf.einplanen') }}</h2>
      <div class="flex flex-wrap gap-2">
        <UButton size="sm" color="neutral" variant="outline" v-for="fahrzeug in arbeitsmappe.kataloge.fahrzeuge.filter(v => offen({fahrzeugId: v.id}))"
                :key="fahrzeug.id"
                @click="einplanen({fahrzeugId: fahrzeug.id})">
          <UIcon name="i-lucide-plus"/>
          {{ fahrzeug.funkrufname || t('ablauf.ohneName') }}
        </UButton>
        <UButton size="sm" color="neutral" variant="outline" v-for="person in arbeitsmappe.kataloge.personen.filter(p => offen({personId: p.id}))"
                :key="person.id"
                @click="einplanen({personId: person.id})">
          <UIcon name="i-lucide-plus"/>
          {{ person.name || t('ablauf.ohneName') }}
        </UButton>
      </div>
      <p class="text-muted text-[13px] mt-2">{{ t('ablauf.einplanenHinweis') }}</p>
    </section>

    <p v-if="!arbeitsmappe.planung.laeufe.length" class="text-muted text-sm">
      {{ t('ablauf.keineKetten') }}
    </p>

    <CollapsibleSection storage-key="alarmplaner_kataloge" v-for="lauf in arbeitsmappe.planung.laeufe" :key="lauf.id"
                    :name="`kette-${lauf.id}`" :title="beschriftung(lauf)"
                    :icon="lauf.fahrzeugId ? 'i-lucide-table' : 'i-lucide-users'"
                    :count="lauf.schritte.length" default-open>
      <template #actions>
        <UButton size="sm" color="signal" variant="outline"
                 @click="entfernen(arbeitsmappe.planung.laeufe, lauf)">
          <UIcon name="i-lucide-trash-2"/>
          {{ t('ablauf.ketteEntfernen') }}
        </UButton>
      </template>
      <LaufKette :lauf="lauf"/>
    </CollapsibleSection>
    </template>
  </div>
</template>
