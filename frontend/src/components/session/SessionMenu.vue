<script setup lang="ts">
import {ref} from 'vue'
import {t} from '../../i18n'
import {neueSitzung, sitzung, sitzungVergessen, sitzungWechseln} from '../../store/sitzung'

/**
 * Whether the list of known sessions is open. The header's other actions, such as sharing, go
 * into the default slot between the new-session button and this list.
 */
const wechsler = ref(false)
const arbeitet = ref(false)

/** Der Tag, an dem diese Sitzung verschwindet, wenn sie niemand öffnet. */
function laeuftAb(): string {
  return sitzung.laeuftAb ? new Date(sitzung.laeuftAb).toLocaleDateString('de-DE') : ''
}

async function tun(was: () => Promise<void>) {
  arbeitet.value = true
  try {
    await was()
    wechsler.value = false
  } finally {
    arbeitet.value = false
  }
}
</script>

<template>
  <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-plus" :loading="arbeitet"
           :title="t('sitzung.neuTitel')" @click="tun(neueSitzung)">
    <span class="hidden md:inline">{{ t('sitzung.neu') }}</span>
  </UButton>

  <slot/>

  <UPopover v-model:open="wechsler">
    <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-refresh-cw">
      <span class="hidden md:inline">{{ t('sitzung.wechseln') }}</span>
    </UButton>
    <template #content>
      <ul class="m-0 grid w-[min(22rem,90vw)] list-none gap-0.5 p-1" role="listbox">
        <li v-if="!sitzung.bekannt.length" class="px-2 py-1.5 text-sm text-muted">{{ t('sitzung.keine') }}</li>
        <li v-for="eintrag in sitzung.bekannt" :key="eintrag.token" role="option"
            :aria-selected="eintrag.token === sitzung.token"
            class="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-elevated"
            :class="eintrag.token === sitzung.token ? 'font-semibold' : ''">
          <button type="button" class="grow cursor-pointer text-left" @click="tun(() => sitzungWechseln(eintrag.token))">
            {{ eintrag.beschriftung }}
          </button>
          <UButton size="xs" color="neutral" variant="ghost" icon="i-lucide-x" :aria-label="t('sitzung.entfernen')"
                   @click.stop="sitzungVergessen(eintrag.token)"/>
        </li>
        <li v-if="sitzung.laeuftAb" class="px-2 py-1.5 text-[12px] text-muted">
          {{ t('sitzung.laeuftAb', {datum: laeuftAb()}) }}
        </li>
      </ul>
    </template>
  </UPopover>
</template>
