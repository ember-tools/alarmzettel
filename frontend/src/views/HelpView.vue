<script setup lang="ts">
import {HelpIndex, HelpPage, HelpSection, HelpTopic, usePage} from '@emberbox/ui'
import {helpTopicInfos, paragraphs} from '../helpContent'
import {t} from '../i18n'

usePage({
  title: t('help.pageTitle'),
  description: t('help.description'),
  path: '/hilfe',
})
</script>

<template>
  <HelpPage :title="t('help.title')" back="/">
    <HelpSection :title="t('help.overview.title')">
      <HelpTopic :paragraphs="paragraphs('overview', 2)"/>
    </HelpSection>
    <HelpIndex :topics="helpTopicInfos()"/>
  </HelpPage>
</template>
