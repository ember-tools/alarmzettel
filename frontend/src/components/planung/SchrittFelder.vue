<script setup lang="ts">
import {computed} from 'vue'
import {t} from '../../i18n'
import {arbeitsmappe} from '../../store/arbeitsmappe'
import {
  besatzungHinzufuegen, entfernen, fahrerSetzen, fahrzeitSchaetzen, nachziehen,
  alleOrte, darfFahren, lageName, materialHinzufuegen, materialName, materialSichern,
  ortName, personName, plandaten, programmpunkt, programmpunktAnlegen,
} from '../../store/planung'
import {anfahrt, fahrzeitSchaetzung, pruefen} from '../../scripts/ablauf'
import type {Befund} from '../../scripts/ablauf'
import {alsMinuten, dauer, uhrzeit, verschieben} from '../../scripts/zeit'
import type {Lauf, Schritt} from '../../interfaces/Planung'

/**
 * Alles, was an einem Schritt hängt. Die Kette zeigt es untereinander, der Tagesplan in einem
 * Fenster – geschrieben ist es einmal, damit an beiden Stellen dasselbe steht.
 */
const {lauf, schritt} = defineProps<{ lauf: Lauf, schritt: Schritt }>()

/** Geprüft wird der ganze Plan; hier steht, was diesen Schritt angeht. */
const befunde = computed<Befund[]>(() =>
    pruefen(plandaten()).filter(befund => befund.schrittId === schritt.id))

function meldung(befund: Befund): string {
  return t(`ablauf.befund.${befund.art}`, befund.werte ?? {})
}

/** Die Fahrt, die vor diesem Aufenthalt von selbst entsteht. */
const weg = computed(() => anfahrt(plandaten(), lauf, schritt))

/** Das Stichwort des Alarms – es steht als Platzhalter dort, wo die Bezeichnung leer bleibt. */
const stichwortDerLage = computed(() => {
  const punkt = programmpunkt(schritt.programmpunktId)
  return arbeitsmappe.alarme.find(alarm => alarm.id === punkt?.alarmId)?.stichwort ?? ''
})

const schaetzung = computed(() => fahrzeitSchaetzung(plandaten(), lauf, schritt))

/** Wie viele Köpfe an Bord sind – „Mimen (4)“ zählt vier. */
const koepfe = computed(() => schritt.besatzung.reduce((summe, sitzt) => {
  const person = arbeitsmappe.kataloge.personen.find(p => p.id === sitzt.personId)
  return summe + (person?.anzahl || 1)
}, 0))

/**
 * Was zuletzt als Fahrzeit vorgeschlagen wurde. Eine Dauer, die noch genau so dasteht, darf ein
 * neuer Vorschlag ersetzen; eine von Hand gesetzte bleibt stehen, auch wenn sich das Ziel noch
 * einmal ändert – die Schätzung wird vorgeschlagen und nicht gesetzt.
 */
const vorgeschlagen = new Map<string, number>()

/** Beim Wechsel des Ziels die geschätzte Fahrzeit vorschlagen, solange keine eigene dasteht. */
async function zielGewaehlt() {
  if (schritt.art !== 'fahrt') return
  const vorher = lauf.schritte[lauf.schritte.indexOf(schritt) - 1]
  if (!vorher) return
  const eigene = dauer(schritt.von, schritt.bis)
  if (eigene !== null && eigene !== vorgeschlagen.get(schritt.id)) return
  const minuten = await fahrzeitSchaetzen(vorher.ortId, schritt.ortId, schritt.mittel)
  if (minuten === null) return
  vorgeschlagen.set(schritt.id, minuten)
  schritt.bis = verschieben(schritt.von, minuten)
  nachziehen(lauf, schritt)
}

/**
 * Ein Schritt fängt an, wo der vorige aufhört. Wird der Beginn vorgezogen, endet der vorige
 * eben früher; wird er nach hinten geschoben, bleibt eine Lücke – die ist erlaubt und heißt,
 * dass hier gewartet wird. Was nicht entstehen darf, ist eine Überschneidung.
 */
function beginnGesetzt() {
  const vorher = lauf.schritte[lauf.schritte.indexOf(schritt) - 1]
  const beginn = alsMinuten(schritt.von)
  if (vorher && beginn !== null && beginn < (alsMinuten(vorher.bis) ?? 0)) vorher.bis = schritt.von
  if (beginn !== null && beginn >= (alsMinuten(schritt.bis) ?? 0)) {
    schritt.bis = verschieben(schritt.von, 5)
  }
  nachziehen(lauf, schritt)
}

/** Ein Name, den es noch nicht gibt, wird angelegt; einer aus der Liste wird nur ausgewählt. */
function materialGewaehlt(feld: HTMLInputElement) {
  const materialId = materialSichern(feld.value)
  if (materialId) materialHinzufuegen(schritt, materialId)
  feld.value = ''
}

function lageAnlegen() {
  schritt.programmpunktId = programmpunktAnlegen().id
}
</script>

<template>
  <div class="grid gap-2">
    <datalist id="materialliste">
      <option v-for="stueck in arbeitsmappe.kataloge.material" :key="stueck.id"
              :value="stueck.name"/>
    </datalist>

    <div class="flex items-center gap-3 flex-wrap text-[13px] text-muted">
      <span>{{ dauer(schritt.von, schritt.bis) }} min</span>
      <span v-if="weg" :title="t('ablauf.anfahrtHinweis')">
        <UIcon
          :name="weg.mittel === 'fahrzeug' ? 'i-lucide-truck' : 'i-lucide-footprints'"
          class="mr-1"/>
        {{ t('ablauf.anfahrt', {woher: ortName(weg.vonOrtId), an: uhrzeit(weg.bis)}) }}
      </span>
      <span v-if="schaetzung !== null" :title="t('ablauf.schaetzungHinweis')">
        {{ t('ablauf.geschaetzt', {n: schaetzung}) }}
      </span>
    </div>

    <div class="grid md:grid-cols-4 gap-2 items-end">
      <div>
        <label class="field-label">{{ t('ablauf.beginn') }}</label>
        <UInput v-model="schritt.von" type="datetime-local" step="300"
                @change="beginnGesetzt()" class="w-full"/>
      </div>
      <div>
        <label class="field-label">{{ t('ablauf.ende') }}</label>
        <UInput v-model="schritt.bis" type="datetime-local" step="300"
                @change="nachziehen(lauf, schritt)" class="w-full"/>
      </div>
      <div>
        <label class="field-label">
          {{ schritt.art === 'fahrt' ? t('ablauf.ziel') : t('ablauf.ort') }}
        </label>
        <select v-model="schritt.ortId" class="native-select" @change="zielGewaehlt()">
          <option v-for="ort in alleOrte()" :key="ort.id" :value="ort.id">
            {{ ort.name || t('ablauf.ohneName') }}
          </option>
        </select>
      </div>
      <div v-if="!lauf.fahrzeugId && (schritt.art === 'fahrt' || weg)">
        <label class="field-label">{{ t('ablauf.mittel') }}</label>
        <select v-model="schritt.mittel" class="native-select" @change="zielGewaehlt()">
          <option value="fuss">{{ t('ablauf.zuFuss') }}</option>
          <option value="eigen">{{ t('ablauf.eigen') }}</option>
        </select>
      </div>
      <div v-if="schritt.art === 'aufenthalt'">
        <label class="field-label">{{ t('ablauf.lage') }}</label>
        <div class="flex gap-2">
          <select v-model="schritt.programmpunktId" class="native-select">
            <option value="">{{ t('ablauf.keineLage') }}</option>
            <option v-for="punkt in arbeitsmappe.planung.programmpunkte" :key="punkt.id"
                    :value="punkt.id">
              {{ lageName(punkt.id) || t('ablauf.ohneName') }}
            </option>
          </select>
          <UButton size="sm" color="neutral" variant="outline" class="shrink-0" :title="t('ablauf.lageNeu')"
                   @click="lageAnlegen()">
            <UIcon name="i-lucide-plus"/>
          </UButton>
        </div>
      </div>
    </div>

    <div v-if="weg" class="flex items-center gap-2">
      <label class="field-label mb-0">{{ t('ablauf.fahrzeit') }}</label>
      <UInput v-model.number="schritt.fahrzeit" type="number" min="0" step="5"
              :placeholder="String(schaetzung ?? 0)" class="w-20 shrink-0" :ui="{base: 'text-right tabular'}"/>
      <span class="text-muted text-[13px]">{{ t('ablauf.fahrzeitHinweis') }}</span>
    </div>

    <div v-if="schritt.programmpunktId && programmpunkt(schritt.programmpunktId)"
         class="grid md:grid-cols-2 gap-2">
      <div v-if="lauf.fahrzeugId" class="flex items-center gap-3 flex-wrap md:col-span-2">
        <div>
          <span class="field-label">{{ t('ablauf.imAufgebot') }}</span>
          <UFieldGroup>
            <UButton size="sm" label="J" :title="t('feld.ja')" :aria-pressed="schritt.aufgebot"
                     :color="schritt.aufgebot ? 'primary' : 'neutral'" :variant="schritt.aufgebot ? 'solid' : 'outline'"
                     @click="schritt.aufgebot = true"/>
            <UButton size="sm" label="N" :title="t('feld.nein')" :aria-pressed="!schritt.aufgebot"
                     :color="schritt.aufgebot ? 'neutral' : 'primary'" :variant="schritt.aufgebot ? 'outline' : 'solid'"
                     @click="schritt.aufgebot = false"/>
          </UFieldGroup>
        </div>
        <span class="text-muted text-[13px] self-end pb-2">
          {{ t('ablauf.imAufgebotHinweis') }}
        </span>
      </div>
      <div>
        <label class="field-label">{{ t('ablauf.lageName') }}</label>
        <UInput v-model="programmpunkt(schritt.programmpunktId)!.name" type="text"
                :placeholder="stichwortDerLage || t('ablauf.lageNamePlatzhalter')"
                :title="t('ablauf.lageNameHinweis')" class="w-full"/>
      </div>
      <div>
        <label class="field-label">{{ t('ablauf.lageAlarm') }}</label>
        <select v-model="programmpunkt(schritt.programmpunktId)!.alarmId" class="native-select">
          <option value="">{{ t('ablauf.ohneAlarm') }}</option>
          <option v-for="alarm in arbeitsmappe.alarme" :key="alarm.id" :value="alarm.id">
            {{ alarm.stichwort || t('ablauf.ohneName') }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="lauf.fahrzeugId">
      <span class="field-label">{{ t('ablauf.besatzung') }} ({{ koepfe }})</span>
      <div class="flex flex-wrap gap-2">
        <span v-for="sitzt in schritt.besatzung" :key="sitzt.id" class="flex">
          <UButton size="sm" class="rounded-r-none"
                   :color="sitzt.faehrt ? 'primary' : 'neutral'" :variant="sitzt.faehrt ? 'solid' : 'outline'"
                   :disabled="!sitzt.faehrt && !darfFahren(lauf.fahrzeugId, sitzt.personId)"
                   :title="darfFahren(lauf.fahrzeugId, sitzt.personId)
                   ? t('ablauf.fahrerUmschalten')
                   : t('ablauf.darfNichtFahren', {wer: personName(sitzt.personId)})"
                   @click="fahrerSetzen(lauf, schritt, sitzt.personId)">
            <UIcon v-if="sitzt.faehrt" name="i-lucide-check"/>
            {{ personName(sitzt.personId) }}
          </UButton>
          <UButton size="sm" color="neutral" variant="outline" class="rounded-l-none border-l-0 px-2"
                   :title="t('ablauf.besatzungEntfernen', {wer: personName(sitzt.personId)})"
                   @click="entfernen(schritt.besatzung, sitzt)">
            <UIcon name="i-lucide-x"/>
          </UButton>
        </span>
        <select class="native-select w-auto" @change="besatzungHinzufuegen(schritt, ($event.target as HTMLSelectElement).value); ($event.target as HTMLSelectElement).value = ''">
          <option value="">{{ t('ablauf.personDazu') }}</option>
          <option v-for="person in arbeitsmappe.kataloge.personen" :key="person.id"
                  :value="person.id">{{ person.name || t('ablauf.ohneName') }}</option>
        </select>
      </div>
    </div>

    <div class="grid md:grid-cols-2 gap-3">
      <div>
        <span class="field-label">{{ t('ablauf.material') }}</span>
        <div class="flex flex-wrap gap-2 items-center">
          <UFieldGroup v-for="stueck in schritt.material" :key="stueck.id" size="sm">
            <UInput v-model.number="stueck.anzahl" type="number" min="1" step="1" class="w-16"
                    :title="t('ablauf.materialAnzahl')" :ui="{base: 'text-right tabular'}"/>
            <UBadge color="neutral" variant="outline" size="lg" icon="i-lucide-package"
                    :label="materialName(stueck.materialId) || t('ablauf.ohneName')"/>
            <UButton color="neutral" variant="outline"
                     :title="t('ablauf.materialEntfernen', {was: materialName(stueck.materialId)})"
                     @click="entfernen(schritt.material, stueck)">
              <UIcon name="i-lucide-x"/>
            </UButton>
          </UFieldGroup>
          <UInput type="text" list="materialliste"
                  :placeholder="t('ablauf.materialDazu')"
                  @change="materialGewaehlt($event.target as HTMLInputElement)" class="w-auto"/>
        </div>
      </div>

      <div>
        <label class="field-label">{{ t('ablauf.notiz') }}</label>
        <UInput v-model="schritt.notiz" type="text"
                :placeholder="t('ablauf.notizPlatzhalter')" class="w-full"/>
      </div>
    </div>

    <div v-if="befunde.length" class="flex flex-wrap gap-3">
      <span v-for="(befund, nummer) in befunde" :key="nummer"
            class="text-(--eb-signal-text) text-[13px]">{{ meldung(befund) }}</span>
    </div>
  </div>
</template>
