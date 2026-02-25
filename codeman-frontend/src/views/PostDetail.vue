<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import MarkdownEditor from '../components/MarkdownEditor.vue'
import { useI18n } from '../i18n'
import { ThumbsUp, Eye, ShieldCheck, Trash2, MessageCircle, Heart, Reply, Flag, X } from 'lucide-vue-next'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const post = ref(null)
const comments = ref([])
const loading = ref(true)
const error = ref('')
const replyContent = ref('')
const submitting = ref(false)
const replyTo = ref(null)

const parsedContent = computed(() => {
  if (!post.value || !post.value.content) return ''
  const html = marked.parse(post.value.content)
  return DOMPurify.sanitize(html)
})

const renderMarkdown = (content) => {
    if (!content) return ''
    // Basic BBCode-like image support [img]url[/img]
    let processed = content.replace(/\[img\](.*?)\[\/img\]/g, '![]($1)')
    
    // Parse Markdown
    const html = marked.parse(processed)
    
    // Sanitize
    return DOMPurify.sanitize(html)
}

const fetchPost = async () => {
  loading.value = true
  try {
    const headers = {}
    if (authState.isAuthenticated) {
        const token = authState.token || localStorage.getItem('token')
        if (token) headers['Authorization'] = `Bearer ${token}`
    }

    const res = await axios.get(`/api/posts/${route.params.id}`, { headers })
    post.value = res.data
    
    // Fetch comments
    try {
      const commentsRes = await axios.get(`/api/posts/${route.params.id}/comments`, { headers })
      comments.value = commentsRes.data
    } catch (commentErr) {
      console.error("Failed to fetch comments", commentErr)
    }
    
  } catch (e) {
    error.value = "Failed to load post. It might have been deleted."
  } finally {
    loading.value = false
  }
}

const togglePostLike = async () => {
    if (!authState.isAuthenticated) {
        alert("Please login to like")
        return
    }
    
    try {
        const token = authState.token || localStorage.getItem('token')
        const res = await axios.post(`/api/posts/${post.value.id}/like`, {}, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        
        post.value.is_liked = res.data.status === 'liked'
        post.value.likes = res.data.likes
    } catch (e) {
        console.error("Like failed", e)
        alert("Failed to like post")
    }
}

const setReply = (comment) => {
    replyTo.value = comment
    // Scroll to editor
    document.querySelector('.markdown-editor-container').scrollIntoView({ behavior: 'smooth' })
}

const cancelReply = () => {
    replyTo.value = null
}

const submitComment = async () => {
  if (!replyContent.value.trim()) return
  
  const token = authState.token || localStorage.getItem('token')
  if (!token) {
    alert("Please login first")
    return
  }

  submitting.value = true
  try {
    const payload = {
        content: replyContent.value,
        parent_id: replyTo.value ? replyTo.value.id : null
    }

    const res = await axios.post(`/api/posts/${route.params.id}/comments`, payload, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    comments.value.unshift(res.data)
    replyContent.value = ''
    replyTo.value = null
  } catch (e) {
    alert("Failed to post comment: " + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

const toggleCommentLike = async (comment) => {
    if (!authState.isAuthenticated) {
        alert("Please login to like comments")
        return
    }
    
    try {
        const token = authState.token || localStorage.getItem('token')
        const res = await axios.post(`/api/posts/comments/${comment.id}/like`, {}, {
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
        await axios.delete(`/api/posts/${post.value.id}/comments/${comment.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        
        comments.value = comments.value.filter(c => c.id !== comment.id)
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
        await axios.post(`/api/posts/comments/${comment.id}/report`, { reason }, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        alert("Comment reported. Thank you.")
    } catch (e) {
        console.error("Report failed", e)
        alert("Failed to report comment")
    }
}

const deletePost = async () => {
  if (!confirm('Are you sure you want to delete this post?')) return
  try {
    const token = authState.token || localStorage.getItem('token')
    await axios.delete(`/api/posts/${post.value.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    router.push('/forum')
  } catch (e) {
    alert("Failed to delete post")
  }
}

onMounted(() => {
  fetchPost()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-4xl">
    <div v-if="loading" class="text-center py-12 text-gray-500">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      {{ t('common.loading') }}
    </div>

    <div v-else-if="error" class="bg-red-50 text-red-600 p-8 rounded-xl text-center border border-red-100">
      {{ error }}
    </div>

    <div v-else class="space-y-6">
      <article class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="p-8">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-4">
                <img :src="post.user.avatar_url || 'https://via.placeholder.com/48'" class="w-12 h-12 rounded-full border border-gray-200">
                <div>
                  <div class="flex items-center space-x-2">
                    <span class="font-bold text-gray-900 text-lg">{{ post.user.username }}</span>
                    <span v-if="post.user.id === 1" class="bg-red-500 text-white text-xs px-2 py-0.5 rounded font-bold flex items-center">
                        <ShieldCheck class="w-3 h-3 mr-1" /> SU
                    </span>
                    <span v-else-if="post.user.is_admin" class="bg-blue-500 text-white text-xs px-2 py-0.5 rounded font-bold flex items-center">
                        <ShieldCheck class="w-3 h-3 mr-1" /> Admin
                    </span>
                  </div>
                  <div class="text-sm text-gray-500">
                    {{ new Date(post.created_at).toLocaleString() }}
                  </div>
                </div>
            </div>
            
            <div v-if="authState.user && (authState.user.is_admin || authState.user.id === post.user.id)">
                <button @click="deletePost" class="flex items-center text-gray-400 hover:text-red-600 transition p-2 rounded-full hover:bg-red-50">
                    <Trash2 class="w-5 h-5" />
                </button>
            </div>
          </div>

          <h1 class="text-3xl font-extrabold text-gray-900 mb-6 break-words leading-tight">{{ post.title }}</h1>
          
          <!-- Post Content -->
          <div class="prose prose-lg max-w-none mb-8 text-gray-800 leading-relaxed break-words overflow-hidden" v-html="parsedContent"></div>
        </div>
        
        <div class="bg-gray-50 px-8 py-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-600">
          <div class="flex space-x-6">
            <div class="flex items-center space-x-2">
              <Eye class="w-5 h-5 text-gray-400" />
              <span>{{ post.views }} {{ t('common.views') }}</span>
            </div>
            
            <button 
                @click="togglePostLike"
                class="flex items-center space-x-2 transition cursor-pointer"
                :class="post.is_liked ? 'text-pink-600' : 'text-gray-600 hover:text-pink-600'"
            >
              <Heart class="w-5 h-5" :class="post.is_liked ? 'fill-current' : ''" />
              <span>{{ post.likes }} {{ t('common.likes') }}</span>
            </button>
            
            <div class="flex items-center space-x-2">
                <MessageCircle class="w-5 h-5 text-gray-400" />
                <span>{{ comments.length }} {{ t('post.comments') }}</span>
            </div>
          </div>
        </div>
      </article>

      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
        <h3 class="text-xl font-bold text-gray-900 mb-6 flex items-center">
            {{ t('post.comments') }} 
            <span class="ml-2 bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">{{ comments.length }}</span>
        </h3>
        
        <!-- Comment Input -->
        <div v-if="authState.isAuthenticated" class="mb-10 markdown-editor-container">
            <div v-if="replyTo" class="mb-3 flex items-center justify-between bg-blue-50 px-4 py-2 rounded-lg text-sm text-blue-600 border border-blue-100">
                <span class="flex items-center"><Reply class="w-4 h-4 mr-2" /> Replying to <b>{{ replyTo.user.username }}</b></span>
                <button @click="cancelReply" class="hover:bg-blue-100 p-1 rounded-full"><X class="w-4 h-4" /></button>
            </div>
            
            <MarkdownEditor v-model="replyContent" height="150px" :placeholder="replyTo ? `Replying to @${replyTo.user.username}...` : t('post.writeComment')" />
            
            <div class="flex justify-end mt-4">
                <button @click="submitComment" :disabled="submitting || !replyContent.trim()" class="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition shadow-sm disabled:opacity-50">
                    {{ submitting ? t('post.posting') : t('post.postComment') }}
                </button>
            </div>
        </div>
        
        <div v-else class="mb-10 text-center py-8 bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <p class="text-gray-500 mb-3">Please log in to participate in the discussion.</p>
            <router-link to="/login" class="text-blue-600 font-bold hover:underline">Log In / Sign Up</router-link>
        </div>

        <!-- Comments List -->
        <div class="space-y-6">
           <div v-if="comments.length === 0" class="text-center text-gray-400 py-8">
               No comments yet.
           </div>
           
           <div v-else v-for="comment in comments" :key="comment.id" class="flex gap-4 p-6 bg-gray-50 rounded-xl border border-gray-100 hover:border-gray-200 transition">
              <div class="flex-shrink-0">
                  <img :src="comment.user.avatar_url" class="w-10 h-10 rounded-full border border-gray-200 bg-white">
              </div>
              <div class="flex-grow min-w-0">
                 <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                       <span class="font-bold text-gray-900">{{ comment.user.username }}</span>
                       <span class="text-xs text-gray-400">{{ new Date(comment.created_at).toLocaleString() }}</span>
                       <span v-if="comment.parent_id" class="text-xs text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">Reply</span>
                    </div>
                 </div>
                 
                 <div class="text-gray-800 leading-relaxed whitespace-pre-wrap mb-3 prose prose-sm max-w-none break-words overflow-hidden" v-html="renderMarkdown(comment.content)"></div>
                 
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
