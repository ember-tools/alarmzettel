<script setup lang="ts">
import {HelpPage, HelpSection, HelpTopic, usePage} from '@emberbox/ui'

usePage({
  title: 'Hilfe – Alarmplaner',
  description: 'So schreibt man im Alarmplaner Alarmzettel, pflegt Kataloge, plant Übungstage und arbeitet gemeinsam.',
  path: '/hilfe',
})
</script>

<template>
  <HelpPage title="Hilfe zum Alarmplaner" back="/info">
    <HelpSection title="Überblick">
      <HelpTopic :paragraphs="[
        'Der Alarmplaner schreibt die Alarmzettel der Berliner Feuerwehr für Einsatzübungen und plant auf Wunsch den Übungstag drumherum.',
        'Alles, was du eingibst, liegt in einer Arbeitsmappe in deinem Browser. Wer gemeinsam arbeiten will, legt eine Sitzung an; dann liegt die Arbeitsmappe zusätzlich auf dem Server.',
      ]"/>
    </HelpSection>

    <HelpSection title="Alarme">
      <HelpTopic title="Einen Alarm anlegen" :paragraphs="[
        'Unter „Alarme“ legst du einen neuen Alarm an, duplizierst oder löschst ihn und änderst die Reihenfolge.',
        'Der Editor ist wie der Zettel gegliedert: Einsatz, Stichwort, Adressen, Karte, Beteiligte, Hinweise und Einsatzmittelaufgebot.',
      ]"/>
      <HelpTopic title="Adressen" :paragraphs="[
        'Tippe Straße und Hausnummer in das Straßenfeld, zum Beispiel „Archenholdstr 21“, und wähle den Vorschlag. Hausnummer, Postleitzahl und Ortsteil werden übernommen, die Polarkoordinaten von der Wache aus berechnet.',
        'Für Orte ohne Hausnummer setzt du einen Punkt auf der Karte; er gilt dann vor der Straße.',
      ]"/>
      <HelpTopic title="Einsatzmittel" :paragraphs="[
        'Ein Alarm hat beliebig viele Gruppen mit beliebig vielen Fahrzeugen. Genau ein Fahrzeug ist das, an das der Zettel gerichtet ist; es wird grau hinterlegt gedruckt.',
      ]"/>
      <HelpTopic title="Drucken" :paragraphs="[
        'Die Vorschau zeigt den Zettel so, wie er gedruckt wird. Als PDF lädst du jeden Alarm einzeln oder alle in einer Datei herunter.',
      ]"/>
    </HelpSection>

    <HelpSection title="Kataloge">
      <HelpTopic :paragraphs="[
        'In den Katalogen steht, was die Wache hat: Stichwörter, Fahrzeuge, Orte, Material, Status und Trupp, die Tage der Veranstaltung und die Personen mit Funktionen und Führerscheinklassen.',
        'Ein Alarm verweist auf Stichwort und Fahrzeug, statt sie zu kopieren. Eine Korrektur im Katalog ändert also jeden Zettel, der sie benutzt.',
      ]"/>
    </HelpSection>

    <HelpSection title="Ablauf">
      <HelpTopic :paragraphs="[
        'Die Ablaufplanung ist zuschaltbar. Ein Übungstag wird als Kette je Fahrzeug und je Person geplant; jeder Schritt beginnt dort, wo der vorige endet.',
        'Der Plan prüft unter anderem Sitzplätze, Fahrten ohne Fahrer, Personen an zwei Stellen zugleich und Fahrten, die viel kürzer geplant sind als geschätzt. Nichts davon blockiert die Eingabe.',
        'Jede Person und jedes Fahrzeug bekommt ein eigenes Blatt mit dem Tagesablauf, verlinkbar über die Sitzung.',
      ]"/>
    </HelpSection>

    <HelpSection title="Gemeinsam arbeiten">
      <HelpTopic :paragraphs="[
        'Über „Teilen“ bekommst du zwei Links: einen zum Mitarbeiten und einen, der nur zusehen lässt.',
        'Wer den Link zum Mitarbeiten öffnet, arbeitet entweder an einer eigenen Kopie oder mit allen anderen an derselben Arbeitsmappe. Eine Sitzung wird 30 Tage nach ihrer letzten Nutzung gelöscht.',
      ]"/>
    </HelpSection>
  </HelpPage>
</template>
