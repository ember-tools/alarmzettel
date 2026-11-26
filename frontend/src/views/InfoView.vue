<script setup lang="ts">
import {usePage, webApplicationData} from '@emberbox/ui'
import {t} from '../i18n'

usePage({
  title: `${t('app.name')} – ${t('app.untertitel')}`,
  description: t('info.description'),
  path: '/info',
  structuredData: [webApplicationData({name: t('app.name'), description: t('info.description')})],
})

/** What the page names as the tool's parts, by their catalogue keys under `info.features`. */
const FEATURES = [
  {key: 'alarms', icon: 'i-lucide-clipboard-list'},
  {key: 'pdf', icon: 'i-lucide-file-text'},
  {key: 'addresses', icon: 'i-lucide-map-pin'},
  {key: 'guidedQuery', icon: 'i-lucide-list-checks'},
  {key: 'schedule', icon: 'i-lucide-calendar-range'},
  {key: 'together', icon: 'i-lucide-share-2'},
] as const
</script>

<template>
  <div class="mx-auto flex max-w-5xl flex-col gap-10 py-4">
    <section class="flex max-w-3xl flex-col gap-3">
      <p class="eyebrow">{{ t('app.name') }}</p>
      <h1 class="headline m-0 text-4xl md:text-5xl">{{ t('app.untertitel') }}</h1>
      <p class="m-0 text-lg text-muted">{{ t('info.description') }}</p>
      <div class="flex flex-wrap gap-2">
        <UButton to="/" icon="i-lucide-arrow-right" trailing :label="t('info.open')"/>
        <UButton to="/hilfe" color="neutral" variant="outline" icon="i-lucide-life-buoy" :label="t('nav.hilfe')"/>
      </div>
    </section>

    <section aria-labelledby="features" class="flex flex-col gap-4">
      <h2 id="features" class="eyebrow m-0">{{ t('info.featuresTitle') }}</h2>
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <UCard v-for="feature in FEATURES" :key="feature.key">
          <div class="flex flex-col gap-2">
            <UIcon :name="feature.icon" class="size-6 text-signal"/>
            <h3 class="headline m-0 text-xl">{{ t(`info.features.${feature.key}.title`) }}</h3>
            <p class="m-0 text-muted">{{ t(`info.features.${feature.key}.text`) }}</p>
          </div>
        </UCard>
      </div>
    </section>

    <section class="flex max-w-3xl flex-col gap-2">
      <h2 class="eyebrow m-0">{{ t('info.audienceTitle') }}</h2>
      <p class="m-0">{{ t('info.audience') }}</p>
    </section>
  </div>
</template>
