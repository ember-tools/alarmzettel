<script setup lang="ts">
import {nextTick, onBeforeUnmount, ref, watch} from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {t} from '../../i18n'
import {markeAlsText, markeAusText, mitte, utm33ZuWgs84} from '../../scripts/geo'
import type {Ortsmarke} from '../../scripts/geo'
import {zuPunkt} from '../../api/adressen'
import type {Adresse} from '../../interfaces/Alarm'
import {MAP_LIMITS, TILE_LAYER_OPTIONS, TILE_URL} from '../../scripts/tiles'

/**
 * Sets a point on the map, for everything without a house number: the yard behind the house, the
 * meadow, the meeting point at the edge of the forest. A point set here takes precedence over the
 * street. The map opens where something already is: at the set point, otherwise at the looked-up
 * address, otherwise over Berlin.
 */
const {address} = defineProps<{ address: Adresse }>()
const open = defineModel<boolean>('open', {required: true})
const emit = defineEmits<{ set: [value: string] }>()

const container = ref<HTMLElement>()
const chosen = ref<Ortsmarke | null>(null)
let map: L.Map | undefined
let marker: L.Marker | undefined

function place(point: Ortsmarke) {
  chosen.value = point
  const position: L.LatLngExpression = [point.breite, point.laenge]
  if (marker) marker.setLatLng(position)
  else if (map) {
    marker = L.marker(position, {draggable: true}).addTo(map)
    marker.on('dragend', () => {
      const where = marker!.getLatLng()
      chosen.value = {breite: where.lat, laenge: where.lng}
    })
  }
}

/** Where the address lies as far as the service knows it, only as the map's starting point. */
async function lookedUp(): Promise<Ortsmarke | null> {
  const point = await zuPunkt({...address, koordinaten: ''})
  return point ? utm33ZuWgs84(point) : null
}

async function showMap() {
  chosen.value = markeAusText(address.koordinaten ?? '')
  const start = chosen.value ?? await lookedUp()
  await nextTick()
  if (!container.value) return
  const center = start ?? mitte([])
  map = L.map(container.value, MAP_LIMITS).setView([center.breite, center.laenge], start ? 17 : 11)
  L.tileLayer(TILE_URL, TILE_LAYER_OPTIONS).addTo(map)
  if (chosen.value) place(chosen.value)
  map.on('click', (event: L.LeafletMouseEvent) => place({breite: event.latlng.lat, laenge: event.latlng.lng}))
}

function removeMap() {
  map?.remove()
  map = undefined
  marker = undefined
}

watch(open, isOpen => isOpen ? void showMap() : removeMap(), {immediate: true})
onBeforeUnmount(removeMap)
</script>

<template>
  <UModal v-model:open="open" :title="t('adresse.punktTitel')" :description="t('adresse.punktHinweis')"
          :ui="{content: 'sm:max-w-3xl'}">
    <template #body>
      <div ref="container" class="h-[55vh] min-h-72 rounded-sm border border-default" />
    </template>
    <template #footer>
      <div class="flex w-full flex-wrap items-center gap-3">
        <span class="tabular text-sm">{{ chosen ? markeAlsText(chosen) : t('adresse.punktKeiner') }}</span>
        <span class="grow" />
        <UButton v-if="address.koordinaten" size="sm" color="signal" variant="outline" icon="i-lucide-trash-2"
                 :label="t('adresse.punktLoeschen')" @click="emit('set', '')"/>
        <UButton size="sm" icon="i-lucide-check" :disabled="!chosen" :label="t('adresse.punktSetzen')"
                 @click="emit('set', chosen ? markeAlsText(chosen) : '')"/>
      </div>
    </template>
  </UModal>
</template>
