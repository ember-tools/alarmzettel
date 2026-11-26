<script setup lang="ts">
import {breadcrumbData, HelpPage, helpPath, HelpSection, HelpTopic, usePage} from '@emberbox/ui'
import {computed} from 'vue'
import {HELP_CONTENT, helpTopicInfos, paragraphs} from '../helpContent'
import type {HelpSlug} from '../helpTopics'
import {t} from '../i18n'

/** One page of the help center; the router only comes here for a known slug. */
const props = defineProps<{ slug: HelpSlug }>()

const topics = helpTopicInfos()
const topic = computed(() => topics.find(candidate => candidate.slug === props.slug)!)

usePage(() => ({
  title: t('help.topicPageTitle', {topic: topic.value.title}),
  description: topic.value.description,
  path: helpPath(topic.value.slug),
  structuredData: [breadcrumbData([
    {name: t('app.name'), path: '/'},
    {name: t('help.title'), path: helpPath()},
    {name: topic.value.title, path: helpPath(topic.value.slug)},
  ])],
}))
</script>

<template>
  <HelpPage :title="topic.title" :topics="topics" :current="topic.slug">
    <HelpSection>
      <HelpTopic v-for="block in HELP_CONTENT[props.slug]" :key="block.topic" :paragraphs="paragraphs(block.topic, block.count)"/>
    </HelpSection>
  </HelpPage>
</template>
