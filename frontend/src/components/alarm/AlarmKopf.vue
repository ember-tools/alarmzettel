<script setup lang="ts">
import {ComboboxField, DateTimeField, TextAreaField, TextField, YesNoField} from '@emberbox/ui'
import {t} from '../../i18n'
import {stichwortSichern, stichwortVorschlaege} from '../../store/arbeitsmappe'
import type {Alarm} from '../../interfaces/Alarm'

const alarm = defineModel<Alarm>({required: true})

/** A yes/no field stores and shows what the slip prints: `J` or `N`. */
const SLIP_YES_NO = {
  yesValue: 'J',
  noValue: 'N',
  yesLabel: 'J',
  noLabel: 'N',
  yesTitle: t('feld.ja'),
  noTitle: t('feld.nein'),
}

/**
 * Zeigt eine Lage auf diesen Alarm, kommen die Zeiten aus dem Ablaufplan. Dann stehen hier die
 * Werte, die gedruckt werden, und nicht die eingetippten, die es nicht aufs Blatt schaffen.
 */
const {zeiten} = defineProps<{ zeiten?: Record<string, string> }>()

const ZEITPUNKTE = ['einsatz', 'meldung'] as const

/**
 * The Meldung follows the Einsatz. The two are minutes apart on a real call, but on a sheet
 * written for an exercise they are the same time far more often than not, and typing it twice is
 * work for nothing. Correcting the Meldung afterwards stands until the Einsatz is touched again.
 */
function meldungFolgt() {
  alarm.value.meldungDatum = alarm.value.einsatzDatum
  alarm.value.meldungZeit = alarm.value.einsatzZeit
}

/**
 * A Stichwort is linked to its catalogue entry by id rather than by its text, so correcting the
 * catalogue later reaches this Alarm. One written for the first time joins the catalogue, which
 * is what gives it an entry to be linked to.
 */
function stichwortGewaehlt() {
  alarm.value.stichwortId = stichwortSichern(alarm.value.stichwort)
}
</script>

<template>
  <section class="panel">
    <h2 class="section-title">{{ t('abschnitt.kopf') }}</h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div v-if="zeiten?.einsatzNr">
        <label class="field-label">{{ t('feld.einsatzNr') }}</label>
        <UInput type="text" disabled :model-value="zeiten.einsatzNr" class="w-full"/>
      </div>
      <TextField v-else v-model="alarm.einsatzNr" :label="t('feld.einsatzNr')"/>
      <TextField v-model="alarm.aPlatz" :label="t('feld.aPlatz')"/>
      <TextField v-model="alarm.behoerde" :label="t('feld.behoerde')"/>
      <TextField v-model="alarm.titel" :label="t('feld.titel')"/>
      <template v-if="zeiten">
        <div v-for="name in ZEITPUNKTE" :key="name">
          <label class="field-label">{{ t(`feld.${name}`) }}</label>
          <UInput type="text" disabled
                  :model-value="`${zeiten[`${name}Datum`]} ${zeiten[`${name}Zeit`]}`.trim()" class="w-full"/>
        </div>
      </template>
      <template v-else>
        <DateTimeField v-model:date="alarm.einsatzDatum" v-model:time="alarm.einsatzZeit"
                       :label="t('feld.einsatz')" @change="meldungFolgt"/>
        <DateTimeField v-model:date="alarm.meldungDatum" v-model:time="alarm.meldungZeit"
                       :label="t('feld.meldung')"/>
      </template>
      <YesNoField v-model="alarm.polizei" :label="t('feld.polizei')" v-bind="SLIP_YES_NO"/>
      <YesNoField v-model="alarm.sonderrechte" :label="t('feld.sonderrechte')" v-bind="SLIP_YES_NO"/>
      <TextField v-model="alarm.arbeitsgruppe" :label="t('feld.arbeitsgruppe')"/>
      <TextField v-model="alarm.wachalarmNr" :label="t('feld.wachalarmNr')"/>
    </div>
  </section>

  <section class="panel">
    <h2 class="section-title">{{ t('abschnitt.stichwort') }}</h2>
    <div class="grid gap-3">
      <ComboboxField v-model="alarm.stichwort" :label="t('feld.stichwort')"
                   :suggestions="stichwortVorschlaege()" @change="stichwortGewaehlt"/>
      <TextAreaField v-model="alarm.kurzinfo" :label="t('feld.kurzinfo')" :rows="2"/>
    </div>
  </section>
</template>
