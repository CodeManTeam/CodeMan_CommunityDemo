
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const appInfo = ref(null)

// Params
const clientId = route.query.client_id
const redirectUri = route.query.redirect_uri
const responseType = route.query.response_type || 'code'
const state = route.query.state

onMounted(async () => {
  if (!authState.isAuthenticated) {
    // Redirect to login, but keep the current URL as return target
    // The router guard might have already handled this, but just in case
    window.location.href = `/login?redirect=${encodeURIComponent(route.fullPath)}`
    return
  }

  if (!clientId || !redirectUri) {
    error.value = "Missing required parameters (client_id, redirect_uri)"
    loading.value = false
    return
  }

  try {
    const res = await axios.get('/api/oauth/authorize', {
      params: {
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: responseType,
        state: state
      }
    })
    appInfo.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || "Authorization request failed"
  } finally {
    loading.value = false
  }
})

const handleAuthorize = async () => {
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('client_id', clientId)
    formData.append('redirect_uri', redirectUri)
    formData.append('response_type', responseType)
    if (state) formData.append('state', state)

    const res = await axios.post('/api/oauth/authorize', formData)
    
    // Redirect back to the app
    window.location.href = res.data.redirect_to
  } catch (err) {
    error.value = err.response?.data?.detail || "Authorization failed"
    loading.value = false
  }
}

const handleCancel = () => {
  // Redirect back with error or just close?
  // Standard OAuth says redirect with error=access_denied
  const sep = redirectUri.includes('?') ? '&' : '?'
  let target = `${redirectUri}${sep}error=access_denied`
  if (state) target += `&state=${state}`
  window.location.href = target
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center items-center p-4">
    <div class="max-w-md w-full bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100">
      
      <!-- Header -->
      <div class="bg-gray-50 p-6 border-b border-gray-100 flex items-center justify-center">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">C</div>
          <span class="font-bold text-gray-800 text-lg">CodeMan SSO</span>
        </div>
      </div>

      <div class="p-8">
        <div v-if="loading" class="text-center py-8">
          <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p class="text-gray-500">Verifying application...</p>
        </div>

        <div v-else-if="error" class="text-center py-4">
           <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Authorization Error</h3>
          <p class="text-red-600 bg-red-50 p-3 rounded-lg text-sm">{{ error }}</p>
        </div>

        <div v-else>
          <div class="text-center mb-8">
            <div class="w-20 h-20 bg-gray-100 rounded-2xl mx-auto mb-4 flex items-center justify-center text-3xl">
              {{ appInfo.app_name.charAt(0).toUpperCase() }}
            </div>
            <h2 class="text-xl font-bold text-gray-900 mb-2">{{ appInfo.app_name }}</h2>
            <p class="text-gray-500 text-sm">wants to access your CodeMan account</p>
          </div>

          <div class="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-8">
            <h4 class="text-xs font-bold text-blue-800 uppercase tracking-wider mb-3">This app will be able to:</h4>
            <ul class="space-y-2">
              <li class="flex items-start">
                <svg class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                <span class="text-sm text-gray-700">Read your public profile (Username, Avatar, ID)</span>
              </li>
            </ul>
          </div>

          <div class="flex items-center justify-center space-x-2 mb-8">
            <img :src="authState.user?.avatar_url" class="w-8 h-8 rounded-full border border-gray-200">
            <span class="text-sm font-medium text-gray-700">{{ authState.user?.username }}</span>
            <span class="text-xs text-gray-400">(You)</span>
          </div>

          <div class="space-y-3">
            <button 
              @click="handleAuthorize"
              class="w-full py-3 bg-blue-600 text-white font-bold rounded-xl shadow-lg hover:bg-blue-700 hover:shadow-xl transition transform active:scale-95"
            >
              Authorize {{ appInfo.app_name }}
            </button>
            <button 
              @click="handleCancel"
              class="w-full py-3 bg-white border border-gray-200 text-gray-600 font-bold rounded-xl hover:bg-gray-50 transition"
            >
              Cancel
            </button>
          </div>
          
          <p class="text-center text-xs text-gray-400 mt-6">
            You will be redirected to <span class="font-mono">{{ appInfo.redirect_uri }}</span>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
