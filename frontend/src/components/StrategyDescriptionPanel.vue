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

    <div v-if="!readonly || attachments.length" class="block">
      <h3 class="block-title">附件</h3>
      <div
        v-if="!readonly"
        class="dropzone"
        :class="{ over: dragOver, readonly: readonly }"
        @dragenter.prevent="onDragEnter"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
        @paste="onPaste"
        tabindex="0"
      >
        <p class="drop-hint">支援 png / jpg；可拖拉、貼上圖片</p>
        <div class="attach-actions">
          <span
            class="add-icon"
            :class="{ disabled: uploading }"
            role="button"
            tabindex="0"
            aria-label="新增附件"
            @click="openAttachPicker"
            @keydown.enter.prevent="openAttachPicker"
            @keydown.space.prevent="openAttachPicker"
          >
            <svg viewBox="0 0 32 32" aria-hidden="true">
              <g>
                <path d="M16,29A13,13,0,1,1,29,16,13,13,0,0,1,16,29ZM16,5A11,11,0,1,0,27,16,11,11,0,0,0,16,5Z"/>
                <path d="M16,23a1,1,0,0,1-1-1V10a1,1,0,0,1,2,0V22A1,1,0,0,1,16,23Z"/>
                <path d="M22,17H10a1,1,0,0,1,0-2H22a1,1,0,0,1,0,2Z"/>
              </g>
            </svg>
          </span>
          <input
            ref="attachInputRef"
            class="file-input-hidden"
            type="file"
            accept="image/png,image/jpeg"
            multiple
            @change="onAttachInputChange"
          />
        </div>
      </div>

      <div v-if="attachments.length" class="gallery">
        <div v-for="a in attachments" :key="a.filename" class="thumb-card">
          <button
            v-if="!readonly"
            type="button"
            class="remove-icon"
            aria-label="刪除附件"
            @click="removeAttachment(a.filename)"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M14.59 8L12 10.59 9.41 8 8 9.41 10.59 12 8 14.59 9.41 16 12 13.41 14.59 16 16 14.59 13.41 12 16 9.41 14.59 8zM12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
            </svg>
          </button>
          <img
            class="thumb"
            :src="attachmentSrc(a.filename)"
            :alt="a.filename"
            loading="lazy"
            @click="openPreview(a.filename)"
          />
        </div>
      </div>
      <p v-else class="hint">尚無附件</p>
      <p v-if="uploading" class="hint">上傳中...</p>
    </div>

    <div v-if="previewOpen" class="preview-overlay" @click.self="closePreview">
      <div class="preview-body">
        <button type="button" class="preview-close" @click="closePreview">關閉</button>
        <div class="preview-scroll">
          <img class="preview-image" :src="previewSrc" :alt="previewName" />
        </div>
      </div>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  deleteProjectAttachment,
  getProjectAttachmentUrl,
  listProjectAttachments,
  uploadProjectAttachment
} from '../api'
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
const attachments = ref([])
const uploading = ref(false)
const dragOver = ref(false)
const attachInputRef = ref(null)
const previewOpen = ref(false)
const previewSrc = ref('')
const previewName = ref('')
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

watch(
  () => props.projectId,
  async () => {
    await loadAttachments()
  }
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

function attachmentSrc(filename) {
  return getProjectAttachmentUrl(props.projectId, filename)
}

async function loadAttachments() {
  try {
    attachments.value = await listProjectAttachments(props.projectId)
  } catch (e) {
    if (!String(e?.message || '').includes('not found')) {
      error.value = e?.message || '載入附件失敗'
    }
  }
}

function isImageFile(file) {
  if (!file) return false
  const name = String(file.name || '').toLowerCase()
  const type = String(file.type || '').toLowerCase()
  return type === 'image/png' || type === 'image/jpeg' || /\.(png|jpe?g)$/.test(name)
}

function normalizeName(name, fallbackExt = '.png') {
  const ext = /\.(png|jpe?g)$/i.test(name) ? name.match(/\.(png|jpe?g)$/i)[0] : fallbackExt
  const stem = String(name || 'image').replace(/\.[^.]+$/, '').replace(/[^A-Za-z0-9._-]+/g, '_') || 'image'
  return `${stem}${ext}`
}

function fileFromBlob(blob, nameHint) {
  const t = Date.now()
  const ext = blob.type === 'image/jpeg' ? '.jpg' : '.png'
  const fileName = normalizeName(nameHint || `paste_${t}${ext}`, ext)
  return new File([blob], fileName, { type: blob.type || 'image/png' })
}

async function uploadAttachments(files) {
  if (props.readonly) return
  const list = Array.from(files || []).filter(isImageFile)
  if (!list.length) return
  uploading.value = true
  error.value = ''
  try {
    for (const f of list) {
      await uploadProjectAttachment(props.projectId, f)
    }
    await loadAttachments()
  } catch (e) {
    error.value = e?.message || '上傳附件失敗'
  } finally {
    uploading.value = false
    dragOver.value = false
  }
}

function openAttachPicker() {
  if (props.readonly) return
  attachInputRef.value?.click()
}

function onAttachInputChange(event) {
  const files = Array.from(event.target.files || [])
  uploadAttachments(files)
  event.target.value = ''
}

function onDragEnter() {
  if (props.readonly) return
  dragOver.value = true
}

function onDragOver() {
  if (props.readonly) return
  dragOver.value = true
}

function onDragLeave() {
  if (props.readonly) return
  dragOver.value = false
}

function onDrop(event) {
  if (props.readonly) return
  const files = Array.from(event.dataTransfer?.files || [])
  uploadAttachments(files)
}

function onPaste(event) {
  if (props.readonly) return
  const items = Array.from(event.clipboardData?.items || [])
  const blobs = items
    .filter((it) => it.type === 'image/png' || it.type === 'image/jpeg')
    .map((it) => it.getAsFile())
    .filter(Boolean)
  if (!blobs.length) return
  const files = blobs.map((b, i) => fileFromBlob(b, `paste_${Date.now()}_${i}${b.type === 'image/jpeg' ? '.jpg' : '.png'}`))
  uploadAttachments(files)
}

async function removeAttachment(filename) {
  if (props.readonly) return
  if (!confirm(`刪除附件 ${filename} ?`)) return
  error.value = ''
  try {
    await deleteProjectAttachment(props.projectId, filename)
    await loadAttachments()
  } catch (e) {
    error.value = e?.message || '刪除附件失敗'
  }
}

function openPreview(filename) {
  previewName.value = filename
  previewSrc.value = attachmentSrc(filename)
  previewOpen.value = true
}

function closePreview() {
  previewOpen.value = false
}

function onKeydown(event) {
  if (event.key === 'Escape' && previewOpen.value) {
    closePreview()
  }
}

onMounted(() => {
  loadAttachments()
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }
  if (savedHintTimer) {
    clearTimeout(savedHintTimer)
    savedHintTimer = null
  }
  window.removeEventListener('keydown', onKeydown)
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
.dropzone {
  border: 1px dashed #b6c2cf;
  border-radius: 8px;
  padding: 16px 10px;
  min-height: 36px;
  background: #f8fafc;
  transition: border-color 120ms ease-in-out, background 120ms ease-in-out;
}
.dropzone:focus {
  outline: none;
  border-color: var(--accent);
}
.dropzone.over {
  border-color: var(--accent);
  background: #edf8fb;
}
.dropzone.readonly {
  background: #fbfdff;
}
.drop-hint {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}
.attach-actions {
  margin-top: 0;
  margin-bottom: 0;
}
.add-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
  transition: color 120ms ease-in-out;
}
.add-icon svg {
  width: 29px;
  height: 29px;
  fill: currentColor;
}
.add-icon:hover {
  color: var(--accent);
}
.add-icon:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--accent) 35%, #ffffff);
  outline-offset: 2px;
  border-radius: 6px;
}
.add-icon.disabled {
  opacity: 0.45;
  pointer-events: none;
}
.gallery {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}
.thumb-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  position: relative;
}
.thumb {
  width: 100%;
  height: 120px;
  object-fit: cover;
  display: block;
  background: #f1f5f9;
  cursor: zoom-in;
}
.remove-icon {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 26px;
  height: 26px;
  border: none;
  background: transparent;
  color: #dc2626;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  padding: 0;
}
.remove-icon svg {
  width: 24px;
  height: 24px;
  fill: currentColor;
}
.remove-icon:hover {
  color: #b91c1c;
}
.remove-icon:focus-visible {
  outline: 2px solid color-mix(in srgb, #dc2626 40%, #ffffff);
  outline-offset: 2px;
  border-radius: 999px;
}
.file-input-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.desc-box {
  width: 100%;
  min-height: 153px;
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
  margin: 6px 0 0;
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
.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.72);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.preview-body {
  background: #fff;
  border-radius: 10px;
  width: min(96vw, 1200px);
  height: min(92vh, 860px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.preview-close {
  align-self: flex-end;
  margin: 8px 10px 0 0;
  padding: 5px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
}
.preview-scroll {
  flex: 1;
  overflow: auto;
  padding: 8px 12px 12px;
}
.preview-image {
  display: block;
  max-width: none;
  max-height: none;
}
</style>
