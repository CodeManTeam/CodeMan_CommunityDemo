<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { authState } from '../store'
import MarkdownEditor from '../components/MarkdownEditor.vue'
import { useI18n } from '../i18n'
import { ShieldCheck, Eye, MessageCircle, Search, X, Heart, Pin } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()

// --- State ---
const categories = ref([])
const posts = ref([])
const bcmPosts = ref([]) // State for Codemao posts
const bcmBoards = ref([]) // State for Codemao boards
const selectedBcmBoard = ref('2') // Default to 'Chat' (2) or first available
const activeTab = ref('community') // 'community' or 'codemao'
const selectedCategory = ref('All')
const loading = ref(false)
const showCreateModal = ref(false)
const page = ref(1)
const bcmPage = ref(0) // Codemao API uses offset, we can track page or offset
const hasMore = ref(true)
const bcmHasMore = ref(true)

const newPost = ref({
  title: '',
  content: '',
  category_id: null
})

const searchQuery = ref('')

// --- Fetch Data ---
const fetchCategories = async () => {
  try {
    const res = await axios.get('/api/categories')
    categories.value = res.data
  } catch (e) {
    console.error("Failed to fetch categories", e)
  }
}

const fetchBcmBoards = async () => {
  try {
    const res = await axios.get('/api/bcm/boards')
    bcmBoards.value = res.data.items || res.data
  } catch (e) {
    console.error("Failed to fetch BCM boards", e)
  }
}

const fetchPosts = async (reset = false) => {
  if (reset) {
    page.value = 1
    posts.value = []
    hasMore.value = true
  }
  
  if (!hasMore.value && !reset) return

  loading.value = true
  try {
    const params = {
      skip: (page.value - 1) * 20,
      limit: 20
    }
    
    // Add auth token if available to get "is_liked" status
    const headers = {}
    const token = localStorage.getItem('token')
    if (token) headers['Authorization'] = `Bearer ${token}`

    if (selectedCategory.value !== 'All') {
      const cat = categories.value.find(c => c.name === selectedCategory.value)
      if (cat) params.category_id = cat.id
    }
    
    const res = await axios.get('/api/posts', { params, headers })
    if (res.data.length < 20) {
      hasMore.value = false
    }
    
    posts.value = [...posts.value, ...res.data]
    page.value++
  } catch (e) {
    console.error("Failed to fetch posts", e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push(`/search?q=${encodeURIComponent(searchQuery.value)}`)
  }
}

const fetchBcmPosts = async (reset = false) => {
  if (reset) {
    bcmPage.value = 0
    bcmPosts.value = []
    bcmHasMore.value = true
  }
  
  if (!bcmHasMore.value && !reset) return
  
  loading.value = true
  try {
    const limit = 20
    const offset = bcmPage.value * limit
    const res = await axios.get('/api/bcm/posts', {
      params: { 
        limit, 
        offset,
        board_id: selectedBcmBoard.value 
      }
    })
    
    if (res.data.length < limit) {
      bcmHasMore.value = false
    }
    
    // Filter out duplicates based on ID
    const newPosts = res.data.filter(newPost => 
      !bcmPosts.value.some(existingPost => existingPost.id === newPost.id)
    )
    
    bcmPosts.value = [...bcmPosts.value, ...newPosts]
    bcmPage.value++
  } catch (e) {
    console.error("Failed to fetch BCM posts", e)
    bcmHasMore.value = false
  } finally {
    loading.value = false
  }
}

const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'codemao' && bcmPosts.value.length === 0) {
    fetchBcmPosts(true)
  }
}

const changeBcmBoard = (boardId) => {
    selectedBcmBoard.value = boardId
    fetchBcmPosts(true)
}

// --- Actions ---
const filterPosts = (categoryName) => {
  selectedCategory.value = categoryName
  fetchPosts(true)
}

const handleCreatePost = async () => {
  if (!newPost.value.title || !newPost.value.content || !newPost.value.category_id) {
    alert("Please fill in all fields")
    return
  }
  
  const token = localStorage.getItem('token')
  if (!token) {
    alert("Please login first")
    return
  }

  try {
    await axios.post('/api/posts', newPost.value, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    showCreateModal.value = false
    newPost.value = { title: '', content: '', category_id: null }
    fetchPosts(true) // Refresh
  } catch (e) {
    alert("Failed to create post: " + (e.response?.data?.detail || e.message))
  }
}

const openCodemaoPost = (postId) => {
  router.push(`/forum/bcm/${postId}`)
}

const togglePin = async (post, event) => {
    event.stopPropagation()
    if (!confirm(`Are you sure you want to ${post.is_pinned ? 'unpin' : 'pin'} this post?`)) return
    
    try {
        const token = localStorage.getItem('token')
        await axios.put(`/api/posts/${post.id}/pin`, {}, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        post.is_pinned = !post.is_pinned
        // Refresh to re-sort
        fetchPosts(true)
    } catch (e) {
        alert("Failed to pin post: " + (e.response?.data?.detail || e.message))
    }
}

// --- Lifecycle ---
onMounted(async () => {
  await fetchCategories()
  await fetchPosts(true)
  fetchBcmBoards() // Fetch boards in background
})
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
    <!-- Sidebar: Categories -->
    <div class="md:col-span-1 space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">{{ t('forum.categories') }}</h3>
        <ul class="space-y-2">
          <li>
            <button 
              @click="filterPosts('All')"
              class="w-full text-left px-4 py-2 rounded-lg transition-colors"
              :class="selectedCategory === 'All' ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-50'"
            >
              {{ t('forum.allPosts') }}
            </button>
          </li>
          <li v-for="cat in categories" :key="cat.id">
            <button 
              @click="filterPosts(cat.name)"
              class="w-full text-left px-4 py-2 rounded-lg transition-colors"
              :class="selectedCategory === cat.name ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-50'"
            >
              {{ cat.name }}
            </button>
          </li>
        </ul>
      </div>
      
      <button 
        @click="showCreateModal = true"
        class="w-full py-3 bg-blue-600 text-white font-bold rounded-xl shadow-lg hover:bg-blue-700 transition transform hover:-translate-y-1"
      >
        {{ t('forum.newPost') }}
      </button>

      <!-- Search Box (Simple) -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">{{ t('common.search') }}</h3>
        <div class="relative">
          <input 
            v-model="searchQuery"
            @keyup.enter="handleSearch"
            type="text" 
            :placeholder="t('forum.searchPlaceholder')" 
            class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
          >
          <Search class="h-5 w-5 text-gray-400 absolute left-3 top-2.5" />
        </div>
      </div>
    </div>

    <!-- Main Content: Post List -->
    <div class="md:col-span-3">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-800">{{ selectedCategory === 'All' ? t('forum.allPosts') : selectedCategory }} {{ t('forum.discussions') }}</h2>
        
        <!-- Tabs -->
        <div class="flex bg-gray-100 p-1 rounded-lg">
           <button 
             @click="switchTab('community')"
             class="px-4 py-1.5 rounded-md text-sm font-medium transition"
             :class="activeTab === 'community' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
           >
             {{ t('forum.communityTab') }}
           </button>
           <button 
             @click="switchTab('codemao')"
             class="px-4 py-1.5 rounded-md text-sm font-medium transition"
             :class="activeTab === 'codemao' ? 'bg-white text-orange-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
           >
             {{ t('forum.officialTab') }}
           </button>
        </div>
      </div>

      <div v-if="loading && posts.length === 0 && bcmPosts.length === 0" class="text-center py-12 text-gray-500">
        {{ t('common.loading') }}
      </div>

      <!-- Community Posts List -->
      <div v-if="activeTab === 'community'">
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div v-if="posts.length === 0 && !loading" class="p-12 text-center text-gray-400">
            {{ t('forum.noPosts') }}
          </div>
          <div 
            v-for="post in posts" 
            :key="post.id" 
            @click="$router.push(`/forum/${post.id}`)"
            class="p-6 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition cursor-pointer group relative"
          >
            <!-- Pin Button for Admin -->
            <div class="absolute top-4 right-4 z-10" v-if="authState.isAdmin">
                <button @click="togglePin(post, $event)" class="p-1.5 hover:bg-gray-200 rounded-full transition" :title="post.is_pinned ? 'Unpin' : 'Pin'">
                    <Pin class="w-4 h-4" :class="post.is_pinned ? 'text-red-500 fill-current' : 'text-gray-400'" />
                </button>
            </div>

            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-xl font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors flex items-center">
                    <Pin v-if="post.is_pinned" class="w-4 h-4 mr-2 text-red-500 fill-current flex-shrink-0" />
                    {{ post.title }}
                </h3>
                <p class="text-sm text-gray-500 mb-2">
                  {{ t('forum.postedBy') }} <span class="font-medium text-gray-700">{{ post.user?.username || 'Unknown' }}</span>
                  <span v-if="post.user?.id === 1" class="bg-red-500 text-white text-xs px-2 py-0.5 rounded font-bold ml-1 flex items-center inline-flex" :title="t('common.admin')">
                      <ShieldCheck class="w-3 h-3 mr-1" />
                      {{ t('common.admin') }}
                  </span> 
                  <span v-else-if="post.user?.is_admin" class="bg-blue-500 text-white text-xs px-2 py-0.5 rounded font-bold ml-1 flex items-center inline-flex" title="Admin">
                      <ShieldCheck class="w-3 h-3 mr-1" />
                      Admin
                  </span>
                  • {{ new Date(post.created_at).toLocaleDateString() }}
                </p>
                <p class="text-gray-600 text-sm line-clamp-2 break-words">{{ post.content }}</p>
              </div>
              <div class="flex space-x-4 text-gray-400 text-sm">
                <span class="flex items-center"><Eye class="w-4 h-4 mr-1" /> {{ post.views }}</span>
                <span class="flex items-center text-pink-500" v-if="post.is_liked"><Heart class="w-4 h-4 mr-1 fill-current" /> {{ post.likes }}</span>
                <span class="flex items-center" v-else><Heart class="w-4 h-4 mr-1" /> {{ post.likes }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Load More Button -->
        <div v-if="hasMore" class="p-4 text-center mt-4">
          <button 
            @click="fetchPosts(false)" 
            :disabled="loading"
            class="px-8 py-3 bg-white border border-gray-200 text-gray-600 rounded-full hover:bg-gray-50 hover:border-gray-300 transition shadow-sm text-sm font-medium disabled:opacity-50"
          >
            {{ loading ? t('common.loading') : t('forum.loadMore') }}
          </button>
        </div>
      </div>

      <!-- Codemao Posts List -->
      <div v-if="activeTab === 'codemao'">
        <!-- Board Selector -->
        <div class="mb-4 overflow-x-auto whitespace-nowrap pb-2">
            <button 
                v-for="board in bcmBoards" 
                :key="board.id"
                @click="changeBcmBoard(board.id)"
                class="px-4 py-2 rounded-full text-sm font-medium mr-2 transition-colors border"
                :class="selectedBcmBoard === board.id ? 'bg-orange-100 text-orange-600 border-orange-200' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
            >
                <img :src="board.icon_url" class="w-4 h-4 inline-block mr-1 rounded-full" v-if="board.icon_url">
                {{ board.name }}
            </button>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-orange-100 overflow-hidden">
          <div v-if="bcmPosts.length === 0 && !loading" class="p-12 text-center text-gray-400">
            {{ t('forum.noOfficialPosts') }}
          </div>
          <div 
            v-for="post in bcmPosts" 
            :key="post.id" 
            class="p-6 border-b border-gray-100 last:border-0 hover:bg-orange-50 transition cursor-pointer group"
            @click="openCodemaoPost(post.id)"
          >
            <div class="flex justify-between items-start">
              <div>
                <div class="flex items-center space-x-2 mb-1">
                   <span v-if="post.is_top" class="px-1.5 py-0.5 bg-red-100 text-red-600 text-xs font-bold rounded">{{ t('post.top') }}</span>
                   <span v-if="post.is_hot" class="px-1.5 py-0.5 bg-orange-100 text-orange-600 text-xs font-bold rounded">{{ t('post.hot') }}</span>
                   <h3 class="text-xl font-semibold text-gray-900 group-hover:text-orange-600 transition-colors">{{ post.title }}</h3>
                </div>
                
                <p class="text-sm text-gray-500 mb-2 flex items-center">
                  <img 
                    :src="post.user?.avatar_url" 
                    class="w-4 h-4 rounded-full mr-1"
                    width="16"
                    height="16"
                    loading="lazy"
                  >
                  <span class="font-medium text-gray-700 mr-2">{{ post.user?.nickname || 'Unknown' }}</span> 
                  • {{ new Date(post.created_at * 1000).toLocaleDateString() }}
                </p>
                <p class="text-gray-600 text-sm line-clamp-2 break-words" v-html="post.content"></p>
              </div>
              <div class="flex space-x-4 text-gray-400 text-sm">
                <span class="flex items-center" :title="t('common.views')"><Eye class="w-4 h-4 mr-1" /> {{ post.n_views }}</span>
                <span class="flex items-center" :title="t('post.replies')"><MessageCircle class="w-4 h-4 mr-1" /> {{ post.n_replies }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Load More Button -->
        <div v-if="bcmHasMore" class="p-4 text-center mt-4">
          <button 
            @click="fetchBcmPosts(false)" 
            :disabled="loading"
            class="px-8 py-3 bg-white border border-orange-200 text-orange-600 rounded-full hover:bg-orange-50 hover:border-orange-300 transition shadow-sm text-sm font-medium disabled:opacity-50"
          >
            {{ loading ? t('common.loading') : t('forum.loadMoreOfficial') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create Post Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showCreateModal = false"></div>
      <div class="bg-white rounded-2xl w-full max-w-2xl p-6 shadow-2xl relative z-10 max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-gray-800">{{ t('forum.createTitle') }}</h2>
          <button @click="showCreateModal = false" class="text-gray-400 hover:text-gray-600">
            <X class="h-6 w-6" />
          </button>
        </div>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">{{ t('forum.titleLabel') }}</label>
            <input 
              v-model="newPost.title" 
              type="text" 
              :placeholder="t('forum.enterTitle')"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            >
          </div>
          
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">{{ t('forum.categoryLabel') }}</label>
            <select 
              v-model="newPost.category_id" 
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-white"
            >
              <option :value="null" disabled>{{ t('forum.selectCategory') }}</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">{{ t('forum.contentLabel') }}</label>
            <div class="border border-gray-300 rounded-lg overflow-hidden">
               <MarkdownEditor v-model="newPost.content" height="300px" />
            </div>
            <p class="text-xs text-gray-500 mt-1 text-right">{{ t('forum.markdownSupported') }}</p>
          </div>

          <div class="flex justify-end space-x-3 pt-4 border-t border-gray-100 mt-6">
            <button 
              @click="showCreateModal = false" 
              class="px-5 py-2 text-gray-600 font-medium hover:bg-gray-100 rounded-lg transition"
            >
              {{ t('forum.cancel') }}
            </button>
            <button 
              @click="handleCreatePost" 
              class="px-5 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 shadow-md hover:shadow-lg transition transform active:scale-95"
            >
              {{ t('forum.publish') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
