<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../store'
import JSEncrypt from 'jsencrypt'
import { useI18n } from '../i18n'

const router = useRouter()
const { t } = useI18n()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const publicKey = ref('')
const isBanned = ref(false)
const banScreenHtml = ref('')

onMounted(async () => {
  try {
    const res = await fetch('/api/auth/public-key')
    if (res.ok) {
      const data = await res.json()
      publicKey.value = data.public_key
    }
  } catch (e) {
    console.error("Failed to load public key", e)
  }
})

const handleLogin = async () => {
  if (!username.value || !password.value) {
    error.value = t('common.loginTitle') // Reusing as placeholder for now, better to add specific error msg
    return
  }

  loading.value = true
  error.value = ''
  
  try {
    let finalPassword = password.value
    
    if (publicKey.value) {
      const encryptor = new JSEncrypt()
      encryptor.setPublicKey(publicKey.value)
      const encrypted = encryptor.encrypt(password.value)
      if (!encrypted) {
        throw new Error("加密失败，请刷新重试")
      }
      finalPassword = encrypted
    } else {
      console.warn("Public key not found, sending plaintext (not recommended)")
    }

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        identity: username.value,
        password: finalPassword
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      if (response.status === 403 && data.detail === "Account Banned") {
          isBanned.value = true
          banScreenHtml.value = data.ban_screen
          return
      }

      // Translate common errors
      let msg = data.detail || '登录失败'
      if (msg.includes("Invalid password")) msg = "密码错误或加密失效"
      if (msg.includes("User not found")) msg = "用户不存在"
      throw new Error(msg)
    }

    // Success
    console.log('Login successful:', data)
    
    // Update global auth state
    login(data)

    // Redirect to home
    router.push('/')

  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-if="isBanned" class="fixed inset-0 bg-gray-900 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden">
          <div class="p-8 prose prose-red max-w-none" v-html="banScreenHtml"></div>
          <div class="bg-gray-50 px-8 py-4 border-t border-gray-100 text-right">
              <button @click="isBanned = false" class="px-4 py-2 bg-gray-200 text-gray-700 font-bold rounded hover:bg-gray-300">Close</button>
          </div>
      </div>
  </div>

  <div v-else class="min-h-screen flex flex-col bg-[#f8f9fa] text-[#333]">
    
    <!-- Navbar-like Header -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">C</div>
        <span class="font-semibold text-lg tracking-tight">CodeMan <span class="text-gray-400 font-normal">| 统一认证平台</span></span>
      </div>
      <div class="text-sm text-gray-500">API Gateway v1.0</div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 flex items-center justify-center p-4">
      <div class="w-full max-w-4xl bg-white rounded-xl shadow-lg overflow-hidden flex flex-col md:flex-row border border-gray-100">
        
        <!-- Left Side: Info & Context -->
        <div class="md:w-5/12 bg-gray-50 p-8 flex flex-col justify-between border-r border-gray-100">
          <div>
            <h1 class="text-2xl font-bold text-gray-800 mb-4">{{ t('common.authTitle') }}</h1>
            <p class="text-gray-600 mb-6 text-sm leading-relaxed">
              <strong class="text-gray-900">CodeMan Community</strong> {{ t('common.authRequest') }}
              {{ t('common.authScope') }}
            </p>
            
            <div class="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-6">
              <h3 class="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2">AUTH SCOPE</h3>
              <ul class="space-y-2">
                <li class="flex items-center text-sm text-blue-900">
                  <svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                  {{ t('common.scopeProfile') }}
                </li>
                <li class="flex items-center text-sm text-blue-900">
                  <svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                  {{ t('common.scopePost') }}
                </li>
              </ul>
            </div>
          </div>

          <div class="text-xs text-gray-400 mt-8">
            <p>Protected by RSA-2048 Encryption</p>
            <p class="mt-1">CodeMan ID: 8829102</p>
          </div>
        </div>

        <!-- Right Side: Login Form -->
        <div class="md:w-7/12 p-8 md:p-10 flex flex-col justify-center">
          <div class="mb-8 text-center md:text-left">
            <h2 class="text-xl font-bold text-gray-900">{{ t('common.loginTitle') }}</h2>
            <p class="text-sm text-gray-500 mt-1">{{ t('common.loginSubtitle') }}</p>
          </div>

          <div v-if="error" class="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-r">
            <div class="flex">
              <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                </svg>
              </div>
              <div class="ml-3">
                <p class="text-sm text-red-700">{{ error }}</p>
              </div>
            </div>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.usernameLabel') }}</label>
              <div class="relative">
                <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
                  <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </span>
                <input 
                  v-model="username" 
                  type="text" 
                  required
                  class="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-white"
                  :placeholder="t('common.usernamePlaceholder')"
                >
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.passwordLabel') }}</label>
              <div class="relative">
                <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
                  <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </span>
                <input 
                  v-model="password" 
                  type="password" 
                  required
                  class="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-white"
                  :placeholder="t('common.passwordPlaceholder')"
                >
              </div>
            </div>

            <div class="pt-2">
              <button 
                type="submit"
                :disabled="loading"
                class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ loading ? t('common.loggingIn') : t('common.submitLogin') }}
              </button>
            </div>
          </form>
          
          <div class="mt-6 text-center">
             <a href="https://shequ.codemao.cn/wiki/forum" target="_blank" class="text-xs text-gray-400 hover:text-gray-600">{{ t('common.forgotPassword') }}</a>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="py-6 text-center text-gray-400 text-xs">
      <p>&copy; 2026 CodeMan Community. All rights reserved.</p>
      <p class="mt-1">Designed for Codemao Developers.</p>
    </footer>

  </div>
</template>
