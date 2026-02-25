<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { authState } from '../store'

const router = useRouter()
const notifications = ref([])
const showDropdown = ref(false)
const unreadCount = ref(0)
let pollInterval = null

const fetchNotifications = async () => {
  if (!authState.isAuthenticated) return
  
  const token = authState.token || localStorage.getItem('token')
  if (!token) {
    console.warn("No token found for fetching notifications")
    return
  }

  try {
    const res = await axios.get('/api/notifications', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    notifications.value = res.data || []
    unreadCount.value = notifications.value.filter(n => !n.is_read).length
  } catch (e) {
    if (e.response && e.response.status === 401) {
       console.error("Token expired or invalid. Please login again.")
       // Optional: trigger logout if token is definitely invalid
       // import { logout } from '../store'; logout();
    }
    console.error("Failed to fetch notifications", e)
  }
}

const markAsRead = async (notification) => {
  if (notification.is_read) return
  
  const token = authState.token || localStorage.getItem('token')
  if (!token) return

  try {
    await axios.post(`/api/notifications/${notification.id}/read`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    notification.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (e) {
    console.error("Failed to mark read", e)
  }
}

const markAllRead = async () => {
  const token = authState.token || localStorage.getItem('token')
  if (!token) return

  try {
    await axios.post('/api/notifications/read-all', {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (e) {
    console.error("Failed to mark all read", e)
  }
}

const handleNotificationClick = async (notification) => {
  await markAsRead(notification)
  showDropdown.value = false
  
  if (notification.target_type === 'post') {
    router.push(`/forum/${notification.target_id}`)
  } else if (notification.target_type === 'work') {
    window.open(`https://shequ.codemao.cn/work/${notification.target_id}`, '_blank')
  }
}

onMounted(() => {
  fetchNotifications()
  // Poll every 30 seconds
  pollInterval = setInterval(fetchNotifications, 30000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="relative" v-if="authState.isAuthenticated">
    <button 
      @click="showDropdown = !showDropdown" 
      class="p-2 rounded-full hover:bg-gray-100 transition relative text-gray-600 hover:text-blue-600"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <span v-if="unreadCount > 0" class="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-red-100 transform translate-x-1/4 -translate-y-1/4 bg-red-600 rounded-full">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <div 
      v-if="showDropdown" 
      class="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden z-50 origin-top-right animate-fade-in-down"
    >
      <div class="p-3 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <h3 class="font-bold text-gray-700">Notifications</h3>
        <button 
          v-if="unreadCount > 0"
          @click="markAllRead" 
          class="text-xs text-blue-600 hover:underline font-medium"
        >
          Mark all read
        </button>
      </div>
      
      <div class="max-h-96 overflow-y-auto">
        <div v-if="notifications.length === 0" class="p-8 text-center text-gray-400 text-sm">
          No notifications yet
        </div>
        
        <div 
          v-for="notification in notifications" 
          :key="notification.id"
          @click="handleNotificationClick(notification)"
          class="p-4 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition cursor-pointer flex items-start space-x-3"
          :class="{'bg-blue-50/50': !notification.is_read}"
        >
          <img :src="notification.sender.avatar_url || 'https://via.placeholder.com/32'" class="w-8 h-8 rounded-full border border-gray-200 mt-1 object-cover flex-shrink-0">
          <div class="flex-1 min-w-0">
            <p class="text-sm text-gray-800 break-words">
              <span class="font-bold">{{ notification.sender.username }}</span> 
              {{ notification.message }}
            </p>
            <p class="text-xs text-gray-400 mt-1">{{ new Date(notification.created_at).toLocaleString() }}</p>
          </div>
          <div v-if="!notification.is_read" class="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
        </div>
      </div>
    </div>
    
    <!-- Backdrop -->
    <div 
      v-if="showDropdown" 
      class="fixed inset-0 z-40" 
      @click="showDropdown = false"
    ></div>
  </div>
</template>
