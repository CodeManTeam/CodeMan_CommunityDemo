<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'

const route = useRoute()
const router = useRouter()
const query = ref(route.query.q || '')
const results = ref([])
const loading = ref(false)
const selectedWork = ref(null)
const showWorkModal = ref(false)
const workLoading = ref(false)

// Review State
const reviewContent = ref('')
const reviewRating = ref(5)
const submittingReview = ref(false)

const performSearch = async () => {
  if (!query.value) return
  
  loading.value = true
  try {
    const res = await axios.get('/api/search/global', {
      params: { q: query.value }
    })
    results.value = res.data
  } catch (e) {
    console.error("Search failed", e)
  } finally {
    loading.value = false
  }
}

watch(() => route.query.q, (newVal) => {
  query.value = newVal
  performSearch()
})

onMounted(() => {
  performSearch()
})

const fetchWorkDetails = async (workId) => {
  // Directly navigate to work detail page
  router.push(`/work/${workId}`)
}

const navigateTo = (item) => {
  if (item.type === 'work') {
    // Navigate to internal work detail page
    router.push(`/work/${item.id}`)
  } else if (item.url.startsWith('http')) {
    window.open(item.url, '_blank')
  } else {
    router.push(item.url)
  }
}

const openCodemao = () => {
  // Logic removed as it's now handled in WorkDetail page
}

const downloadBcm = () => {
  // Logic removed as it's now handled in WorkDetail page
}

const submitReview = async () => {
  // Logic removed as it's now handled in WorkDetail page
}

const getIcon = (type) => {
  switch (type) {
    case 'user': return '👤'
    case 'post': return '📝'
    case 'work': return '🎮'
    default: return '🔍'
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-6 flex items-center">
      <span class="mr-2">🔍</span> 
      Search Results for "{{ query }}"
    </h1>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="results.length === 0" class="text-center py-12 bg-white rounded-xl border border-gray-100 shadow-sm">
      <p class="text-gray-500 text-lg">No results found.</p>
      <p class="text-gray-400 text-sm mt-2">Try different keywords or check spelling.</p>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div 
        v-for="(item, index) in results" 
        :key="index"
        @click="navigateTo(item)"
        class="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition cursor-pointer overflow-hidden flex flex-col group"
      >
        <!-- Card Image/Cover -->
        <div class="h-32 bg-gray-100 relative overflow-hidden">
          <img 
            v-if="item.image_url" 
            :src="item.image_url" 
            class="w-full h-full object-cover group-hover:scale-105 transition duration-500"
          >
          <div v-else class="w-full h-full flex items-center justify-center text-4xl text-gray-300">
            {{ getIcon(item.type) }}
          </div>
          
          <!-- Type Badge -->
          <div class="absolute top-2 right-2 px-2 py-1 bg-white/90 backdrop-blur-sm rounded-md text-xs font-bold shadow-sm capitalize"
               :class="{
                 'text-blue-600': item.type === 'post',
                 'text-purple-600': item.type === 'work',
                 'text-green-600': item.type === 'user'
               }">
            {{ item.type }}
          </div>
        </div>

        <!-- Card Content -->
        <div class="p-4 flex-1 flex flex-col">
          <h3 class="font-bold text-gray-900 mb-1 line-clamp-1 group-hover:text-blue-600 transition">{{ item.title }}</h3>
          <p class="text-sm text-gray-500 line-clamp-2 mb-4 flex-1">{{ item.subtitle }}</p>
          
          <div class="mt-auto pt-3 border-t border-gray-50 flex justify-between items-center text-xs text-gray-400">
            <span>
              <span v-if="item.type === 'work'">Open in Codemao</span>
              <span v-else>View Details</span>
            </span>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Work Detail Modal Removed (replaced by WorkDetail.vue) -->
  </div>
</template>
