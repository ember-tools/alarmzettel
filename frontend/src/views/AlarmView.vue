<script setup lang="ts">
import {computed, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import AlarmAusPlan from '../components/alarm/AlarmAusPlan.vue'
import AlarmKopf from '../components/alarm/AlarmKopf.vue'
import AlarmAdressen from '../components/alarm/AlarmAdressen.vue'
import AlarmBeteiligte from '../components/alarm/AlarmBeteiligte.vue'
import AlarmHinweise from '../components/alarm/AlarmHinweise.vue'
import AlarmEinsatzmittel from '../components/alarm/AlarmEinsatzmittel.vue'
import PdfVorschau from '../components/PdfVorschau.vue'
import {t} from '../i18n'
import {alarmFinden, arbeitsmappe} from '../store/arbeitsmappe'
import {fehlertext, renderEinen} from '../api/render'
import {alarmableitung, type Alarmableitung} from '../api/plan'
import {jetztAbgleichen} from '../store/sync'

const route = useRoute()
const fehler = ref<string | null>(null)
const alarm = computed(() => alarmFinden(String(route.params.id)))
const abgeleitet = ref<Alarmableitung | null>(null)

/**
 * Zeigt eine Lage auf diesen Alarm, kommen Zeiten, Einsatzadresse und Aufgebot aus dem Plan.
 * Gerechnet wird das auf dem Server, damit hier nichts anderes steht als auf dem Blatt – und
 * neu gerechnet, sobald sich am Plan etwas ändert, das diesen Alarm angeht. Vorher wird
 * abgeglichen, sonst fragte die Ansicht nach einem eben angelegten Alarm, bevor der Server ihn kennt.
 */
const planstand = computed(() => JSON.stringify([
  route.params.id,
  arbeitsmappe.planung.programmpunkte.map(punkt => [punkt.id, punkt.alarmId]),
  arbeitsmappe.planung.laeufe.map(lauf => lauf.schritte.map(
      schritt => [schritt.programmpunktId, schritt.ortId, schritt.von, schritt.bis,
                  schritt.besatzung.length])),
]))

watch(planstand, async () => {
  try {
    await jetztAbgleichen()
    abgeleitet.value = await alarmableitung(String(route.params.id))
    fehler.value = null
  } catch (error) {
    fehler.value = await fehlertext(error)
  }
}, {immediate: true})

/** Der Kopf zeigt die Zeiten des ersten Blattes; die der übrigen stehen im Plan-Abschnitt. */
const planzeiten = computed(() => {
  const blatt = abgeleitet.value?.blaetter[0]
  return blatt ? {
    einsatzDatum: blatt.einsatzDatum, einsatzZeit: blatt.einsatzZeit,
    meldungDatum: blatt.einsatzDatum, meldungZeit: blatt.einsatzZeit,
    einsatzNr: blatt.einsatzNr,
  } : undefined
})

/**
 * Renders the sheet after an exchange, so it shows what everyone has rather than what this browser
 * happened to see a few seconds ago, and a freshly created alarm is on the server before it is
 * asked for. Outside a shared session the exchange does nothing.
 */
async function rendern(): Promise<Blob> {
  await jetztAbgleichen()
  return renderEinen(String(route.params.id))
}

async function pdf() {
  fehler.value = null
  try {
    const blob = await rendern()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `alarmzettel-${alarm.value?.einsatzNr || 'alarm'}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    fehler.value = await fehlertext(error)
  }
}
</script>

<template>
  <div v-if="!alarm" class="panel text-center py-10">
    <p>{{ t('nichtGefunden.titel') }}</p>
    <UButton color="neutral" variant="outline" class="mt-3 inline-flex" to="/alarme">{{ t('nichtGefunden.zurueck') }}</UButton>
  </div>

  <div v-else class="grid gap-5">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-3">
        <UButton size="sm" color="neutral" variant="outline" to="/alarme">
          <UIcon name="i-lucide-arrow-left"/>
          {{ t('aktion.zurueck') }}
        </UButton>
        <h1 class="headline text-2xl">
          {{ alarm.stichwort || t('liste.ohneStichwort') }}
        </h1>
      </div>
      <UButton color="neutral" variant="outline" @click="pdf">
        <UIcon name="i-lucide-file-text"/>
        {{ t('datei.pdfEiner') }}
      </UButton>
    </div>

    <p v-if="fehler" class="text-sm text-(--eb-signal-text)">{{ fehler }}</p>

    <div class="grid xl:grid-cols-[minmax(0,1fr)_minmax(360px,44%)] gap-5 items-start">
      <div class="grid gap-4 min-w-0">
        <AlarmAusPlan v-if="abgeleitet" :abgeleitet="abgeleitet"/>
        <AlarmKopf v-model="alarm" :zeiten="planzeiten"/>
        <AlarmAdressen v-model="alarm" :aus-plan="Boolean(abgeleitet?.einsatzadresse)"/>
        <AlarmBeteiligte v-model="alarm"/>
        <AlarmHinweise v-model="alarm"/>
        <AlarmEinsatzmittel v-model="alarm"
                            :aus-plan="Boolean(abgeleitet?.blaetter.length)"/>
      </div>

      <div class="xl:sticky xl:top-5 h-[75vh] min-h-100">
        <PdfVorschau :rendern="rendern" :ausloeser="alarm"/>
      </div>
    </div>
  </div>
</template>
