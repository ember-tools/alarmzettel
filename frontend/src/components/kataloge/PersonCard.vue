<script setup lang="ts">
import {TextField} from '@emberbox/ui'
import {computed, useId} from 'vue'
import {t} from '../../i18n'
import {arbeitsmappe} from '../../store/arbeitsmappe'
import {entfernen as ausListe, umschalten, verfuegbarkeitAnlegen, wortHinzufuegen} from '../../store/planung'

/**
 * One person in the catalogue: name, count, sheet, roles, licences and availability. The person is
 * given by id and looked up in the workbook, which this component edits directly.
 */
const {personId} = defineProps<{ personId: string }>()

const person = computed(() => arbeitsmappe.kataloge.personen.find(eintrag => eintrag.id === personId)!)

/** The prefix of this instance's field ids, so labels find their fields when it appears more than once. */
const fieldId = useId()

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
</script>

<template>
  <div class="border border-default rounded p-3 bg-muted grid gap-3">
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
</template>
