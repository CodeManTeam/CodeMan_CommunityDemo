<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'
import { Eye, ThumbsUp, Download } from 'lucide-vue-next'

const router = useRouter()

const works = ref([])
const loading = ref(true)
const page = ref(1)
const limit = 24 // More items per page for showcase
const hasMore = ref(true)

const showSubmitModal = ref(false)
const userWorks = ref([])
const loadingUserWorks = ref(false)
const submission = ref({
  work_id: '',
  bcm_url: ''
})
const submitting = ref(false)

const fetchWorks = async (reset = false) => {
  if (reset) {
    page.value = 1
    works.value = []
    hasMore.value = true
  }
  
  loading.value = true
  try {
    const skip = (page.value - 1) * limit
    const res = await axios.get(`/api/works?skip=${skip}&limit=${limit}`)
    
    if (res.data.length < limit) {
      hasMore.value = false
    }
    
    works.value = [...works.value, ...res.data]
  } catch (e) {
    console.error("Failed to fetch works", e)
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  page.value++
  fetchWorks()
}

const openWork = (workId) => {
  router.push(`/work/${workId}`)
}

const downloadBcm = (url, event) => {
  event.stopPropagation() // Prevent card click
  if (url) {
    window.open(url, '_blank')
  }
}

const fetchUserWorks = async () => {
  if (!authState.user) return
  loadingUserWorks.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get('/api/works/user-codemao-works', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    userWorks.value = res.data.items || []
  } catch (e) {
    console.error("Failed to fetch user works", e)
  } finally {
    loadingUserWorks.value = false
  }
}

const selectWork = (work) => {
  submission.value.work_id = work.id
}

const submitWork = async () => {
  if (!submission.value.work_id) return
  
  const token = localStorage.getItem('token')
  if (!token) return

  submitting.value = true
  try {
    await axios.post('/api/works/submit', {
      work_id: parseInt(submission.value.work_id),
      bcm_url: '' // Removed user input for bcm_url
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    alert('Work submitted successfully!')
    showSubmitModal.value = false
    submission.value = { work_id: '', bcm_url: '' }
    fetchWorks(true) // Refresh list
  } catch (e) {
    alert("Submission failed: " + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

const openSubmitModal = () => {
  showSubmitModal.value = true
  fetchUserWorks()
}

onMounted(() => {
  fetchWorks(true)
})
</script>

<template>
  <div class="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="flex items-center justify-between mb-12">
      <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight">Community Showcase</h1>
      <button 
        v-if="authState.isAuthenticated"
        @click="openSubmitModal"
        class="px-8 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition shadow-lg transform hover:-translate-y-0.5"
      >
        Submit Your Work
      </button>
    </div>

    <!-- Submit Modal -->
    <div v-if="showSubmitModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-2xl p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-gray-800">Submit Your Work</h2>
          <button @click="showSubmitModal = false" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>
        
        <div class="space-y-6">
          <!-- Step 1: Select from Codemao -->
          <div>
            <h3 class="text-sm font-bold text-gray-500 uppercase mb-3">Select from your Codemao works</h3>
            <div v-if="loadingUserWorks" class="text-center py-8 text-gray-500">Loading your works...</div>
            <div v-else class="grid grid-cols-2 gap-4 max-h-60 overflow-y-auto p-2 border border-gray-100 rounded-lg">
              <div 
                v-for="work in userWorks" 
                :key="work.id"
                @click="selectWork(work)"
                class="flex items-center space-x-3 p-2 rounded-lg cursor-pointer transition border"
                :class="submission.work_id === work.id ? 'border-blue-500 bg-blue-50' : 'border-transparent hover:bg-gray-50'"
              >
                <img :src="work.preview" class="w-12 h-12 rounded object-cover">
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-gray-800 truncate">{{ work.work_name }}</div>
                  <div class="text-xs text-gray-500">ID: {{ work.id }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 2: Manual Input / Confirmation -->
          <div class="border-t border-gray-100 pt-4">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Work ID</label>
              <input 
                v-model="submission.work_id" 
                type="number" 
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Select above or enter ID"
              >
            </div>
            
            <div class="mb-4 p-4 bg-yellow-50 rounded-lg flex items-start space-x-3 text-sm text-yellow-800">
               <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
               </svg>
               <p>
                 If your work requires a BCM file, please manually upload it to a file hosting service and include the link in your work's description on Codemao.
               </p>
            </div>
          </div>

          <div class="flex justify-end space-x-4 pt-2">
            <button @click="showSubmitModal = false" class="px-6 py-2 text-gray-600 font-medium hover:bg-gray-100 rounded-lg">Cancel</button>
            <button 
              @click="submitWork" 
              :disabled="submitting || !submission.work_id"
              class="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ submitting ? 'Verifying...' : 'Submit' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Works Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
      <div 
        v-for="work in works" 
        :key="work.work_id" 
        @click="openWork(work.work_id)"
        class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl hover:-translate-y-2 transition-all duration-300 cursor-pointer group flex flex-col h-full"
      >
        <!-- Preview Image (Square) -->
        <div class="aspect-square bg-gray-100 relative overflow-hidden">
          <img 
            :src="work.preview_url" 
            alt="Work Preview" 
            class="w-full h-full object-cover group-hover:scale-110 transition duration-700"
            loading="lazy"
            width="300"
            height="300"
          >
          <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition"></div>
        </div>
        
        <!-- Content -->
        <div class="p-6 flex-1 flex flex-col">
          <h3 class="font-bold text-gray-800 mb-2 line-clamp-1 text-lg group-hover:text-blue-600 transition">{{ work.work_name }}</h3>
          
          <div class="flex items-center space-x-2.5 mb-5">
             <img 
               :src="work.avatar_url || 'https://via.placeholder.com/32'" 
               class="w-6 h-6 rounded-full border border-gray-200" 
               alt="Avatar"
               width="24"
               height="24"
               loading="lazy"
             >
             <span class="text-sm text-gray-500 truncate font-medium">{{ work.nickname }}</span>
          </div>

          <div class="mt-auto pt-4 border-t border-gray-50 flex items-center justify-between">
            <div class="flex items-center text-gray-400 space-x-3 text-xs">
              <span class="flex items-center" title="Views"><Eye class="w-3 h-3 mr-1" /> {{ work.views_count }}</span>
              <span class="flex items-center" title="Likes"><ThumbsUp class="w-3 h-3 mr-1" /> {{ work.likes_count }}</span>
            </div>
            
            <button 
              @click="downloadBcm(work.bcm_url, $event)"
              :disabled="!work.bcm_url"
              class="text-xs font-bold px-3 py-1.5 rounded-full transition-colors flex items-center space-x-1"
              :class="work.bcm_url ? 'bg-blue-50 text-blue-600 hover:bg-blue-100' : 'bg-gray-50 text-gray-400 cursor-not-allowed group/btn relative'"
            >
              <span>Download</span>
              <Download class="w-3 h-3" />
              
              <!-- Tooltip for disabled button -->
              <div v-if="!work.bcm_url" class="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 w-48 bg-gray-800 text-white text-xs rounded py-1 px-2 text-center opacity-0 group-hover/btn:opacity-100 transition pointer-events-none z-10">
                Please visit original link to find download
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div class="text-center py-12">
      <div v-if="loading" class="flex items-center justify-center space-x-2 text-gray-500">
        <svg class="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading works...</span>
      </div>
      
      <button 
        v-else-if="hasMore"
        @click="loadMore"
        class="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-bold rounded-full hover:bg-gray-50 hover:border-gray-300 transition shadow-sm hover:shadow transform hover:-translate-y-0.5"
      >
        Load More Works
      </button>
      
      <p v-else class="text-gray-400">
        You've viewed all works!
      </p>
    </div>
  </div>
</template>
