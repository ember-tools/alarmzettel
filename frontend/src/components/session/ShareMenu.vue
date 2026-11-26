<script setup lang="ts">
import {copyToClipboard} from '@emberbox/ui'
import {computed, ref} from 'vue'
import {lesetoken} from '../../api/sitzung'
import {t} from '../../i18n'
import {personenplan} from '../../scripts/ablauf'
import {arbeitsmappe} from '../../store/arbeitsmappe'
import {plandaten} from '../../store/planung'
import {sitzung} from '../../store/sitzung'
import {jetztAbgleichen} from '../../store/sync'

/** Whether the share menu is open; opening it exchanges first and fetches the read link. */
const teiler = ref(false)
const nurLesenToken = ref<string | null>(null)
const kopiert = ref<string | null>(null)

/** Ein Link auf diese Sitzung, so wie dieser Browser sie erreicht. */
function linkAuf(token: string | null): string {
  return token ? `${window.location.origin}/sitzung/${token}` : ''
}

/**
 * Teilen heißt hier: den Link weitergeben. Vorher wird abgeglichen, damit der andere den Stand
 * sieht, den alle haben. Der Lesen-Link entsteht beim ersten Öffnen dieses Menüs und bleibt
 * danach derselbe – wer eine Sitzung nur ansieht, kann keinen erzeugen und braucht auch keinen.
 */
async function teilen() {
  teiler.value = !teiler.value
  kopiert.value = null
  if (!teiler.value || !sitzung.token || sitzung.nurLesen) return
  await jetztAbgleichen()
  try {
    nurLesenToken.value = await lesetoken(sitzung.token)
  } catch {
    nurLesenToken.value = null
  }
}

/**
 * Ein Link je Zettel: wer ihn bekommt, sieht seinen Tag und sonst nichts. Aufgeführt wird, wer
 * auch ein Blatt bekäme – jede Person mit einem Plan und jedes Fahrzeug mit einer Kette.
 */
const blaetter = computed(() => {
  const token = nurLesenToken.value ?? (sitzung.nurLesen ? sitzung.token : null)
  if (!token || !arbeitsmappe.planung.aktiv) return []
  const daten = plandaten()
  const zeilen: {name: string, link: string}[] = []
  for (const person of arbeitsmappe.kataloge.personen) {
    if (person.blatt === false || !personenplan(daten, person.id).length) continue
    zeilen.push({name: person.name || t('ablauf.ohneName'),
                 link: `${window.location.origin}/blatt/${token}/person/${person.id}`})
  }
  for (const fahrzeug of arbeitsmappe.kataloge.fahrzeuge) {
    const kette = arbeitsmappe.planung.laeufe.find(lauf => lauf.fahrzeugId === fahrzeug.id)
    if (!kette?.schritte.length) continue
    zeilen.push({name: fahrzeug.funkrufname || t('ablauf.ohneName'),
                 link: `${window.location.origin}/blatt/${token}/fahrzeug/${fahrzeug.id}`})
  }
  return zeilen
})

const blattliste = computed(() =>
    blaetter.value.map(blatt => `${blatt.name} – ${blatt.link}`).join('\n'))

/** Copies a link; when even the fallback fails, the link stays on screen to be selected by hand. */
async function kopieren(link: string) {
  if (await copyToClipboard(link)) kopiert.value = link
}
</script>

<template>
  <UPopover :open="teiler" @update:open="(isOpen: boolean) => isOpen ? teilen() : (teiler = false)">
    <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-share-2" :title="t('freigabe.teilenTitel')">
      <span class="hidden md:inline">{{ t('freigabe.teilen') }}</span>
    </UButton>
    <template #content>
      <div class="grid w-[min(24rem,90vw)] gap-3 p-3">
        <UFormField v-if="!sitzung.nurLesen" :label="t('freigabe.zumMitarbeiten')">
          <UFieldGroup class="w-full">
            <UInput class="w-full" size="sm" readonly :model-value="linkAuf(sitzung.token)"
                    @focus="($event.target as HTMLInputElement).select()"/>
            <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-copy"
                     :aria-label="t('freigabe.kopieren')" @click="kopieren(linkAuf(sitzung.token))"/>
          </UFieldGroup>
        </UFormField>

        <UFormField :label="t('freigabe.zumAnsehen')" :help="t('freigabe.zumAnsehenHinweis')">
          <UFieldGroup class="w-full">
            <UInput class="w-full" size="sm" readonly
                    :model-value="sitzung.nurLesen ? linkAuf(sitzung.token) : (nurLesenToken ? linkAuf(nurLesenToken) : '…')"
                    @focus="($event.target as HTMLInputElement).select()"/>
            <UButton size="sm" color="neutral" variant="outline" icon="i-lucide-copy"
                     :aria-label="t('freigabe.kopieren')" :disabled="!sitzung.nurLesen && !nurLesenToken"
                     @click="kopieren(linkAuf(sitzung.nurLesen ? sitzung.token : nurLesenToken))"/>
          </UFieldGroup>
        </UFormField>

        <div v-if="blaetter.length" class="border-t border-default pt-3">
          <UFormField :label="t('blatt.titel')" :help="t('blatt.hinweisLinks')">
            <UTextarea class="tabular w-full" size="sm" :rows="4" readonly :model-value="blattliste"
                       @focus="($event.target as HTMLTextAreaElement).select()"/>
          </UFormField>
          <UButton class="mt-2" size="sm" color="neutral" variant="outline" icon="i-lucide-copy"
                   :label="t('blatt.kopieren')" @click="kopieren(blattliste)"/>
        </div>

        <p v-if="kopiert" class="m-0 text-[12px]">{{ t('freigabe.kopiert') }}</p>
      </div>
    </template>
  </UPopover>
</template>
