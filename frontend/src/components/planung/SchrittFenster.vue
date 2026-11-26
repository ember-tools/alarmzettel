<script setup lang="ts">
import {computed, watch} from 'vue'
import SchrittFelder from './SchrittFelder.vue'
import {t} from '../../i18n'
import {arbeitsmappe} from '../../store/arbeitsmappe'
import {entfernen, mehrereTage} from '../../store/planung'
import {tagVon, uhrzeit} from '../../scripts/zeit'

/**
 * A step to edit, above the day plan, with the same fields as in the chain. The step is given by
 * id and looked up in the workbook, so the window always shows the current state; when the step
 * or its chain disappears, for example because someone else in the session deleted it, the window
 * closes.
 */
const {laufId, schrittId, name} = defineProps<{ laufId: string, schrittId: string, name: string }>()
const meldet = defineEmits<{ schliessen: [] }>()

const lauf = computed(() => arbeitsmappe.planung.laeufe.find(kette => kette.id === laufId))
const schritt = computed(() => lauf.value?.schritte.find(eintrag => eintrag.id === schrittId))

watch(schritt, aktuell => {
  if (!aktuell) meldet('schliessen')
})

function wegwerfen() {
  if (lauf.value && schritt.value) entfernen(lauf.value.schritte, schritt.value)
  meldet('schliessen')
}
</script>

<template>
  <UModal :open="true" :title="name" :ui="{content: 'sm:max-w-3xl'}"
          @update:open="(open: boolean) => !open && meldet('schliessen')">
    <template #description>
      <span v-if="schritt" class="tabular">
        <span v-if="mehrereTage()">{{ tagVon(schritt.von) }} </span>
        {{ uhrzeit(schritt.von) }}–{{ uhrzeit(schritt.bis) }}
      </span>
    </template>
    <template #body>
      <SchrittFelder v-if="lauf && schritt" :lauf-id="laufId" :schritt-id="schrittId"/>
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
