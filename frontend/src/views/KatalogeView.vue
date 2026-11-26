<script setup lang="ts">
import {CollapsibleSection, TextField} from '@emberbox/ui'
import {computed, reactive, ref, useId, watch} from 'vue'
import AddressField from '../components/base/AddressField.vue'
import {t} from '../i18n'
import {arbeitsmappe} from '../store/arbeitsmappe'
import {
  entfernen as ausListe, ortAnlegen, personAnlegen, tagAnlegen, umschalten,
  verfuegbarkeitAnlegen, wortHinzufuegen,
} from '../store/planung'
import {truppText} from '../scripts/staerke'
import {STICHWOERTER} from '../interfaces/Alarm'
import type {
  Fahrzeugvorlage, Kataloge, Materialvorlage, Stichwortvorlage,
} from '../interfaces/Alarm'
import type {Ort} from '../interfaces/Planung'

/** The prefix of this instance's field ids, so labels find their fields when it appears more than once. */
const fieldId = useId()

type Wortliste = Extract<keyof Kataloge, 'status' | 'trupp' | 'rollen' | 'fahrerlaubnisse'>

const listen: { schluessel: Wortliste, titel: string }[] = [
  {schluessel: 'status', titel: t('kataloge.status')},
  {schluessel: 'trupp', titel: t('kataloge.trupp')},
  {schluessel: 'rollen', titel: t('planung.rollen')},
  {schluessel: 'fahrerlaubnisse', titel: t('planung.fahrerlaubnisse')},
]

/**
 * A display order that stands still while someone is typing in the section.
 *
 * The catalogues are sorted by name. Sorting on every keystroke would move the row under the
 * cursor and send the next letter into a different field, so the list is re-sorted only when the
 * section loses focus, and when an entry is added or removed. What is watched is *which* entries
 * exist, as a sorted set of ids, not their order: an exchange rebuilds the workbook and may lay it
 * out the other way round, and if sorting depended on that, the row under the cursor would jump
 * away mid-word. The result is `reactive` so the template reads `liste` without `.value`, which
 * Vue does not unwrap in a plain object.
 */
function geordnet<T extends { id: string }>(quelle: () => T[], lesen: (eintrag: T) => string) {
  const reihenfolge = ref<string[]>([])

  function ordnen() {
    reihenfolge.value = [...quelle()]
        .sort((a, b) => lesen(a).localeCompare(lesen(b), 'de') || a.id.localeCompare(b.id))
        .map(eintrag => eintrag.id)
  }

  /** Was neu ist, hängt hinten an, bis neu geordnet wird – dort sieht man es auch. */
  const liste = computed(() => {
    const nachId = new Map(quelle().map(eintrag => [eintrag.id, eintrag]))
    const bekannt = reihenfolge.value
        .map(id => nachId.get(id))
        .filter((eintrag): eintrag is T => Boolean(eintrag))
    const gesehen = new Set(bekannt.map(eintrag => eintrag.id))
    return [...bekannt, ...quelle().filter(eintrag => !gesehen.has(eintrag.id))]
  })

  watch(() => [...quelle().map(eintrag => eintrag.id)].sort().join(), ordnen, {immediate: true})
  return reactive({liste, ordnen})
}

/** Erst wenn der Fokus den Abschnitt ganz verlässt, nicht schon beim Sprung ins nächste Feld. */
function verlassen(ereignis: FocusEvent, ordnen: () => void) {
  const ziel = ereignis.relatedTarget
  if (!(ziel instanceof Node) || !(ereignis.currentTarget as Node).contains(ziel)) ordnen()
}

const fahrzeuge = geordnet(() => arbeitsmappe.kataloge.fahrzeuge, eintrag => eintrag.funkrufname)
const stichwoerter = geordnet(() => arbeitsmappe.kataloge.stichwoerter, eintrag => eintrag.text)
const materialliste = geordnet(() => arbeitsmappe.kataloge.material, eintrag => eintrag.name)

const stichwort = ref('')

/**
 * Was die Wache üblicherweise führt und in diesem Katalog noch fehlt. Wer eine Liste geleert
 * oder aus einer Tabelle geladen hat, muss die Standardstichwörter nicht abtippen.
 */
const stichwortvorschlaege = computed(() => {
  const vorhanden = new Set(arbeitsmappe.kataloge.stichwoerter.map(e => e.text.trim()))
  return STICHWOERTER.filter(text => !vorhanden.has(text))
})
const materialname = ref('')

function materialHinzufuegen() {
  const name = materialname.value.trim()
  if (!name || arbeitsmappe.kataloge.material.some(stueck => stueck.name === name)) return
  arbeitsmappe.kataloge.material.push({id: crypto.randomUUID(), name, bestand: 0})
  materialname.value = ''
}

function materialEntfernen(stueck: Materialvorlage) {
  const stelle = arbeitsmappe.kataloge.material.indexOf(stueck)
  if (stelle >= 0) arbeitsmappe.kataloge.material.splice(stelle, 1)
}

/**
 * Ein Wort an einer Person: was der Katalog noch nicht kennt, kommt dort dazu – so wie ein neu
 * geschriebenes Stichwort oder ein neues Materialstück. Die Knöpfe daneben bleiben der schnelle
 * Weg für alles, was schon geführt wird.
 */
function wortGeben(liste: 'rollen' | 'fahrerlaubnisse', an: string[], feld: HTMLInputElement) {
  const wert = feld.value.trim()
  feld.value = ''
  if (!wert) return
  wortHinzufuegen(arbeitsmappe.kataloge[liste], wert)
  if (!an.includes(wert)) an.push(wert)
}

function ortEntfernen(ort: Ort) {
  const stelle = arbeitsmappe.kataloge.orte.indexOf(ort)
  if (stelle >= 0) arbeitsmappe.kataloge.orte.splice(stelle, 1)
}

function stichwortHinzufuegen() {
  const text = stichwort.value.trim()
  if (!text || arbeitsmappe.kataloge.stichwoerter.some(e => e.text === text)) return
  arbeitsmappe.kataloge.stichwoerter.push({id: crypto.randomUUID(), text})
  stichwort.value = ''
}

/**
 * Removing a Stichwort leaves the Alarme that pointed at it holding the text they last printed,
 * so a sheet already written does not go blank because the catalogue was tidied up.
 */
/** Ein Vorschlag mit einem Klick: das Standardstichwort steht danach im Katalog. */
function stichwortUebernehmen(text: string) {
  arbeitsmappe.kataloge.stichwoerter.push({id: crypto.randomUUID(), text})
}

function stichwortEntfernen(index: number) {
  const eintrag = arbeitsmappe.kataloge.stichwoerter[index]
  if (!eintrag) return
  for (const alarm of arbeitsmappe.alarme) {
    if (alarm.stichwortId !== eintrag.id) continue
    alarm.stichwort = eintrag.text
    alarm.stichwortId = ''
  }
  arbeitsmappe.kataloge.stichwoerter.splice(index, 1)
}

const entwurf = ref<Record<string, string>>({})

function hinzufuegen(schluessel: Wortliste) {
  const wert = (entwurf.value[schluessel] ?? '').trim()
  if (!wert || arbeitsmappe.kataloge[schluessel].includes(wert)) return
  arbeitsmappe.kataloge[schluessel].push(wert)
  entwurf.value[schluessel] = ''
}

function entfernen(schluessel: Wortliste, index: number) {
  arbeitsmappe.kataloge[schluessel].splice(index, 1)
}

function fahrzeugHinzufuegen() {
  arbeitsmappe.kataloge.fahrzeuge.push({
    id: crypto.randomUUID(), funkrufname: '',
    staerke: '', ezp: '', status: '', plaetze: '', fuehrerschein: '',
  })
}

/** As with a Stichwort: what the vehicle rows last printed stays on them. */
function fahrzeugEntfernen(index: number) {
  const vorlage = arbeitsmappe.kataloge.fahrzeuge[index]
  if (!vorlage) return
  for (const alarm of arbeitsmappe.alarme) {
    for (const gruppe of alarm.einsatzmittel) {
      for (const fahrzeug of gruppe.fahrzeuge) {
        if (fahrzeug.vorlageId !== vorlage.id) continue
        fahrzeug.funkrufname = vorlage.funkrufname
        fahrzeug.vorlageId = ''
      }
    }
  }
  arbeitsmappe.kataloge.fahrzeuge.splice(index, 1)
}

/**
 * Renaming an entry reaches every Alarm pointing at it – which is the whole reason the catalogue
 * has ids. An Alarm that merely happens to read the same, because someone typed the word rather
 * than picking it, is left alone: it was never linked to this entry.
 */
function stichwortUmbenannt(eintrag: Stichwortvorlage) {
  for (const alarm of arbeitsmappe.alarme) {
    if (alarm.stichwortId === eintrag.id) alarm.stichwort = eintrag.text
  }
}

function fahrzeugUmbenannt(vorlage: Fahrzeugvorlage) {
  for (const alarm of arbeitsmappe.alarme) {
    for (const gruppe of alarm.einsatzmittel) {
      for (const fahrzeug of gruppe.fahrzeuge) {
        if (fahrzeug.vorlageId === vorlage.id) fahrzeug.funkrufname = vorlage.funkrufname
      }
    }
  }
}

/** Shows what the strength will print as, so a wrong number is visible before it is used. */
function truppVorschau(staerke: string): string {
  const zahl = Number(staerke)
  return Number.isFinite(zahl) && zahl > 0 ? truppText(zahl) : ''
}
</script>

<template>
  <div class="grid gap-5">
    <datalist id="rollenliste">
      <option v-for="wert in arbeitsmappe.kataloge.rollen" :key="wert" :value="wert"/>
    </datalist>
    <datalist id="klassenliste">
      <option v-for="wert in arbeitsmappe.kataloge.fahrerlaubnisse" :key="wert" :value="wert"/>
    </datalist>
    <datalist id="stichwortliste">
      <option v-for="text in stichwortvorschlaege" :key="text" :value="text"/>
    </datalist>
    <div>
      <h1 class="headline text-2xl">{{ t('kataloge.titel') }}</h1>
      <p class="text-muted text-sm mt-1">{{ t('kataloge.beschreibung') }}</p>
    </div>

    <section class="panel">
      <h2 class="section-title">{{ t('planung.titel') }}</h2>
      <label class="flex items-center gap-3 cursor-pointer">
        <input v-model="arbeitsmappe.planung.aktiv" type="checkbox" class="h-4 w-4"/>
        <span class="text-sm">{{ t('planung.einschalten') }}</span>
      </label>
      <p class="text-muted text-[13px] mt-2">{{ t('planung.einschaltenHinweis') }}</p>
    </section>

    <CollapsibleSection storage-key="alarmplaner_kataloge" name="dienststelle" :title="t('kataloge.dienststelle')">
      <div class="grid md:grid-cols-3 gap-3">
        <TextField v-model="arbeitsmappe.kataloge.arbeitsgruppe" :label="t('feld.arbeitsgruppe')"/>
        <TextField v-model="arbeitsmappe.kataloge.wacheName" :label="t('kataloge.wacheName')"
                  :placeholder="t('kataloge.wachePlatzhalter')"/>
        <div>
          <label class="field-label" :for="`${fieldId}-calls-per-day`">{{ t('kataloge.alarmeProTag') }}</label>
          <UInput :id="`${fieldId}-calls-per-day`" v-model.number="arbeitsmappe.kataloge.alarmeProTag" type="number" min="0"
                  step="100" class="w-full" :ui="{base: 'tabular'}"/>
        </div>
      </div>
      <p class="text-muted text-[13px] mt-3 mb-4">{{ t('kataloge.arbeitsgruppeHinweis') }}</p>
      <p class="text-muted text-[13px] mb-4">{{ t('kataloge.alarmeProTagHinweis') }}</p>

      <AddressField v-model="arbeitsmappe.kataloge.wache" :title="t('kataloge.wache')"/>
      <p class="text-muted text-[13px] mt-3">{{ t('kataloge.wacheHinweis') }}</p>
    </CollapsibleSection>

    <CollapsibleSection storage-key="alarmplaner_kataloge" name="orte" :title="t('kataloge.orte')"
                    :count="arbeitsmappe.kataloge.orte.length + 1">
      <template #actions>
        <UButton size="sm" color="neutral" variant="outline" @click="ortAnlegen">
          <UIcon name="i-lucide-plus"/>
          {{ t('kataloge.ortNeu') }}
        </UButton>
      </template>
      <p class="text-muted text-[13px] mb-3">{{ t('kataloge.orteHinweis') }}</p>

      <div class="grid gap-4">
        <div class="border border-default rounded p-3 bg-muted">
          <span class="eyebrow">{{ arbeitsmappe.kataloge.wacheName || t('kataloge.dienststelle') }}</span>
          <p class="text-muted text-[13px] mt-1">{{ t('kataloge.dienststelleOrt') }}</p>
        </div>

        <div v-for="ort in arbeitsmappe.kataloge.orte" :key="ort.id"
             class="border border-default rounded p-3 bg-muted grid gap-3">
          <div class="grid md:grid-cols-[1fr_auto] gap-3 items-end">
            <TextField v-model="ort.name" :label="t('kataloge.ortName')"
                      :placeholder="t('kataloge.ortPlatzhalter')"/>
            <UButton size="sm" color="signal" variant="outline"
                     @click="ortEntfernen(ort)">
              <UIcon name="i-lucide-trash-2"/>
              {{ t('kataloge.ortEntfernen') }}
            </UButton>
          </div>
          <AddressField v-model="ort.adresse" :title="t('kataloge.ortAdresse')"/>
        </div>
      </div>
    </CollapsibleSection>

    <CollapsibleSection storage-key="alarmplaner_kataloge" name="fahrzeuge" :title="t('kataloge.fahrzeuge')"
                    :count="arbeitsmappe.kataloge.fahrzeuge.length">
      <template #actions>
        <UButton size="sm" color="neutral" variant="outline" @click="fahrzeugHinzufuegen">
          <UIcon name="i-lucide-plus"/>
          {{ t('kataloge.hinzufuegen') }}
        </UButton>
      </template>
      <p class="text-muted text-[13px] mb-3">{{ t('kataloge.fahrzeugeHinweis') }}</p>

      <p v-if="!arbeitsmappe.kataloge.fahrzeuge.length" class="text-muted text-sm">
        {{ t('kataloge.leer') }}
      </p>

      <div class="grid gap-2" @focusout="verlassen($event, fahrzeuge.ordnen)">
        <div v-for="fahrzeug in fahrzeuge.liste" :key="fahrzeug.id"
             class="grid md:grid-cols-[1fr_auto] gap-2 items-end">
          <div class="grid grid-cols-2 gap-2"
               :class="arbeitsmappe.planung.aktiv ? 'md:grid-cols-6' : 'md:grid-cols-4'">
            <TextField v-model="fahrzeug.funkrufname" :label="t('feld.funkrufname')"
                      @change="fahrzeugUmbenannt(fahrzeug)"/>
            <TextField v-model="fahrzeug.staerke" :label="t('feld.staerke')"/>
            <TextField v-model="fahrzeug.ezp" :label="t('feld.ezp')"/>
            <TextField v-model="fahrzeug.status" :label="t('feld.status')"/>
            <TextField v-if="arbeitsmappe.planung.aktiv" v-model="fahrzeug.plaetze"
                      :label="t('planung.plaetze')"/>
            <TextField v-if="arbeitsmappe.planung.aktiv" v-model="fahrzeug.fuehrerschein"
                      :label="t('planung.fuehrerschein')"
                      :suggestions="arbeitsmappe.kataloge.fahrerlaubnisse"/>
          </div>
          <UButton size="sm" color="signal" variant="outline"
                   :title="t('kataloge.eintragEntfernen')"
                   @click="fahrzeugEntfernen(arbeitsmappe.kataloge.fahrzeuge.indexOf(fahrzeug))">
            <UIcon name="i-lucide-x"/>
          </UButton>
          <p v-if="truppVorschau(fahrzeug.staerke)" class="tabular text-[13px] text-muted md:col-span-2">
            {{ truppVorschau(fahrzeug.staerke) }}
          </p>
        </div>
      </div>
    </CollapsibleSection>

    <CollapsibleSection storage-key="alarmplaner_kataloge" name="material" :title="t('kataloge.material')"
                    :count="arbeitsmappe.kataloge.material.length">
      <p class="text-muted text-[13px] mb-3">{{ t('kataloge.materialHinweis') }}</p>
      <form class="flex gap-2 mb-3" @submit.prevent="materialHinzufuegen">
        <UInput v-model="materialname" type="text"
                :placeholder="t('kataloge.materialPlatzhalter')" class="w-full"/>
        <UButton color="neutral" variant="outline" class="shrink-0" type="submit">
          <UIcon name="i-lucide-plus"/>
        </UButton>
      </form>
      <p v-if="!arbeitsmappe.kataloge.material.length" class="text-muted text-sm">
        {{ t('kataloge.keinMaterial') }}
      </p>
      <div class="grid gap-2" @focusout="verlassen($event, materialliste.ordnen)">
        <div v-for="stueck in materialliste.liste" :key="stueck.id"
             class="flex gap-2 items-center">
          <UInput v-model="stueck.name" type="text" class="w-full"/>
          <UInput v-model.number="stueck.bestand" type="number" min="0" step="1"
                  :title="t('kataloge.bestand')"
                  :placeholder="t('kataloge.bestandPlatzhalter')" class="w-20 shrink-0" :ui="{base: 'text-right tabular'}"/>
          <UButton size="sm" color="signal" variant="outline" class="shrink-0"
                   @click="materialEntfernen(stueck)">
            <UIcon name="i-lucide-trash-2"/>
          </UButton>
        </div>
      </div>
    </CollapsibleSection>

    <CollapsibleSection storage-key="alarmplaner_kataloge" name="stichwoerter" :title="t('kataloge.stichwoerter')"
                    :count="arbeitsmappe.kataloge.stichwoerter.length">
      <p class="text-muted text-[13px] mb-3">{{ t('kataloge.stichwoerterHinweis') }}</p>

      <form class="flex gap-2 mb-3" @submit.prevent="stichwortHinzufuegen">
        <UInput v-model="stichwort" type="text" list="stichwortliste"
                :placeholder="t('kataloge.stichwortPlatzhalter')" class="w-full"/>
        <UButton color="neutral" variant="outline" class="shrink-0" type="submit">
          <UIcon name="i-lucide-plus"/>
        </UButton>
      </form>
      <p v-if="stichwortvorschlaege.length" class="text-muted text-[13px] mb-3">
        {{ t('kataloge.stichwortFehlen') }}
        <UButton v-for="text in stichwortvorschlaege" :key="text" size="sm" color="neutral" variant="outline" class="ml-2 mb-1"
                 @click="stichwortUebernehmen(text)">
          {{ text }}
        </UButton>
      </p>

      <p v-if="!arbeitsmappe.kataloge.stichwoerter.length" class="text-muted text-sm">
        {{ t('kataloge.leer') }}
      </p>

      <div class="grid md:grid-cols-2 gap-2" @focusout="verlassen($event, stichwoerter.ordnen)">
        <div v-for="eintrag in stichwoerter.liste" :key="eintrag.id"
             class="flex gap-2 items-center">
          <UInput v-model="eintrag.text" type="text"
                  class="w-full" @change="stichwortUmbenannt(eintrag)"/>
          <UButton size="sm" color="signal" variant="outline" class="shrink-0"
                   :title="t('kataloge.eintragEntfernen')"
                   @click="stichwortEntfernen(arbeitsmappe.kataloge.stichwoerter.indexOf(eintrag))">
            <UIcon name="i-lucide-x"/>
          </UButton>
        </div>
      </div>
    </CollapsibleSection>

    <CollapsibleSection storage-key="alarmplaner_kataloge" name="tage" :title="t('planung.tage')"
                    :count="arbeitsmappe.kataloge.tage.length">
      <template #actions>
        <UButton size="sm" color="neutral" variant="outline" @click="tagAnlegen">
          <UIcon name="i-lucide-plus"/>
          {{ t('planung.tagNeu') }}
        </UButton>
      </template>
      <p v-if="!arbeitsmappe.kataloge.tage.length" class="text-muted text-sm">{{ t('planung.keineTage') }}</p>

      <div class="grid gap-2">
        <div v-for="tag in arbeitsmappe.kataloge.tage" :key="tag.id"
             class="grid md:grid-cols-[10rem_1fr_auto] gap-2 items-end">
          <div>
            <label class="field-label" :for="`${fieldId}-date-${tag.id}`">{{ t('planung.datum') }}</label>
            <UInput :id="`${fieldId}-date-${tag.id}`" v-model="tag.datum" type="date" class="w-full"/>
          </div>
          <TextField v-model="tag.name" :label="t('planung.tagName')"
                    :placeholder="t('planung.tagPlatzhalter')"/>
          <UButton size="sm" color="signal" variant="outline"
                   @click="ausListe(arbeitsmappe.kataloge.tage, tag)">
            <UIcon name="i-lucide-x"/>
          </UButton>
        </div>
      </div>
    </CollapsibleSection>

    <CollapsibleSection storage-key="alarmplaner_kataloge" name="personen" :title="t('planung.personen')"
                    :count="arbeitsmappe.kataloge.personen.length">
      <template #actions>
        <UButton size="sm" color="neutral" variant="outline" @click="personAnlegen">
          <UIcon name="i-lucide-plus"/>
          {{ t('planung.personNeu') }}
        </UButton>
      </template>
      <p class="text-muted text-[13px] mb-3">{{ t('planung.personenHinweis') }}</p>
      <p v-if="!arbeitsmappe.kataloge.personen.length" class="text-muted text-sm">
        {{ t('planung.keinePersonen') }}
      </p>

      <div class="grid gap-4">
        <div v-for="person in arbeitsmappe.kataloge.personen" :key="person.id"
             class="border border-default rounded p-3 bg-muted grid gap-3">
          <div class="grid md:grid-cols-[1fr_6rem_auto_auto] gap-3 items-end">
            <TextField v-model="person.name" :label="t('planung.personName')"/>
            <div>
              <label class="field-label" :for="`${fieldId}-count-${person.id}`">{{ t('planung.anzahl') }}</label>
              <UInput :id="`${fieldId}-count-${person.id}`" v-model.number="person.anzahl" type="number" min="1" class="w-full"/>
            </div>
            <label class="flex items-center gap-2 text-sm h-9.5"
                   :title="t('planung.blattHinweis')">
              <input v-model="person.blatt" type="checkbox"/>
              {{ t('planung.blatt') }}
            </label>
            <UButton size="sm" color="signal" variant="outline"
                     @click="ausListe(arbeitsmappe.kataloge.personen, person)">
              <UIcon name="i-lucide-trash-2"/>
            </UButton>
          </div>

          <div class="grid md:grid-cols-2 gap-3">
            <div>
              <span class="field-label">{{ t('planung.rollen') }}</span>
              <div class="flex flex-wrap gap-2 items-center">
                <UButton v-for="wert in arbeitsmappe.kataloge.rollen" :key="wert" size="sm"
                         :color="person.rollen.includes(wert) ? 'primary' : 'neutral'" :variant="person.rollen.includes(wert) ? 'solid' : 'outline'"
                         @click="umschalten(person.rollen, wert)">
                  {{ wert }}
                </UButton>
                <UInput type="text" list="rollenliste"
                        :placeholder="t('planung.rolleDazu')"
                        class="w-auto" @change="wortGeben('rollen', person.rollen, $event.target as HTMLInputElement)"/>
              </div>
            </div>
            <div>
              <span class="field-label">{{ t('planung.fahrerlaubnis') }}</span>
              <div class="flex flex-wrap gap-2 items-center">
                <UButton v-for="wert in arbeitsmappe.kataloge.fahrerlaubnisse" :key="wert" size="sm"
                         :color="person.fahrerlaubnis.includes(wert) ? 'primary' : 'neutral'" :variant="person.fahrerlaubnis.includes(wert) ? 'solid' : 'outline'"
                         @click="umschalten(person.fahrerlaubnis, wert)">
                  {{ wert }}
                </UButton>
                <UInput type="text" list="klassenliste"
                        :placeholder="t('planung.klasseDazu')"
                        class="w-auto" @change="wortGeben('fahrerlaubnisse', person.fahrerlaubnis,
                        $event.target as HTMLInputElement)"/>
              </div>
            </div>
          </div>

          <div>
            <div class="flex items-center gap-3 mb-2 flex-wrap">
              <span class="field-label mb-0">{{ t('planung.verfuegbar') }}</span>
              <UButton size="sm" color="neutral" variant="outline"
                       @click="verfuegbarkeitAnlegen(person)">
                <UIcon name="i-lucide-plus"/>
                {{ t('planung.fensterNeu') }}
              </UButton>
            </div>
            <p v-if="!person.verfuegbar.length" class="text-muted text-[13px]">
              {{ t('planung.immerDa') }}
            </p>
            <div class="grid gap-2">
              <div v-for="fenster in person.verfuegbar" :key="fenster.id"
                   class="grid md:grid-cols-[1fr_1fr_auto] gap-2 items-end">
                <div>
                  <label class="field-label" :for="`${fieldId}-from-${fenster.id}`">{{ t('planung.von') }}</label>
                  <UInput :id="`${fieldId}-from-${fenster.id}`" v-model="fenster.von" type="datetime-local" class="w-full"/>
                </div>
                <div>
                  <label class="field-label" :for="`${fieldId}-to-${fenster.id}`">{{ t('planung.bis') }}</label>
                  <UInput :id="`${fieldId}-to-${fenster.id}`" v-model="fenster.bis" type="datetime-local" class="w-full"/>
                </div>
                <UButton size="sm" color="signal" variant="outline"
                         @click="ausListe(person.verfuegbar, fenster)">
                  <UIcon name="i-lucide-x"/>
                </UButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </CollapsibleSection>
    <div class="grid md:grid-cols-2 gap-4">
      <CollapsibleSection v-for="liste in listen" :key="liste.schluessel" storage-key="alarmplaner_kataloge" :name="liste.schluessel"
                      :title="liste.titel" :count="arbeitsmappe.kataloge[liste.schluessel].length">

        <form class="flex gap-2 mb-3" @submit.prevent="hinzufuegen(liste.schluessel)">
          <UInput v-model="entwurf[liste.schluessel]" type="text" class="w-full"/>
          <UButton color="neutral" variant="outline" class="shrink-0" type="submit">
            <UIcon name="i-lucide-plus"/>
          </UButton>
        </form>

        <p v-if="!arbeitsmappe.kataloge[liste.schluessel].length" class="text-muted text-sm">
          {{ t('kataloge.leer') }}
        </p>

        <ul class="flex flex-wrap gap-2">
          <li v-for="(wert, index) in arbeitsmappe.kataloge[liste.schluessel]" :key="wert"
              class="flex items-center gap-2 border border-default rounded px-2 py-1 bg-muted">
            <span class="text-sm">{{ wert }}</span>
            <button type="button" class="text-muted hover:text-signal"
                    :title="t('kataloge.eintragEntfernen')"
                    @click="entfernen(liste.schluessel, index)">
              <UIcon name="i-lucide-x"/>
            </button>
          </li>
        </ul>
      </CollapsibleSection>
    </div>
  </div>
</template>
