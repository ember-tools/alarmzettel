<script setup lang="ts">
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import {t} from '../i18n'
import {
    alarmAnlegen, alarmKopieren, alarmLoeschen, alarmVerschieben, arbeitsmappe, ersetzen, uebernehmen,
} from '../store/arbeitsmappe'
import {renderAlle, fehlertext} from '../api/render'
import {tabelleImportieren} from '../api/tabelle'
import {useConfirm} from '@emberbox/ui'
import {jetztAbgleichen} from '../store/sync'

const router = useRouter()
const datei = ref<HTMLInputElement>()
const tabelle = ref<HTMLInputElement>()
const meldung = ref<string | null>(null)
const fehler = ref<string | null>(null)
const confirm = useConfirm()

/** Asks before replacing a working set that has something in it, without blocking the page. */
async function ersetzenLassen(tun: () => void) {
  if (!arbeitsmappe.alarme.length || await confirm(t('datei.ersetzen'), {confirmLabel: t('aktion.weiter')})) tun()
}

function anlegen() {
  router.push(`/alarm/${alarmAnlegen().id}`)
}

/**
 * Saves the workbook after an exchange, so the file holds what everyone has. Outside a shared
 * session the exchange does nothing.
 */
async function herunterladen() {
  await jetztAbgleichen()
  speichern(new Blob([JSON.stringify(arbeitsmappe, null, 2)], {type: 'application/json'}),
      'alarmplaner.json')
}

/**
 * Prints all sheets after an exchange, so they show what everyone has rather than what this
 * browser happened to see a few seconds ago. Outside a shared session the exchange does nothing.
 */
async function pdf() {
  fehler.value = null
  try {
    await jetztAbgleichen()
    speichern(await renderAlle(), 'alarmzettel.pdf')
  } catch (error) {
    fehler.value = await fehlertext(error)
  }
}

function speichern(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  URL.revokeObjectURL(url)
}

/** The old spreadsheet: one row per Alarm, one vehicle, Hinweise squashed into one cell. */
async function tabelleLaden(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  fehler.value = null
  meldung.value = null
  try {
    const geladen = await tabelleImportieren(file)
    ersetzenLassen(() => {
      ersetzen(uebernehmen(geladen))
      meldung.value = t('datei.importiert', arbeitsmappe.alarme.length)
    })
  } catch (error) {
    fehler.value = await fehlertext(error)
  } finally {
    if (tabelle.value) tabelle.value.value = ''
  }
}

async function laden(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  fehler.value = null
  meldung.value = null
  try {
    const roh = JSON.parse(await file.text())
    ersetzenLassen(() => {
      ersetzen(uebernehmen(roh))
      meldung.value = t('datei.geladen')
    })
  } catch {
    fehler.value = t('datei.fehlerhaft')
  } finally {
    if (datei.value) datei.value.value = ''
  }
}
</script>

<template>
  <div class="grid gap-5">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div>
        <h1 class="headline text-2xl">{{ t('nav.alarme') }}</h1>
        <p class="eyebrow mt-1">{{ t('liste.anzahl', arbeitsmappe.alarme.length) }}</p>
      </div>
      <div class="flex gap-2 flex-wrap">
        <UButton color="neutral" variant="outline" @click="tabelle?.click()">
          <UIcon name="i-lucide-table"/>
          {{ t('datei.tabelle') }}
        </UButton>
        <UButton color="neutral" variant="outline" @click="datei?.click()">
          <UIcon name="i-lucide-upload"/>
          {{ t('datei.hochladen') }}
        </UButton>
        <UButton color="neutral" variant="outline" :disabled="!arbeitsmappe.alarme.length" @click="herunterladen">
          <UIcon name="i-lucide-download"/>
          {{ t('datei.herunterladen') }}
        </UButton>
        <UButton color="neutral" variant="outline" :disabled="!arbeitsmappe.alarme.length" @click="pdf">
          <UIcon name="i-lucide-file-text"/>
          {{ t('datei.pdfAlle') }}
        </UButton>
        <UButton @click="anlegen">
          <UIcon name="i-lucide-plus"/>
          {{ t('liste.neu') }}
        </UButton>
      </div>
    </div>

    <input ref="datei" type="file" accept="application/json" class="hidden" @change="laden"/>
    <input ref="tabelle" type="file" class="hidden"
           accept=".ods,.xlsx,application/vnd.oasis.opendocument.spreadsheet,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
           @change="tabelleLaden"/>

    <p v-if="meldung" class="text-sm text-muted">{{ meldung }}</p>
    <p v-if="fehler" class="text-sm text-(--eb-signal-text)">{{ fehler }}</p>

    <div v-if="!arbeitsmappe.alarme.length" class="panel text-center py-10">
      <p class="text-highlighted">{{ t('liste.leer') }}</p>
      <p class="text-muted text-sm mt-1">{{ t('liste.leerHinweis') }}</p>
    </div>

    <ul v-else class="grid gap-2">
      <li v-for="(alarm, index) in arbeitsmappe.alarme" :key="alarm.id"
          class="panel flex items-center gap-3 flex-wrap">
        <span class="tabular text-muted w-8 shrink-0">{{ alarm.einsatzNr || index }}</span>
        <div class="grow min-w-40">
          <div class="font-condensed font-bold tracking-wide uppercase">
            {{ alarm.stichwort || t('liste.ohneStichwort') }}
          </div>
          <div class="text-sm text-muted">
            {{ alarm.kurzinfo }}
            <span v-if="alarm.einsatzadresse.strasse" class="tabular">
              · {{ alarm.einsatzadresse.strasse }} {{ alarm.einsatzadresse.hnr }}
            </span>
          </div>
        </div>
        <span class="eyebrow shrink-0">
          {{ alarm.einsatzDatum }} {{ alarm.einsatzZeit }}
        </span>
        <div class="flex gap-1 shrink-0">
          <UButton size="sm" color="neutral" variant="outline" :title="t('liste.hoch')"
                   :disabled="index === 0" @click="alarmVerschieben(alarm.id, -1)">
            <UIcon name="i-lucide-chevron-up"/>
          </UButton>
          <UButton size="sm" color="neutral" variant="outline" :title="t('liste.runter')"
                   :disabled="index === arbeitsmappe.alarme.length - 1"
                   @click="alarmVerschieben(alarm.id, 1)">
            <UIcon name="i-lucide-chevron-down"/>
          </UButton>
          <UButton size="sm" color="neutral" variant="outline" :title="t('liste.kopieren')"
                   @click="alarmKopieren(alarm.id)">
            <UIcon name="i-lucide-copy"/>
          </UButton>
          <UButton size="sm" color="signal" variant="outline" :title="t('liste.loeschen')"
                   @click="alarmLoeschen(alarm.id)">
            <UIcon name="i-lucide-trash-2"/>
          </UButton>
          <UButton size="sm" color="neutral" variant="outline" :to="`/alarm/${alarm.id}`">
            <UIcon name="i-lucide-pencil"/>
            {{ t('liste.oeffnen') }}
          </UButton>
        </div>
      </li>
    </ul>

  </div>
</template>
