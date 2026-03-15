<template>
  <section>
    <h3>Diversity</h3>
    <pre>{{ formatted }}</pre>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'

const { analysis } = storeToRefs(usePortfolioStore())
const formatted = computed(() => JSON.stringify(analysis.value.diversity, null, 2))
</script>
