<script setup lang="ts">
import SchrittFelder from './SchrittFelder.vue'
import {t} from '../../i18n'
import {entfernen, mehrereTage} from '../../store/planung'
import {tagVon, uhrzeit} from '../../scripts/zeit'
import type {Lauf, Schritt} from '../../interfaces/Planung'

/** Ein Schritt zum Ändern, über dem Tagesplan. Dieselben Felder wie in der Kette. */
const {lauf, schritt, name} = defineProps<{ lauf: Lauf, schritt: Schritt, name: string }>()
const meldet = defineEmits<{ schliessen: [] }>()

function wegwerfen() {
  entfernen(lauf.schritte, schritt)
  meldet('schliessen')
}
</script>

<template>
  <UModal :open="true" :title="name" :ui="{content: 'sm:max-w-3xl'}"
          @update:open="(open: boolean) => !open && meldet('schliessen')">
    <template #description>
      <span class="tabular">
        <span v-if="mehrereTage()">{{ tagVon(schritt.von) }} </span>
        {{ uhrzeit(schritt.von) }}–{{ uhrzeit(schritt.bis) }}
      </span>
    </template>
    <template #body>
      <SchrittFelder :lauf="lauf" :schritt="schritt"/>
    </template>
    <template #footer>
      <div class="flex w-full flex-wrap justify-end gap-2">
          <UButton size="sm" color="signal" variant="outline" @click="wegwerfen">
            <UIcon name="i-lucide-trash-2"/>
            {{ t('ablauf.schrittEntfernen') }}
          </UButton>
          <UButton size="sm" color="neutral" variant="outline" @click="meldet('schliessen')">
            <UIcon name="i-lucide-x"/>
            {{ t('aktion.schliessen') }}
          </UButton>
      </div>
    </template>
  </UModal>
</template>
