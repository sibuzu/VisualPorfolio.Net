<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ modelValue: { type: String, default: '' }, label: String, disabled: Boolean })
const emit = defineEmits(['update:modelValue'])
const draft = ref('')
const field = ref(null)
const picker = ref(null)
watch(() => props.modelValue, value => {
  draft.value = (value || '').replaceAll('-', '/')
  field.value?.setCustomValidity('')
}, { immediate: true })

function commit() {
  const value = draft.value.trim().replaceAll('-', '/')
  const parts = value.match(/^(\d{4})\/(\d{2})\/(\d{2})$/)
  const iso = value.replaceAll('/', '-')
  const date = new Date(`${iso}T00:00:00`)
  if (value && (!parts || Number(parts[1]) < 1 || date.getFullYear() !== Number(parts[1])
    || date.getMonth() + 1 !== Number(parts[2]) || date.getDate() !== Number(parts[3]))) {
    field.value.setCustomValidity('請輸入有效日期，格式為 yyyy/mm/dd。')
    field.value.reportValidity()
    return
  }
  field.value.setCustomValidity('')
  draft.value = value
  emit('update:modelValue', iso)
}

function selectDate(event) {
  draft.value = event.target.value.replaceAll('-', '/')
  field.value.setCustomValidity('')
  emit('update:modelValue', event.target.value)
}
</script>

<template>
  <span class="report-date-input" :class="{ disabled }">
    <input ref="field" v-model="draft" type="text" :aria-label="label" placeholder="yyyy/mm/dd"
      :disabled="disabled" maxlength="10" autocomplete="off" spellcheck="false"
      @input="field.setCustomValidity('')" @change="commit" @keydown.enter.prevent="commit" />
    <button type="button" :disabled="disabled" :aria-label="`${label}：選擇日期`" title="選擇日期" @click="picker.showPicker()">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 4h-1V2h-2v2H8V2H6v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 16H5V9h14zM7 11h5v5H7z" /></svg>
    </button>
    <input ref="picker" class="native-date-picker" type="date" :value="modelValue" :disabled="disabled"
      tabindex="-1" aria-hidden="true" @change="selectDate" />
  </span>
</template>

<style scoped>
.report-date-input { display: inline-flex; position: relative; width: 96px; min-width: 0; }
.report-date-input > input[type='text'] { width: 100%; min-width: 0; border: 1px solid var(--line); border-radius: 6px; padding: 4px 22px 4px 4px; font-size: 12px; color: var(--text); background: white; }
.report-date-input.disabled { opacity: .5; }
.report-date-input button { position: absolute; right: 2px; top: 0; bottom: 0; display: inline-flex; align-items: center; justify-content: center; width: 18px; padding: 0; border: 0; background: transparent; color: var(--text); }
.report-date-input svg { width: 14px; height: 14px; fill: currentColor; }
.native-date-picker { position: absolute; right: 0; bottom: 0; width: 1px; height: 1px; padding: 0; border: 0; opacity: 0; pointer-events: none; }
</style>
