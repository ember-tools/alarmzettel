<script setup lang="ts">
import {ComboboxField, TextField} from '@emberbox/ui'
import {computed, defineAsyncComponent, onBeforeUnmount, ref, watch} from 'vue'
import {t} from '../../i18n'
import {adresspunkt, suchen, type Adresspunkt, type Adressvorschlag} from '../../api/adressen'
import type {Adresse} from '../../interfaces/Alarm'

/** An address with street suggestions, lookup of the point and an optional point set on the map. */
defineProps<{ title: string }>()
const emit = defineEmits<{ resolved: [Adresspunkt] }>()
const address = defineModel<Adresse>({required: true})

/** Leaflet brings its own weight and is only loaded once someone opens the map. */
const PointPickerDialog = defineAsyncComponent(() => import('./PointPickerDialog.vue'))
const picking = ref(false)

/** A point set on the map takes precedence over the street. */
function setPoint(value: string) {
  address.value.koordinaten = value
  picking.value = false
}

const hits = ref<Adressvorschlag[]>([])
const suggestions = computed(() => hits.value.map(hit => hit.beschriftung))

let counter = 0
let timer: number | undefined

/**
 * Suggestions follow the typing, but the answers do not come back in the order they were asked
 * for. Each request carries a number and a late answer to an older one is dropped, or a slow reply
 * for "mark" would overwrite the list for "marksburg".
 */
function suggest(value: string) {
  window.clearTimeout(timer)
  timer = window.setTimeout(async () => {
    const run = ++counter
    const found = await suchen(value)
    if (run !== counter) return
    hits.value = found
  }, 200)
}

/**
 * A picked suggestion carries the whole address, so "Archenholdstr 21" typed into this one field
 * settles street, number, postcode and district together. Anything typed and left alone falls
 * back to looking up whatever the separate fields hold.
 */
function adopt() {
  const chosen = hits.value.find(hit => hit.beschriftung === address.value.strasse)
  if (!chosen) {
    void resolve()
    return
  }
  address.value.strasse = chosen.strasse
  address.value.plz = chosen.plz
  address.value.ort = chosen.ort
  if (chosen.hnr) address.value.hnr = chosen.hnr
  if (chosen.ostwert !== null && chosen.nordwert !== null) {
    emit('resolved', chosen as Adresspunkt)
  } else {
    void resolve()
  }
}

async function resolve() {
  const point = await adresspunkt(address.value.strasse, address.value.hnr, address.value.plz)
  if (!point) return
  address.value.plz = point.plz
  address.value.ort = point.ort
  emit('resolved', point)
}

watch(() => address.value.strasse, suggest)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <div>
    <div class="eyebrow mb-2">{{ title }}</div>
    <div class="grid grid-cols-3 gap-3">
      <ComboboxField v-model="address.strasse" :label="t('feld.strasse')" :suggestions="suggestions"
                     :placeholder="t('adresse.platzhalter')" wide prefiltered @change="adopt"/>
      <TextField v-model="address.hnr" :label="t('feld.hnr')" @change="resolve"/>
      <TextField v-model="address.objekt" :label="t('feld.objekt')" wide/>
      <TextField v-model="address.plz" :label="t('feld.plz')" @change="resolve"/>
      <TextField v-model="address.ort" :label="t('feld.ort')" wide/>
    </div>

    <div class="mt-2 flex flex-wrap items-center gap-2">
      <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-map-pin"
               :label="address.koordinaten ? t('adresse.punktAendern') : t('adresse.punktWaehlen')"
               @click="picking = true"/>
      <span v-if="address.koordinaten" class="tabular text-[13px] text-muted" :title="t('adresse.punktGilt')">
        {{ address.koordinaten }}
      </span>
    </div>

    <PointPickerDialog v-if="picking" v-model:open="picking" :address="address" @set="setPoint"/>
  </div>
</template>
