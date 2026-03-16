<template>
  <main class="auth-wrap">
    <section class="panel auth-card">
      <h1>{{ mode === 'login' ? 'Login' : 'Sign up' }}</h1>
      <div class="form">
        <input v-model.trim="userId" placeholder="user_id" />
        <input v-model="password" type="password" placeholder="password" @keyup.enter="submit" />
        <input
          v-if="mode === 'signup'"
          v-model="passwordConfirm"
          type="password"
          placeholder="confirm password"
          @keyup.enter="submit"
        />
        <button :disabled="loading" @click="submit">{{ mode === 'login' ? 'Login' : 'Create Account' }}</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <a href="#" @click.prevent="toggleMode">
        {{ mode === 'login' ? 'Sign up' : 'Back to login' }}
      </a>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authLogin, authSignUp } from '../api'

const router = useRouter()
const mode = ref('login')
const userId = ref('')
const password = ref('')
const passwordConfirm = ref('')
const error = ref('')
const loading = ref(false)

function toggleMode() {
  error.value = ''
  mode.value = mode.value === 'login' ? 'signup' : 'login'
  passwordConfirm.value = ''
}

async function submit() {
  if (!userId.value || !password.value) return
  if (mode.value === 'signup' && password.value !== passwordConfirm.value) {
    error.value = 'Password confirm mismatch'
    return
  }
  loading.value = true
  error.value = ''
  try {
    if (mode.value === 'signup') {
      await authSignUp(userId.value, password.value)
    }
    await authLogin(userId.value, password.value)
    await router.replace('/')
  } catch (e) {
    error.value = e.message || 'Authentication failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 16px;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 20px;
}
.form {
  display: grid;
  gap: 10px;
}
input {
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
}
button {
  padding: 10px 12px;
  border: 1px solid var(--accent);
  border-radius: 8px;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
}
.error {
  color: #b00020;
}
a {
  color: var(--accent);
}
</style>
