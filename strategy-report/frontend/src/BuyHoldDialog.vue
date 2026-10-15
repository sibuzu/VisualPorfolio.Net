<script setup>
import { onMounted, ref } from 'vue'

const props = defineProps({ settings: { type: Object, default: null } })
const emit = defineEmits(['apply', 'close'])
const dialog = ref(null)
const helpOpen = ref(false)
const error = ref('')
const form = ref({ product_type: '無', amount_wan: 100, code: '0050', leverage: 5, ...props.settings })
onMounted(() => dialog.value.showModal())

function setProduct(product) {
  if (product === '期貨' && form.value.code === '0050') form.value.code = 'TX'
  if (product === '股票' && form.value.code === 'TX') form.value.code = '0050'
  form.value.product_type = product
  error.value = ''
}

function submit() {
  if (form.value.product_type === '無') {
    emit('apply', null)
    return
  }
  const amount = Number(String(form.value.amount_wan).replaceAll(',', '').trim())
  const leverage = Number(String(form.value.leverage).replaceAll(',', '').trim())
  const code = form.value.code.trim().toUpperCase()
  if (!Number.isFinite(amount) || amount <= 0 || amount > 1000000000) {
    error.value = '金額(萬) 必須大於 0，且不超過 1,000,000,000。'
    return
  }
  if (!/^[A-Z0-9._-]{1,32}$/.test(code)) {
    error.value = '請輸入有效的商品代碼。'
    return
  }
  if (form.value.product_type === '期貨' && (!Number.isFinite(leverage) || leverage <= 0 || leverage > 100)) {
    error.value = '槓桿必須大於 0，且不超過 100。'
    return
  }
  emit('apply', { product_type: form.value.product_type, amount_wan: amount, code, leverage: form.value.product_type === '期貨' ? leverage : 5 })
}
</script>

<template>
  <dialog ref="dialog" class="buy-hold-dialog" aria-labelledby="buy-hold-title" @cancel.prevent="emit('close')">
    <form @submit.prevent="submit">
      <div class="buy-hold-title-row">
        <h4 id="buy-hold-title">Buy&amp;Hold</h4>
        <button type="button" class="copy-project-btn icon-btn" title="Buy&Hold 說明" aria-label="Buy&Hold 說明" :aria-expanded="helpOpen" @click="helpOpen = !helpOpen">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z" /></svg>
        </button>
      </div>
      <div v-if="helpOpen" class="buy-hold-help">
        <p>股票代碼如 2330、0050，配息再投資；期貨如 TX、TE、TF，依槓桿持有並轉倉。</p>
        <p>起始日自動使用指定開始日、報表開始日或第一個交易日，休市日順延至有行情的交易日。</p>
        <p>Buy&amp;Hold 使用本設定金額，不受策略資金管理影響。選擇「無」可取消參考。</p>
      </div>
      <label class="buy-hold-field"><span>金額(萬)</span><input v-model="form.amount_wan" type="text" inputmode="decimal" autocomplete="off" :disabled="form.product_type === '無'" /></label>
      <div class="buy-hold-field">
        <span>商品</span>
        <div class="product-toggle">
          <label v-for="product in ['無', '股票', '期貨']" :key="product"><input type="radio" name="buy-hold-product" :value="product" :checked="form.product_type === product" @change="setProduct(product)" /><span>{{ product }}</span></label>
        </div>
      </div>
      <label class="buy-hold-field"><span>代碼</span><input v-model="form.code" type="text" autocomplete="off" :disabled="form.product_type === '無'" /></label>
      <label v-if="form.product_type === '期貨'" class="buy-hold-field"><span>槓桿</span><input v-model="form.leverage" type="text" inputmode="decimal" autocomplete="off" /></label>
      <p v-if="error" class="error-message buy-hold-error" role="alert">{{ error }}</p>
      <div class="buy-hold-actions"><button type="button" class="copy-project-btn" @click="emit('close')">取消</button><button type="submit" class="copy-project-btn file-btn">設定</button></div>
    </form>
  </dialog>
</template>

<style scoped>
/* Same dialog geometry, typography and controls as Visual Portfolio's Buy&Hold. */
.buy-hold-dialog { width: min(360px, calc(100% - 28px)); border: 1px solid var(--line); border-radius: 8px; background: #fff; color: var(--text); padding: 12px; box-shadow: 0 18px 50px rgba(15, 23, 42, 0.22); margin: 80px auto auto; max-height: calc(100dvh - 94px); }
.buy-hold-dialog::backdrop { background: rgba(15, 23, 42, 0.35); }
.buy-hold-title-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
.buy-hold-title-row h4 { margin: 0; font-size: 18px; }
.icon-btn { width: 30px; height: 30px; display: inline-flex; align-items: center; justify-content: center; padding: 0; }
.icon-btn svg { width: 24px; height: 24px; fill: currentColor; }
.buy-hold-help { margin: 0 0 10px; color: var(--muted); font-size: 13px; line-height: 1.45; }
.buy-hold-help p { margin: 0; }
.buy-hold-help p + p { margin-top: 4px; }
.buy-hold-field { display: grid; grid-template-columns: 86px minmax(0, 1fr); align-items: center; gap: 8px; margin-bottom: 8px; font-size: 14px; }
.buy-hold-field input[type='text'] { width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 5px 7px; font-size: 14px; }
.product-toggle { display: inline-flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.product-toggle label { display: inline-flex; gap: 4px; align-items: center; }
.buy-hold-error { margin: 8px 0; font-size: 13px; }
.buy-hold-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 10px; }
.file-btn { border-color: #9aa8b8; }
</style>
