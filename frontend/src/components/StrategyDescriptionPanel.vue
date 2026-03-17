<template>
  <section class="panel-wrap">
    <div class="block">
      <h3 class="block-title">設定</h3>
      <label class="setting-item">
        <input
          v-model="neverExpires"
          type="checkbox"
          :disabled="readonly || settingSaving"
          @change="onToggleNeverExpires"
        />
        <span>never expires</span>
      </label>
    </div>

    <div class="block">
      <h3 class="block-title">說明</h3>
      <textarea
        v-model="draft"
        class="desc-box"
        :readonly="readonly"
        placeholder="請輸入策略說明..."
        @input="onInput"
      ></textarea>
      <p v-if="saving" class="hint">儲存中...</p>
      <p v-else-if="savedOk" class="hint ok">已儲存</p>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { onBeforeUnmount, ref, watch } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  readonly: { type: Boolean, default: false },
  projectId: { type: String, required: true }
})

const portfolioStore = usePortfolioStore()
const projectStore = useProjectStore()
const { strategyDescription } = storeToRefs(portfolioStore)
const { activeProject } = storeToRefs(projectStore)

const draft = ref('')
const neverExpires = ref(false)
const saving = ref(false)
const settingSaving = ref(false)
const savedOk = ref(false)
const error = ref('')
let saveTimer = null
let savedHintTimer = null

watch(
  strategyDescription,
  (value) => {
    const next = String(value || '')
    if (next !== draft.value) {
      draft.value = next
    }
  },
  { immediate: true }
)

watch(
  activeProject,
  (p) => {
    neverExpires.value = !!p?.never_expires
  },
  { immediate: true }
)

function onInput() {
  if (props.readonly) return
  savedOk.value = false
  portfolioStore.setStrategyDescription(draft.value)
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    saving.value = true
    error.value = ''
    try {
      await portfolioStore.saveProjectPfo(props.projectId)
      savedOk.value = true
      if (savedHintTimer) clearTimeout(savedHintTimer)
      savedHintTimer = setTimeout(() => {
        savedOk.value = false
      }, 1200)
    } catch (e) {
      error.value = e?.message || '儲存策略說明失敗'
    } finally {
      saving.value = false
    }
  }, 500)
}

async function onToggleNeverExpires() {
  if (props.readonly) return
  settingSaving.value = true
  error.value = ''
  try {
    await projectStore.patchProject(props.projectId, { never_expires: !!neverExpires.value })
    await projectStore.loadProjects()
  } catch (e) {
    neverExpires.value = !!activeProject.value?.never_expires
    error.value = e?.message || '更新設定失敗'
  } finally {
    settingSaving.value = false
  }
}

onBeforeUnmount(() => {
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }
  if (savedHintTimer) {
    clearTimeout(savedHintTimer)
    savedHintTimer = null
  }
})
</script>

<style scoped>
.panel-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.block {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}
.block-title {
  margin: 0 0 8px 0;
  font-size: 18px;
}
.setting-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}
.desc-box {
  width: 100%;
  min-height: 230px;
  resize: vertical;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px;
  line-height: 1.55;
  font-size: 16px;
  background: #fff;
  color: #0f172a;
  overflow: auto;
}
.desc-box:focus {
  outline: 2px solid color-mix(in srgb, var(--accent) 28%, #ffffff);
  border-color: var(--accent);
}
.hint {
  color: var(--muted);
  margin: 0;
  font-size: 13px;
}
.hint.ok {
  color: #2563eb;
}
.error {
  color: #b42318;
  margin: 0;
  font-size: 13px;
}
</style>
