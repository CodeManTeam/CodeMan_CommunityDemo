<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { debounce } from 'lodash'

const router = useRouter()
const searchQuery = ref('')
const results = ref([])
const showResults = ref(false)
const loading = ref(false)

const performSearch = async () => {
  if (searchQuery.value.length < 2) {
    results.value = []
    return
  }
  
  loading.value = true
  try {
    const res = await axios.get('/api/search/global', {
      params: { q: searchQuery.value }
    })
    results.value = res.data
    showResults.value = true
  } catch (e) {
    console.error("Search failed", e)
  } finally {
    loading.value = false
  }
}

const debouncedSearch = debounce(performSearch, 300)

watch(searchQuery, () => {
  if (searchQuery.value.length < 2) {
    showResults.value = false
    results.value = []
    return
  }
  debouncedSearch()
})

const navigateTo = (url) => {
  if (url.startsWith('http')) {
    window.open(url, '_blank')
  } else {
    router.push(url)
  }
  showResults.value = false
  searchQuery.value = ''
}

const getIcon = (type) => {
  switch (type) {
    case 'user': return '👤'
    case 'post': return '📝'
    case 'work': return '🎮'
    default: return '🔍'
  }
}

const handleEnter = () => {
  if (searchQuery.value.trim().length >= 1) {
    showResults.value = false
    router.push({ name: 'search-results', query: { q: searchQuery.value } })
  }
}
</script>

<template>
  <div class="relative w-full max-w-md">
    <div class="relative">
      <input 
        v-model="searchQuery"
        type="text" 
        placeholder="Search posts, users, works..." 
        class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition text-sm bg-gray-50 focus:bg-white"
        @focus="searchQuery.length >= 2 && (showResults = true)"
        @keyup.enter="handleEnter"
      >
      <div class="absolute left-3 top-2.5 text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <div v-if="loading" class="absolute right-3 top-2.5">
        <svg class="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
    </div>

    <!-- Dropdown Results -->
    <div 
      v-if="showResults && (results.length > 0 || searchQuery.length >= 2)" 
      class="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden z-50 max-h-96 overflow-y-auto"
    >
      <div v-if="results.length === 0 && !loading" class="p-4 text-center text-gray-500 text-sm">
        No results found for "{{ searchQuery }}"
      </div>
      
      <div v-else class="divide-y divide-gray-50">
        <div 
          v-for="(item, index) in results" 
          :key="index"
          @click="navigateTo(item.url)"
          class="p-3 hover:bg-gray-50 cursor-pointer flex items-center space-x-3 transition"
        >
          <div class="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-lg overflow-hidden">
            <img v-if="item.image_url" :src="item.image_url" class="w-full h-full object-cover">
            <span v-else>{{ getIcon(item.type) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-900 truncate">{{ item.title }}</div>
            <div class="text-xs text-gray-500 truncate">{{ item.subtitle }}</div>
          </div>
          <div class="text-xs text-gray-400 capitalize bg-gray-100 px-2 py-0.5 rounded-full">
            {{ item.type }}
          </div>
        </div>
        
        <!-- View All Link -->
        <div 
          @click="handleEnter"
          class="p-3 text-center text-sm text-blue-600 font-medium hover:bg-blue-50 cursor-pointer border-t border-gray-100"
        >
          View all results for "{{ searchQuery }}"
        </div>
      </div>
    </div>
    
    <!-- Backdrop to close -->
    <div 
      v-if="showResults" 
      class="fixed inset-0 z-40" 
      @click="showResults = false"
    ></div>
  </div>
</template>

<style scoped>
/* Ensure input stays above backdrop */
.relative {
  z-index: 45; 
}
</style>