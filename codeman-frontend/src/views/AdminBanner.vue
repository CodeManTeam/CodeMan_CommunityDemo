<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { authState } from '../store'
import { useRouter } from 'vue-router'

const router = useRouter()
const banners = ref([])
const loading = ref(false)
const showAddModal = ref(false)

const newBanner = ref({
  title: '',
  image_url: '',
  link_url: ''
})

const fetchBanners = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/banners')
    // Filter only custom banners for management (those with is_custom flag or specific ID format)
    banners.value = res.data.filter(b => b.is_custom)
  } catch (e) {
    console.error("Failed to fetch banners", e)
  } finally {
    loading.value = false
  }
}

const addBanner = async () => {
  if (!newBanner.value.title || !newBanner.value.image_url) {
    alert("Please fill in required fields")
    return
  }

  const token = authState.token || localStorage.getItem('token')
  if (!token) {
    alert("Please login first")
    return
  }

  try {
    await axios.post('/api/banners', newBanner.value, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    showAddModal.value = false
    newBanner.value = { title: '', image_url: '', link_url: '' }
    fetchBanners()
  } catch (e) {
    console.error("Add banner failed", e)
    alert("Failed to add banner")
  }
}

const deleteBanner = async (bannerId) => {
  if (!confirm("Are you sure you want to delete this banner?")) return

  const token = authState.token || localStorage.getItem('token')
  // bannerId is like "custom_123", we need "123"
  const id = bannerId.split('_')[1]

  try {
    await axios.delete(`/api/banners/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    fetchBanners()
  } catch (e) {
    console.error("Delete banner failed", e)
    alert("Failed to delete banner")
  }
}

onMounted(() => {
  if (!authState.isAuthenticated) {
    router.push('/login')
    return
  }
  fetchBanners()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-5xl">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-2xl font-bold text-gray-800">Banner Management</h1>
      <button 
        @click="showAddModal = true"
        class="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
      >
        <span>+ Add Banner</span>
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">
      Loading banners...
    </div>

    <div v-else-if="banners.length === 0" class="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300 text-gray-500">
      No custom banners found. Currently using only Codemao official banners.
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div 
        v-for="banner in banners" 
        :key="banner.id"
        class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden group"
      >
        <div class="relative aspect-[2.5/1]">
          <img :src="banner.background_url" class="w-full h-full object-cover">
          <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center space-x-4">
             <a :href="banner.target_url" target="_blank" class="text-white hover:underline text-sm">View Link</a>
             <button @click="deleteBanner(banner.id)" class="text-red-400 hover:text-red-200 font-bold text-sm bg-white/10 px-3 py-1 rounded">Delete</button>
          </div>
        </div>
        <div class="p-4">
          <h3 class="font-bold text-gray-800 truncate">{{ banner.title }}</h3>
          <p class="text-xs text-gray-400 truncate">{{ banner.target_url }}</p>
        </div>
      </div>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showAddModal = false"></div>
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md relative z-10 p-6">
        <h2 class="text-xl font-bold mb-4">Add New Banner</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input v-model="newBanner.title" type="text" class="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Banner Title">
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
            <input v-model="newBanner.image_url" type="text" class="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="https://example.com/image.jpg">
            <p class="text-xs text-gray-500 mt-1">Recommended size: 1200x400</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Target Link</label>
            <input v-model="newBanner.link_url" type="text" class="w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="https://...">
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showAddModal = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
          <button @click="addBanner" class="px-4 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700">Add Banner</button>
        </div>
      </div>
    </div>
  </div>
</template>
