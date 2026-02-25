
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { authState } from '../store'

const apps = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const newApp = ref({
  name: '',
  description: '',
  redirect_uris: ''
})

onMounted(async () => {
  if (authState.isAuthenticated) {
    fetchApps()
  }
})

const fetchApps = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/oauth/apps/me')
    apps.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleCreateApp = async () => {
  try {
    await axios.post('/api/oauth/apps', newApp.value)
    showCreateModal.value = false
    newApp.value = { name: '', description: '', redirect_uris: '' }
    fetchApps()
  } catch (err) {
    alert(err.response?.data?.detail || "Failed to create app")
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-8">
      <h2 class="text-2xl font-bold text-gray-800">My Applications</h2>
      <button 
        @click="showCreateModal = true"
        class="px-4 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition shadow-md"
      >
        + New App
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">
      Loading...
    </div>

    <div v-else-if="apps.length === 0" class="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-200">
      <p class="text-gray-500 mb-4">You haven't created any applications yet.</p>
      <button @click="showCreateModal = true" class="text-blue-600 font-bold hover:underline">Get Started</button>
    </div>

    <div v-else class="grid gap-6">
      <div v-for="app in apps" :key="app.client_id" class="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-xl font-bold text-gray-900">{{ app.name }}</h3>
            <p class="text-gray-500 text-sm mt-1">{{ app.description || 'No description' }}</p>
          </div>
          <span class="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded">Active</span>
        </div>
        
        <div class="space-y-3 bg-gray-50 p-4 rounded-lg text-sm font-mono break-all">
          <div>
            <span class="text-gray-400 select-none block text-xs uppercase mb-1">Client ID</span>
            <span class="text-blue-600">{{ app.client_id }}</span>
          </div>
          <div>
            <span class="text-gray-400 select-none block text-xs uppercase mb-1">Client Secret</span>
            <span class="text-red-600">{{ app.client_secret }}</span>
          </div>
          <div>
            <span class="text-gray-400 select-none block text-xs uppercase mb-1">Redirect URIs</span>
            <span class="text-gray-600">{{ app.redirect_uris }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showCreateModal = false"></div>
      <div class="bg-white rounded-xl w-full max-w-lg p-6 shadow-2xl relative z-10">
        <h3 class="text-xl font-bold text-gray-900 mb-6">Register New Application</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">App Name</label>
            <input v-model="newApp.name" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="My Awesome App">
          </div>
          
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">Description</label>
            <textarea v-model="newApp.description" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" rows="3" placeholder="What does your app do?"></textarea>
          </div>

          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">Redirect URIs</label>
            <input v-model="newApp.redirect_uris" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="https://myapp.com/callback, http://localhost:3000/callback">
            <p class="text-xs text-gray-500 mt-1">Comma separated list of allowed callback URLs</p>
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-8">
          <button @click="showCreateModal = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
          <button @click="handleCreateApp" class="px-4 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700">Create App</button>
        </div>
      </div>
    </div>
  </div>
</template>
