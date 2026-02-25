<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'
import { Eye, ThumbsUp, MessageCircle, ExternalLink, Download, Play, Share2, Heart, Reply, Trash2, Flag, X } from 'lucide-vue-next'

const route = useRoute()
const work = ref(null)
const loading = ref(true)
const error = ref('')

// Comment State
const commentContent = ref('')
const submittingComment = ref(false)
const replyTo = ref(null) // The comment being replied to

const fetchWork = async () => {
  loading.value = true
  try {
    // If authenticated, we need to pass the token to get "is_liked" status
    const headers = {}
    if (authState.isAuthenticated) {
        const token = authState.token || localStorage.getItem('token')
        if (token) headers['Authorization'] = `Bearer ${token}`
    }

    const res = await axios.get(`/api/works/${route.params.id}`, { headers })
    work.value = res.data
  } catch (e) {
    console.error("Failed to fetch work", e)
    error.value = "Work not found"
  } finally {
    loading.value = false
  }
}

const openCodemao = () => {
  if (work.value) {
    window.open(`https://shequ.codemao.cn/work/${work.value.work_id}`, '_blank')
  }
}

const openPlayer = () => {
  if (work.value) {
     window.open(`https://player.codemao.cn/new/${work.value.work_id}`, '_blank')
  }
}

const toggleWorkLike = async () => {
    if (!authState.isAuthenticated) {
        alert("Please login to like")
        return
    }
    
    try {
        const token = authState.token || localStorage.getItem('token')
        const res = await axios.post(`/api/works/${work.value.work_id}/like`, {}, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        
        work.value.is_liked = res.data.status === 'liked'
        work.value.likes_count = res.data.likes
    } catch (e) {
        console.error("Like failed", e)
        alert("Failed to like work")
    }
}

const setReply = (comment) => {
    replyTo.value = comment
    // Scroll to input
    document.getElementById('comment-input').scrollIntoView({ behavior: 'smooth' })
    document.getElementById('comment-input').focus()
}

const cancelReply = () => {
    replyTo.value = null
}

const submitComment = async () => {
  if (!authState.isAuthenticated) {
    alert("Please login to comment")
    return
  }
  
  if (!commentContent.value.trim()) return
  
  submittingComment.value = true
  const token = authState.token || localStorage.getItem('token')
  
  try {
    const payload = {
        content: commentContent.value,
        parent_id: replyTo.value ? replyTo.value.id : null
    }

    const res = await axios.post(`/api/works/${work.value.work_id}/comments`, payload, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    // Add new comment to list
    if (!work.value.comments) work.value.comments = []
    work.value.comments.unshift(res.data)
    
    // Update count
    work.value.comment_count = (work.value.comment_count || 0) + 1
    
    // Reset form
    commentContent.value = ''
    replyTo.value = null
  } catch (e) {
    console.error("Comment failed", e)
    alert(e.response?.data?.detail || "Failed to submit comment")
  } finally {
    submittingComment.value = false
  }
}

const toggleCommentLike = async (comment) => {
    if (!authState.isAuthenticated) {
        alert("Please login to like comments")
        return
    }
    
    try {
        const token = authState.token || localStorage.getItem('token')
        const res = await axios.post(`/api/works/comments/${comment.id}/like`, {}, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        
        comment.is_liked = res.data.status === 'liked'
        comment.likes = res.data.likes
    } catch (e) {
        console.error("Like comment failed", e)
    }
}

const deleteComment = async (comment) => {
    if (!confirm("Are you sure you want to delete this comment?")) return
    
    try {
        const token = authState.token || localStorage.getItem('token')
        await axios.delete(`/api/works/comments/${comment.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        
        // Remove from list or mark as deleted
        // Since backend soft deletes, let's just remove it from UI or mark it
        // Simpler to remove from UI for now
        work.value.comments = work.value.comments.filter(c => c.id !== comment.id)
        work.value.comment_count--
    } catch (e) {
        console.error("Delete failed", e)
        alert("Failed to delete comment")
    }
}

const reportComment = async (comment) => {
    const reason = prompt("Why are you reporting this comment?")
    if (!reason) return
    
    try {
        const token = authState.token || localStorage.getItem('token')
        await axios.post(`/api/works/comments/${comment.id}/report`, { reason }, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        alert("Comment reported. Thank you.")
    } catch (e) {
        console.error("Report failed", e)
        alert("Failed to report comment")
    }
}

const downloadingSource = ref(false)

const downloadSource = async () => {
  if (work.value.bcm_url) {
    window.open(work.value.bcm_url, '_blank')
    return
  }
  
  downloadingSource.value = true
  try {
    const res = await axios.get(`/api/works/${work.value.work_id}/source`)
    const sourceUrls = res.data.source_urls
    
    if (sourceUrls && sourceUrls.length > 0) {
      window.open(sourceUrls[0], '_blank')
    } else {
      alert("No source code found for this work.")
    }
  } catch (e) {
    console.error("Failed to download source", e)
    alert("Failed to retrieve source code. It might be private or deleted.")
  } finally {
    downloadingSource.value = false
  }
}

onMounted(() => {
  fetchWork()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-5xl">
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="error" class="text-center py-20 text-gray-500">
      {{ error }}
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left: Player/Preview -->
      <div class="lg:col-span-2 space-y-6">
        <div class="aspect-video bg-black rounded-xl overflow-hidden shadow-lg relative group">
          <iframe 
            :src="work.player_url || `https://player.codemao.cn/new/${work.work_id}`"
            class="w-full h-full border-0"
            allowfullscreen
          ></iframe>
        </div>
        
        <div class="bg-white p-8 rounded-xl border border-gray-100 shadow-sm">
          <div class="flex justify-between items-start mb-4">
              <h1 class="text-3xl font-extrabold text-gray-900 leading-tight">{{ work.work_name }}</h1>
              
              <!-- Work Like Button -->
              <button 
                @click="toggleWorkLike"
                class="flex items-center space-x-2 px-4 py-2 rounded-full transition"
                :class="work.is_liked ? 'bg-pink-50 text-pink-600' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'"
              >
                  <Heart class="w-6 h-6" :class="work.is_liked ? 'fill-current' : ''" />
                  <span class="font-bold">{{ work.likes_count }}</span>
              </button>
          </div>
          
          <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-6">
            <span class="flex items-center" title="Views"><Eye class="w-4 h-4 mr-1" /> {{ work.views_count }}</span>
             <span v-if="work.is_live" class="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-bold">Live Data</span>
          </div>
          
          <div class="prose prose-lg max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap">
            {{ work.description || 'No description provided.' }}
          </div>
        </div>
      </div>

      <!-- Right: Author & Stats -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Author Card -->
        <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
          <h3 class="font-bold text-gray-400 uppercase text-xs tracking-wide mb-4">Created By</h3>
          <div class="flex items-center space-x-4">
            <img :src="work.avatar_url || 'https://via.placeholder.com/48'" class="w-12 h-12 rounded-full border border-gray-100">
            <div>
              <div class="font-bold text-gray-900 text-lg">
                {{ work.nickname === 'Codemao System' && work.user_id === '0' ? 'Original Developer' : work.nickname }}
              </div>
              <div class="text-xs text-gray-500" v-if="work.user_id !== '0'">ID: {{ work.user_id }}</div>
            </div>
          </div>
          
          <div class="mt-6 flex flex-col space-y-2">
            <router-link 
              v-if="work.internal_user_id" 
              :to="`/user/${work.internal_user_id}`" 
              class="w-full py-2.5 bg-blue-50 text-blue-600 font-bold rounded-xl hover:bg-blue-100 transition text-center text-sm flex items-center justify-center"
            >
              <span class="mr-2">👤</span> View Community Profile
            </router-link>
            
            <a 
              :href="`https://shequ.codemao.cn/user/${work.user_id}`" 
              target="_blank"
              class="w-full py-2.5 border border-gray-200 text-gray-600 font-bold rounded-xl hover:bg-gray-50 transition text-center text-sm flex items-center justify-center"
            >
              <span class="mr-2">🐱</span> Codemao Profile
            </a>
          </div>
        </div>

        <!-- Actions -->
        <div class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-3">
          <button @click="openPlayer" class="w-full py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition shadow-lg hover:shadow-xl flex items-center justify-center space-x-2">
            <span>Open Player Window</span>
            <Play class="w-5 h-5" />
          </button>
        
          <button @click="openCodemao" class="w-full py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition shadow-lg hover:shadow-xl flex items-center justify-center space-x-2">
            <span>View on Codemao</span>
            <ExternalLink class="w-5 h-5" />
          </button>
          
          <button 
            @click="downloadSource"
            :disabled="downloadingSource"
            class="w-full py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 transition shadow-lg hover:shadow-xl flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-wait"
          >
            <span v-if="downloadingSource">Fetching Source...</span>
            <span v-else>Download Source (.bcm)</span>
            <Download v-if="!downloadingSource" class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Comments Section -->
    <div v-if="!loading && work" class="mt-16 max-w-4xl mx-auto">
      <h3 class="text-2xl font-bold text-gray-900 mb-8 flex items-center">
        Comments
        <span class="ml-3 bg-gray-100 text-gray-600 text-sm px-3 py-1 rounded-full font-bold">{{ work.comment_count || 0 }}</span>
      </h3>
      
      <!-- Comment Input -->
      <div v-if="authState.isAuthenticated && !work.is_live" class="mb-10 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h4 class="font-bold text-gray-800 mb-4">Leave a Comment</h4>
        
        <div v-if="replyTo" class="mb-3 flex items-center justify-between bg-blue-50 px-3 py-2 rounded text-sm text-blue-600">
            <span>Replying to <b>{{ replyTo.user.username }}</b></span>
            <button @click="cancelReply" class="hover:text-blue-800"><X class="w-4 h-4" /></button>
        </div>

        <textarea 
            id="comment-input"
            v-model="commentContent" 
            class="w-full p-4 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition bg-gray-50 resize-none h-32 mb-4" 
            :placeholder="replyTo ? `Replying to @${replyTo.user.username}...` : 'Share your thoughts about this work...'"
        ></textarea>
        <div class="flex justify-end">
            <button 
                @click="submitComment" 
                :disabled="submittingComment || !commentContent.trim()"
                class="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
            >
                {{ submittingComment ? 'Posting...' : 'Post Comment' }}
            </button>
        </div>
      </div>
      
      <div v-else-if="work.is_live" class="mb-10 p-6 bg-blue-50 rounded-xl text-blue-700 text-center border border-blue-100 font-medium">
         Comments are disabled for live preview works.
      </div>
      
      <div v-else class="mb-10 text-center py-10 bg-gray-50 rounded-xl border border-dashed border-gray-300">
        <p class="text-gray-500 mb-4 font-medium">Log in to leave a comment</p>
        <router-link to="/login" class="px-6 py-2.5 bg-white text-blue-600 font-bold rounded-xl border border-blue-200 hover:bg-blue-50 transition inline-block shadow-sm">
          Log In / Sign Up
        </router-link>
      </div>

      <!-- Comment List -->
      <div class="space-y-6">
        <div v-if="!work.comments || work.comments.length === 0" class="text-center text-gray-400 py-12">
          No comments yet. Be the first to comment!
        </div>
        <div v-else v-for="comment in work.comments" :key="comment.id" class="p-6 bg-white rounded-2xl border border-gray-100 shadow-sm transition hover:shadow-md">
           <div class="flex gap-4">
               <div class="flex-shrink-0">
                 <img :src="comment.user.avatar_url || 'https://via.placeholder.com/40'" class="w-10 h-10 rounded-full border border-gray-200 object-cover">
               </div>
               <div class="flex-grow">
                  <div class="flex items-center justify-between mb-2">
                     <div class="flex items-center gap-2">
                        <span class="font-bold text-gray-900">{{ comment.user.username }}</span>
                        <span class="text-xs text-gray-400">{{ new Date(comment.created_at).toLocaleDateString() }}</span>
                        <span v-if="comment.parent_id" class="text-xs text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded">Reply</span>
                     </div>
                  </div>
                  <p class="text-gray-700 leading-relaxed whitespace-pre-wrap mb-3">{{ comment.content }}</p>
                  
                  <!-- Comment Actions -->
                  <div class="flex items-center space-x-4 text-sm text-gray-500">
                      <button 
                        @click="toggleCommentLike(comment)" 
                        class="flex items-center space-x-1 transition"
                        :class="comment.is_liked ? 'text-pink-500' : 'hover:text-pink-500'"
                      >
                          <Heart class="w-4 h-4" :class="comment.is_liked ? 'fill-current' : ''" />
                          <span>{{ comment.likes || 0 }}</span>
                      </button>
                      
                      <button @click="setReply(comment)" class="flex items-center space-x-1 hover:text-blue-600 transition">
                          <Reply class="w-4 h-4" />
                          <span>Reply</span>
                      </button>
                      
                      <button @click="reportComment(comment)" class="flex items-center space-x-1 hover:text-yellow-600 transition ml-auto">
                          <Flag class="w-4 h-4" />
                          <span>Report</span>
                      </button>
                      
                      <button 
                        v-if="authState.user && (authState.user.id === comment.user.id || authState.user.is_admin)"
                        @click="deleteComment(comment)" 
                        class="flex items-center space-x-1 hover:text-red-600 transition"
                      >
                          <Trash2 class="w-4 h-4" />
                          <span>Delete</span>
                      </button>
                  </div>
               </div>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>
