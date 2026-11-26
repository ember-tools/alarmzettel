<script setup lang="ts">
import SchrittFelder from './SchrittFelder.vue'
import {t} from '../../i18n'
import {entfernen, mehrereTage, schrittAnhaengen, schrittEinfuegen} from '../../store/planung'
import {tagVon, uhrzeit} from '../../scripts/zeit'
import type {Lauf} from '../../interfaces/Planung'

/**
 * Die Kette als Folge von Karten. Was an einem Schritt hängt, steht in `SchrittFelder` – dieselben
 * Felder benutzt der Tagesplan in seinem Fenster.
 */
const {lauf} = defineProps<{ lauf: Lauf }>()
</script>

<template>
  <div class="grid gap-2">
    <div v-for="(schritt, stelle) in lauf.schritte" :key="schritt.id"
         class="border border-default rounded p-3 bg-muted grid gap-2">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="eyebrow">{{ stelle + 1 }}.</span>
        <span class="flex">
          <UButton size="sm" color="neutral" variant="outline" class="rounded-r-none px-2"
                   :title="t('ablauf.aufenthaltDavor')"
                   @click="schrittEinfuegen(lauf, stelle, 'aufenthalt')">
            <UIcon name="i-lucide-plus"/>
          </UButton>
          <UButton size="sm" color="neutral" variant="outline" class="rounded-l-none border-l-0 px-2"
                   :title="t('ablauf.fahrtDavor')"
                   @click="schrittEinfuegen(lauf, stelle, 'fahrt')">
            <UIcon name="i-lucide-chevron-right"/>
          </UButton>
        </span>
        <span class="tabular text-sm">
          <span v-if="mehrereTage()" class="text-muted">{{ tagVon(schritt.von) }}</span>
          {{ uhrzeit(schritt.von) }}–{{ uhrzeit(schritt.bis) }}
        </span>
        <span class="grow" />
        <UButton size="sm" color="signal" variant="outline"
                 @click="entfernen(lauf.schritte, schritt)">
          <UIcon name="i-lucide-x"/>
        </UButton>
      </div>

      <SchrittFelder :lauf-id="lauf.id" :schritt-id="schritt.id"/>
    </div>

    <div class="flex gap-2 flex-wrap">
      <UButton size="sm" color="neutral" variant="outline"
               @click="schrittAnhaengen(lauf, 'aufenthalt')">
        <UIcon name="i-lucide-plus"/>
        {{ t('ablauf.aufenthalt') }}
      </UButton>
      <UButton size="sm" color="neutral" variant="outline" @click="schrittAnhaengen(lauf, 'fahrt')">
        <UIcon name="i-lucide-chevron-right"/>
        {{ t('ablauf.fahrt') }}
      </UButton>
    </div>
  </div>
</template>
