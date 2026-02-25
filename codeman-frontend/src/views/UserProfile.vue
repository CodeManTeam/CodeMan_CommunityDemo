<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'
import { Eye, ThumbsUp, X, ShieldCheck } from 'lucide-vue-next'

const route = useRoute()
const user = ref(null)
const posts = ref([])
const loading = ref(true)
const error = ref('')

// Follow Modal State
const showFollowModal = ref(false)
const followModalTitle = ref('')
const followList = ref([])
const followLoading = ref(false)

const fetchUserProfile = async () => {
  loading.value = true
  error.value = ''
  user.value = null
  posts.value = []
  
  const userId = route.params.id
  const token = authState.token || localStorage.getItem('token')
  
  try {
    // 1. Fetch User Info (with Auth header for follow status)
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {}
    const userRes = await axios.get(`/api/users/${userId}`, {
      headers: headers
    })
    user.value = userRes.data
    
    // 2. Fetch User Posts
    const postsRes = await axios.get(`/api/users/${userId}/posts`)
    posts.value = postsRes.data
    
  } catch (e) {
    error.value = "User not found or connection failed."
    console.error(e)
  } finally {
    loading.value = false
  }
}

const toggleFollow = async () => {
  if (!authState.isAuthenticated) {
    alert("Please login to follow users")
    return
  }
  
  const token = authState.token || localStorage.getItem('token')
  if (!token) return

  // Prevent spamming
  if (user.value.followLoading) return
  user.value.followLoading = true

  try {
    if (user.value.is_following) {
      // Unfollow
      await axios.delete(`/api/users/${user.value.id}/follow`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      user.value.is_following = false
      user.value.followers_count = Math.max(0, user.value.followers_count - 1)
    } else {
      // Follow
      await axios.post(`/api/users/${user.value.id}/follow`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      user.value.is_following = true
      user.value.followers_count++
    }
  } catch (e) {
    console.error("Follow action failed", e)
    alert(e.response?.data?.detail || "Action failed")
  } finally {
    user.value.followLoading = false
  }
}

const openFollowList = async (type) => {
  if (!user.value) return
  
  followModalTitle.value = type === 'followers' ? 'Followers' : 'Following'
  showFollowModal.value = true
  followList.value = []
  followLoading.value = true
  
  try {
    const res = await axios.get(`/api/users/${user.value.id}/${type}`)
    followList.value = res.data
  } catch (e) {
    console.error(`Failed to fetch ${type}`, e)
    alert("Failed to load list")
  } finally {
    followLoading.value = false
  }
}

// Re-fetch when route ID changes (e.g. clicking another user profile)
watch(() => route.params.id, () => {
  fetchUserProfile()
})

onMounted(() => {
  fetchUserProfile()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-5xl">
    <div v-if="loading" class="text-center py-20 text-gray-500">
      Loading profile...
    </div>

    <div v-else-if="error" class="bg-red-50 text-red-600 p-8 rounded-xl text-center">
      {{ error }}
      <div class="mt-4">
        <router-link to="/" class="text-blue-600 hover:underline font-bold">Back to Home</router-link>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <!-- Left Sidebar: Profile Info -->
      <div class="md:col-span-1">
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden sticky top-24">
          <div class="h-32 bg-gradient-to-r from-blue-500 to-indigo-600"></div>
          <div class="px-6 pb-6">
            <div class="relative flex justify-center -mt-16 mb-4">
              <img 
                :src="user.avatar_url || 'https://via.placeholder.com/128'" 
                class="w-32 h-32 rounded-full border-4 border-white bg-white object-cover shadow-md"
                alt="Avatar"
              >
            </div>
            
            <div class="text-center mb-6">
              <div class="flex items-center justify-center space-x-2">
                <h1 class="text-2xl font-bold text-gray-900">{{ user.username }}</h1>
                <span v-if="user.id === 1" class="bg-red-500 text-white text-xs px-2 py-0.5 rounded font-bold flex items-center" title="Site Owner">
                    <ShieldCheck class="w-3 h-3 mr-1" /> SU
                </span>
                <span v-else-if="user.is_admin" class="bg-blue-500 text-white text-xs px-2 py-0.5 rounded font-bold flex items-center" title="Administrator">
                    <ShieldCheck class="w-3 h-3 mr-1" /> Admin
                </span>
              </div>
              <p class="text-gray-500 text-sm">Codemao ID: {{ user.codemao_id }}</p>
              
              <!-- Follow Button -->
              <div class="mt-4" v-if="authState.user && authState.user.id !== user.id">
                <button 
                  @click="toggleFollow"
                  class="px-6 py-2 rounded-full font-bold text-sm transition shadow-sm hover:shadow-md flex items-center justify-center mx-auto space-x-2"
                  :class="user.is_following 
                    ? 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'"
                >
                  <span v-if="user.is_following">Following</span>
                  <span v-else>Follow</span>
                </button>
              </div>
            </div>

            <div class="border-t border-gray-100 pt-4">
              <h3 class="text-xs font-bold text-gray-400 uppercase tracking-wide mb-2">About</h3>
              <p class="text-gray-600 text-sm leading-relaxed">
                {{ user.description || 'This user has not written a bio yet.' }}
              </p>
            </div>

            <div class="border-t border-gray-100 pt-4 mt-4 flex justify-around text-center">
               <div @click="openFollowList('followers')" class="cursor-pointer hover:text-blue-600 transition group">
                 <div class="font-bold text-gray-900 text-lg group-hover:text-blue-600">{{ user.followers_count || 0 }}</div>
                 <div class="text-xs text-gray-500 uppercase group-hover:text-blue-600">Followers</div>
               </div>
               <div class="w-px h-8 bg-gray-100"></div>
               <div @click="openFollowList('following')" class="cursor-pointer hover:text-blue-600 transition group">
                 <div class="font-bold text-gray-900 text-lg group-hover:text-blue-600">{{ user.following_count || 0 }}</div>
                 <div class="text-xs text-gray-500 uppercase group-hover:text-blue-600">Following</div>
               </div>
               <div class="w-px h-8 bg-gray-100"></div>
               <div>
                 <div class="font-bold text-gray-900 text-lg">{{ posts.length }}</div>
                 <div class="text-xs text-gray-500 uppercase">Posts</div>
               </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Content: Activity -->
      <div class="md:col-span-2 space-y-6">
        <h2 class="text-xl font-bold text-gray-800 flex items-center">
          <span>Recent Activity</span>
          <span class="ml-auto text-sm font-normal text-gray-500">Showing posts</span>
        </h2>

        <div v-if="posts.length === 0" class="bg-white p-12 rounded-xl border border-gray-100 text-center text-gray-400">
          No posts yet.
        </div>

        <div 
          v-for="post in posts" 
          :key="post.id" 
          @click="$router.push(`/forum/${post.id}`)"
          class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition cursor-pointer group"
        >
          <div class="flex justify-between items-start mb-2">
            <span class="text-xs font-medium px-2 py-1 bg-blue-50 text-blue-600 rounded-full">Discussion</span>
            <span class="text-xs text-gray-400">{{ new Date(post.created_at).toLocaleDateString() }}</span>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition">{{ post.title }}</h3>
          <p class="text-gray-600 text-sm line-clamp-2 mb-4">{{ post.content }}</p>
          
          <div class="flex items-center space-x-4 text-xs text-gray-500 border-t border-gray-50 pt-3">
             <span class="flex items-center space-x-1">
               <Eye class="w-3 h-3" /> <span>{{ post.views }}</span>
             </span>
             <span class="flex items-center space-x-1">
               <ThumbsUp class="w-3 h-3" /> <span>{{ post.likes }}</span>
             </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Follow List Modal -->
    <div v-if="showFollowModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="showFollowModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md h-[500px] flex flex-col">
        <div class="p-4 border-b border-gray-100 flex justify-between items-center">
            <h3 class="text-lg font-bold text-gray-900">{{ followModalTitle }}</h3>
            <button @click="showFollowModal = false" class="text-gray-500 hover:text-gray-700">
                <X class="w-5 h-5" />
            </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-4">
            <div v-if="followLoading" class="text-center py-8 text-gray-500">
                Loading...
            </div>
            
            <div v-else-if="followList.length === 0" class="text-center py-8 text-gray-400">
                No users found.
            </div>
            
            <div v-else class="space-y-3">
                <router-link 
                    v-for="u in followList" 
                    :key="u.id"
                    :to="`/user/${u.id}`"
                    @click="showFollowModal = false"
                    class="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded-lg transition"
                >
                    <img :src="u.avatar_url || 'https://via.placeholder.com/40'" class="w-10 h-10 rounded-full border border-gray-200">
                    <div>
                        <div class="font-bold text-gray-800">{{ u.username }}</div>
                        <div class="text-xs text-gray-500 line-clamp-1">{{ u.description || 'No bio' }}</div>
                    </div>
                </router-link>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>