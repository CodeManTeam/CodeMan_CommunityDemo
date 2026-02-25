<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'
import TrendingSidebar from '../components/TrendingSidebar.vue'
import { useI18n } from '../i18n'
import { ArrowDown, ArrowUp } from 'lucide-vue-next'

const { t } = useI18n()

const route = useRoute()
const post = ref(null)
const replies = ref([])
const codemanComments = ref([])
const loading = ref(true)
const error = ref('')
const loadingReplies = ref(false)
const repliesPage = ref(1)
const hasMoreReplies = ref(true)
const activeTab = ref('codemao')
const sortOrder = ref('desc') // 'desc' or 'asc'

// CodeMan Comment State
const newComment = ref('')
const submittingComment = ref(false)

const fetchPost = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/bcm/posts/${route.params.id}`)
    post.value = res.data
    
    // Fetch initial replies
    await fetchReplies(true)
    await fetchCodemanComments()
  } catch (e) {
    console.error("Failed to fetch post", e)
    error.value = "Post not found or failed to load"
  } finally {
    loading.value = false
  }
}

const fetchReplies = async (reset = false) => {
  if (reset) {
    repliesPage.value = 1
    replies.value = []
    hasMoreReplies.value = true
  }
  
  if (!hasMoreReplies.value && !reset) return
  
  loadingReplies.value = true
  try {
    const limit = 20
    const offset = (repliesPage.value - 1) * limit
    const res = await axios.get(`/api/bcm/posts/${route.params.id}/replies`, {
      params: { limit, offset }
    })
    
    if (res.data.length < limit) {
      hasMoreReplies.value = false
    }
    
    replies.value = [...replies.value, ...res.data]
    repliesPage.value++
  } catch (e) {
    console.error("Failed to fetch replies", e)
  } finally {
    loadingReplies.value = false
  }
}

const fetchCodemanComments = async () => {
  try {
    const res = await axios.get(`/api/bcm/posts/${route.params.id}/codeman_comments`)
    codemanComments.value = res.data
  } catch (e) {
    console.error("Failed to fetch CodeMan comments", e)
  }
}

const submitCodemanComment = async () => {
  if (!authState.isAuthenticated) {
    alert("Please login to comment")
    return
  }
  
  if (!newComment.value.trim()) return
  
  submittingComment.value = true
  const token = authState.token || localStorage.getItem('token')
  
  try {
    const res = await axios.post(`/api/bcm/posts/${route.params.id}/codeman_comments`, {
      content: newComment.value
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    codemanComments.value.unshift(res.data)
    newComment.value = ''
  } catch (e) {
    console.error("Comment failed", e)
    alert(e.response?.data?.detail || "Failed to post comment")
  } finally {
    submittingComment.value = false
  }
}

// Simple parser for BCM rich text (which is often just HTML)
// The backend has already sanitized it using nh3
const parsedContent = computed(() => {
  if (!post.value || !post.value.content) return ''
  return post.value.content
})

const sortedReplies = computed(() => {
  if (!replies.value) return []
  return [...replies.value].sort((a, b) => {
    // BCM replies use unix timestamp or iso string? 
    // Usually BCM returns unix timestamp (seconds).
    // Let's check model or API. 
    // In routers/codemao_forum.py: created_at is passed through.
    // If it's a number, it's timestamp. If string, it's date string.
    // Let's assume it can be parsed by Date constructor or is a number.
    const tA = new Date(a.created_at * (typeof a.created_at === 'number' && a.created_at < 10000000000 ? 1000 : 1)).getTime()
    const tB = new Date(b.created_at * (typeof b.created_at === 'number' && b.created_at < 10000000000 ? 1000 : 1)).getTime()
    return sortOrder.value === 'desc' ? tB - tA : tA - tB
  })
})

const sortedCodemanComments = computed(() => {
  if (!codemanComments.value) return []
  return [...codemanComments.value].sort((a, b) => {
    const tA = new Date(a.created_at).getTime()
    const tB = new Date(b.created_at).getTime()
    return sortOrder.value === 'desc' ? tB - tA : tA - tB
  })
})

onMounted(() => {
  fetchPost()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-7xl">
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
    </div>

    <div v-else-if="error" class="text-center py-20 text-gray-500">
      {{ error }}
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-4 gap-8">
      <!-- Main Content -->
      <div class="lg:col-span-3">
        <!-- Post Header -->
        <div class="bg-white rounded-xl shadow-sm border border-orange-100 p-8 mb-6">
          <div class="flex items-center space-x-2 mb-4 text-sm text-gray-500">
            <span class="bg-orange-100 text-orange-600 px-2 py-0.5 rounded font-bold text-xs">{{ t('post.officialLabel') }}</span>
            <span>•</span>
            <span>{{ post.board_name }}</span>
            <span>•</span>
            <span>{{ new Date(post.created_at * 1000).toLocaleDateString() }}</span>
          </div>
        
        <h1 class="text-3xl font-bold text-gray-900 mb-6">{{ post.title }}</h1>
        
        <div class="flex items-center space-x-4 mb-8 pb-6 border-b border-gray-100">
          <img :src="post.user?.avatar_url || 'https://via.placeholder.com/48'" class="w-12 h-12 rounded-full border border-gray-200">
          <div>
            <div class="font-bold text-gray-900 text-lg">{{ post.user?.nickname || 'Unknown' }}</div>
            <div class="text-xs text-gray-500">{{ t('post.author') }}</div>
          </div>
        </div>
        
        <!-- Content -->
        <div class="prose prose-lg max-w-none text-gray-800 leading-relaxed mb-8 bcm-content" v-html="parsedContent">
        </div>
        
        <!-- Stats -->
        <div class="flex items-center space-x-6 text-gray-500 text-sm pt-6 border-t border-gray-100">
          <span class="flex items-center"><span class="mr-2 text-lg">👁️</span> {{ post.n_views }} {{ t('common.views') }}</span>
          <span class="flex items-center"><span class="mr-2 text-lg">💬</span> {{ post.n_replies }} {{ t('post.replies') }}</span>
        </div>
      </div>
    </div>

      <!-- Replies Section -->
      <div class="space-y-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-4">
            <h2 class="text-xl font-bold text-gray-800">{{ t('post.comments') }}</h2>
            
            <button 
              @click="sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'"
              class="flex items-center space-x-1 text-xs font-medium text-gray-500 hover:text-blue-600 transition px-2 py-1 rounded hover:bg-gray-100"
              :title="sortOrder === 'desc' ? 'Newest first' : 'Oldest first'"
            >
              <component :is="sortOrder === 'desc' ? ArrowDown : ArrowUp" class="w-3 h-3" />
              <span>{{ sortOrder === 'desc' ? 'Newest' : 'Oldest' }}</span>
            </button>
          </div>
          
          <!-- Comment Tabs -->
          <div class="flex bg-gray-100 p-1 rounded-lg">
             <button 
               @click="activeTab = 'codemao'"
               class="px-4 py-1.5 rounded-md text-sm font-medium transition"
               :class="activeTab === 'codemao' ? 'bg-white text-orange-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
             >
               {{ t('post.officialLabel') }}
             </button>
             <button 
               @click="activeTab = 'codeman'"
               class="px-4 py-1.5 rounded-md text-sm font-medium transition flex items-center space-x-1"
               :class="activeTab === 'codeman' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
             >
               <span>{{ t('post.specialLabel') }}</span>
               <span class="bg-blue-100 text-blue-600 text-xs px-1.5 rounded-full">{{ codemanComments.length }}</span>
             </button>
          </div>
        </div>
        
        <!-- Codemao Replies -->
        <div v-if="activeTab === 'codemao'">
          <div v-if="replies.length === 0 && !loadingReplies" class="text-center py-12 bg-gray-50 rounded-xl text-gray-500">
            {{ t('post.noOfficialReplies') }}
          </div>
          
          <div v-for="reply in sortedReplies" :key="reply.id" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-4">
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center space-x-3">
                <img :src="reply.user?.avatar_url || 'https://via.placeholder.com/40'" class="w-10 h-10 rounded-full border border-gray-100">
                <div>
                  <div class="font-bold text-gray-900">{{ reply.user?.nickname || 'Unknown' }}</div>
                  <div class="text-xs text-gray-400">{{ new Date(reply.created_at * 1000).toLocaleDateString() }}</div>
                </div>
              </div>
            </div>
            <div class="prose prose-sm max-w-none text-gray-700 leading-relaxed" v-html="reply.content"></div>
          </div>
          
          <!-- Load More -->
          <div v-if="hasMoreReplies" class="text-center py-4">
            <button 
              @click="fetchReplies(false)" 
              :disabled="loadingReplies"
              class="px-6 py-2 bg-white border border-gray-200 text-gray-600 rounded-full hover:bg-gray-50 transition text-sm font-medium disabled:opacity-50"
            >
              {{ loadingReplies ? t('common.loading') : t('forum.loadMore') }}
            </button>
          </div>
        </div>

        <!-- CodeMan Special Comments -->
        <div v-if="activeTab === 'codeman'">
          <!-- Comment Form -->
          <div v-if="authState.isAuthenticated" class="mb-8 bg-white p-6 rounded-xl border border-blue-100 shadow-sm">
            <textarea v-model="newComment" class="w-full p-4 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition bg-gray-50 focus:bg-white" rows="3" :placeholder="t('post.writeComment')"></textarea>
            <div class="flex justify-end mt-4">
              <button @click="submitCodemanComment" :disabled="submittingComment || !newComment.trim()" class="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition disabled:opacity-50 shadow-lg">
                {{ submittingComment ? t('post.posting') : t('post.postComment') }}
              </button>
            </div>
          </div>
          <div v-else class="mb-8 text-center py-8 bg-blue-50 rounded-xl border border-blue-100 border-dashed">
            <p class="text-blue-600 mb-2 font-medium">{{ t('post.joinExclusive') }}</p>
            <router-link to="/login" class="px-6 py-2 bg-white text-blue-600 font-bold rounded-lg border border-blue-200 hover:bg-blue-50 transition inline-block">
              {{ t('common.login') }}
            </router-link>
          </div>

          <!-- Comment List -->
          <div v-if="codemanComments.length === 0" class="text-center py-12 bg-gray-50 rounded-xl text-gray-500">
            {{ t('post.noSpecialComments') }}
          </div>
          
          <div v-for="comment in sortedCodemanComments" :key="comment.id" class="bg-white rounded-xl shadow-sm border border-blue-100 p-6 mb-4 relative overflow-hidden">
            <div class="absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl from-blue-50 to-transparent pointer-events-none"></div>
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center space-x-3">
                <img :src="comment.user.avatar_url || 'https://via.placeholder.com/40'" class="w-10 h-10 rounded-full border border-blue-100 p-0.5">
                <div>
                  <div class="font-bold text-gray-900 flex items-center">
                    {{ comment.user.username }}
                    <span class="ml-2 text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-bold uppercase">CodeMan</span>
                  </div>
                  <div class="text-xs text-gray-400">{{ new Date(comment.created_at).toLocaleDateString() }}</div>
                </div>
              </div>
            </div>
            <p class="text-gray-700 leading-relaxed whitespace-pre-wrap">{{ comment.content }}</p>
          </div>
        </div>
      </div>
      
      <!-- Sidebar -->
      <div class="hidden lg:block lg:col-span-1">
         <TrendingSidebar />
      </div>
    </div>
  </div>
</template>

<style>
/* Custom styles for BCM content to handle legacy HTML/CSS */
.bcm-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 1rem 0;
}
.bcm-content p {
  margin-bottom: 1em;
}
.bcm-content blockquote {
  border-left: 4px solid #f97316;
  padding-left: 1rem;
  font-style: italic;
  background: #fff7ed;
  padding: 0.5rem 1rem;
  border-radius: 0 8px 8px 0;
}
.bcm-content pre {
  background: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
}
.bcm-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}
.bcm-content th, .bcm-content td {
  border: 1px solid #e5e7eb;
  padding: 0.5rem;
}
.bcm-content th {
  background: #f9fafb;
}
</style>
