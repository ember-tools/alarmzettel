<script setup lang="ts">
import {HelpPage, HelpSection, HelpTopic, usePage} from '@emberbox/ui'
import {t} from '../i18n'

usePage({
  title: t('help.pageTitle'),
  description: t('help.description'),
  path: '/hilfe',
})

/**
 * The numbered paragraphs of a help topic, by its catalogue key under `help`.
 *
 * @param topic the topic's key, such as `alarms.create`
 * @param count how many paragraphs it has
 * @returns the paragraphs
 */
function paragraphs(topic: string, count: number): string[] {
  return Array.from({length: count}, (_, index) => t(`help.${topic}.${index + 1}`))
}
</script>

<template>
  <HelpPage :title="t('help.title')" back="/info">
    <HelpSection :title="t('help.overview.title')">
      <HelpTopic :paragraphs="paragraphs('overview', 2)"/>
    </HelpSection>

    <HelpSection :title="t('help.alarms.title')">
      <HelpTopic :title="t('help.alarms.create.title')" :paragraphs="paragraphs('alarms.create', 2)"/>
      <HelpTopic :title="t('help.alarms.addresses.title')" :paragraphs="paragraphs('alarms.addresses', 2)"/>
      <HelpTopic :title="t('help.alarms.vehicles.title')" :paragraphs="paragraphs('alarms.vehicles', 1)"/>
      <HelpTopic :title="t('help.alarms.printing.title')" :paragraphs="paragraphs('alarms.printing', 1)"/>
    </HelpSection>

    <HelpSection :title="t('help.catalogues.title')">
      <HelpTopic :paragraphs="paragraphs('catalogues', 2)"/>
    </HelpSection>

    <HelpSection :title="t('help.schedule.title')">
      <HelpTopic :paragraphs="paragraphs('schedule', 3)"/>
    </HelpSection>

    <HelpSection :title="t('help.together.title')">
      <HelpTopic :paragraphs="paragraphs('together', 2)"/>
    </HelpSection>
  </HelpPage>
</template>
