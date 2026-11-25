<script setup lang="ts">
import {usePage, webApplicationData} from '@emberbox/ui'

const DESCRIPTION = 'Alarmzettel der Berliner Feuerwehr schreiben und Übungstage planen: Einsätze erfassen, '
    + 'Einsatzmittel einteilen, Zettel als PDF drucken und gemeinsam im Browser arbeiten. Kostenlos und ohne Anmeldung.'

usePage({
  title: 'Alarmplaner – Alarmzettel schreiben und Übungstage planen',
  description: DESCRIPTION,
  path: '/info',
  structuredData: [webApplicationData({name: 'Alarmplaner', description: DESCRIPTION})],
})

const FEATURES = [
  {
    icon: 'i-lucide-clipboard-list',
    title: 'Alarme erfassen',
    text: 'Einsatz, Stichwort, Adressen, Beteiligte, Hinweise und Einsatzmittelaufgebot, mit so vielen Gruppen und Fahrzeugen wie nötig.',
  },
  {
    icon: 'i-lucide-file-text',
    title: 'Zettel als PDF',
    text: 'Ein Blatt je Alarm im Format der Berliner Feuerwehr, mit Vorschau beim Tippen, einzeln oder alle in einer Datei.',
  },
  {
    icon: 'i-lucide-map-pin',
    title: 'Adressen und Karte',
    text: 'Straße eintippen, Vorschlag wählen: Hausnummer, Postleitzahl, Ortsteil und Polarkoordinaten stehen sofort da.',
  },
  {
    icon: 'i-lucide-list-checks',
    title: 'Strukturierte Abfrage',
    text: 'Statt den Code nachzuschlagen, klickt man sich durch die Fragen; der Weg wird zum Hinweis auf dem Zettel.',
  },
  {
    icon: 'i-lucide-calendar-range',
    title: 'Übungstage planen',
    text: 'Wer wann wo ist, in welchem Fahrzeug und wer fährt, als Kette je Fahrzeug und Person, mit Prüfung und Blättern zum Mitnehmen.',
  },
  {
    icon: 'i-lucide-share-2',
    title: 'Gemeinsam arbeiten',
    text: 'Eine Sitzung bekommt einen Link zum Mitarbeiten und einen, der nur zusehen lässt.',
  },
]
</script>

<template>
  <div class="mx-auto flex max-w-5xl flex-col gap-10 py-4">
    <section class="flex max-w-3xl flex-col gap-3">
      <p class="eyebrow">Alarmplaner</p>
      <h1 class="headline m-0 text-4xl md:text-5xl">Alarmzettel schreiben und Übungstage planen</h1>
      <p class="m-0 text-lg text-muted">{{ DESCRIPTION }}</p>
      <div class="flex flex-wrap gap-2">
        <UButton to="/" icon="i-lucide-arrow-right" trailing label="Alarmplaner öffnen"/>
        <UButton to="/hilfe" color="neutral" variant="outline" icon="i-lucide-life-buoy" label="Hilfe"/>
      </div>
    </section>

    <section aria-labelledby="features" class="flex flex-col gap-4">
      <h2 id="features" class="eyebrow m-0">Was der Alarmplaner kann</h2>
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <UCard v-for="feature in FEATURES" :key="feature.title">
          <div class="flex flex-col gap-2">
            <UIcon :name="feature.icon" class="size-6 text-signal"/>
            <h3 class="headline m-0 text-xl">{{ feature.title }}</h3>
            <p class="m-0 text-muted">{{ feature.text }}</p>
          </div>
        </UCard>
      </div>
    </section>

    <section class="flex max-w-3xl flex-col gap-2">
      <h2 class="eyebrow m-0">Für wen</h2>
      <p class="m-0">
        Für Jugendfeuerwehren und Einsatzabteilungen, die Übungstage vorbereiten: die Alarmzettel für jede Einsatzübung
        und den Ablauf drumherum an einem Ort. Die Daten bleiben im Browser; nur eine geteilte Sitzung liegt
        zusätzlich auf dem Server.
      </p>
    </section>
  </div>
</template>
