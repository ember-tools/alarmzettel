<script setup lang="ts">
import {TextAreaField, TextField} from '@emberbox/ui'
import {t} from '../../i18n'
import {festnetznummer, mobilnummer, zufallsname} from '../../scripts/generator'
import type {Alarm} from '../../interfaces/Alarm'

const alarm = defineModel<Alarm>({required: true})

/** These sheets are written for practice, so the personal details are made up, not typed. */
function neuErzeugen() {
  alarm.value.meldungsquelle = festnetznummer()
  alarm.value.rueckrufnummer = mobilnummer()
  alarm.value.anrufer = zufallsname()
}
</script>

<template>
  <section class="panel">
    <div class="flex items-center justify-between mb-3 gap-2 flex-wrap">
      <h2 class="section-title">{{ t('abschnitt.beteiligte') }}</h2>
      <UButton size="sm" color="neutral" variant="outline" :title="t('feld.erzeugenHinweis')"
               @click="neuErzeugen">
        <UIcon name="i-lucide-refresh-cw"/>
        {{ t('feld.erzeugen') }}
      </UButton>
    </div>
    <div class="grid md:grid-cols-2 gap-3">
      <TextField v-model="alarm.meldungsquelle" :label="t('feld.meldungsquelle')"/>
      <TextField v-model="alarm.rueckrufnummer" :label="t('feld.rueckrufnummer')"/>
      <TextField v-model="alarm.anrufer" :label="t('feld.anrufer')"/>
      <TextField v-model="alarm.betroffener" :label="t('feld.betroffener')"/>
      <TextField v-model="alarm.meldender" :label="t('feld.meldender')"/>
    </div>
    <div class="mt-3">
      <TextAreaField v-model="alarm.wasIstPassiert" :label="t('feld.wasIstPassiert')" :rows="2"/>
    </div>
  </section>
</template>
