<script setup lang="ts">
import {t} from '../i18n'
</script>

<template>
  <div class="panel text-center py-12">
    <h1 class="headline text-2xl">{{ t('nichtGefunden.titel') }}</h1>
    <UButton color="neutral" variant="outline" class="mt-4 inline-flex" to="/alarme">{{ t('nichtGefunden.zurueck') }}</UButton>
  </div>
</template>
