
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { authState } from '../store'
import { useRouter } from 'vue-router'
import MarkdownEditor from '../components/MarkdownEditor.vue'
import { Wrench, Megaphone, Users, Settings } from 'lucide-vue-next'

const router = useRouter()
const activeTab = ref('announcements') // announcements, users, settings

// Announcements State
const announcements = ref([])
const newAnnouncement = ref({ content: '', type: 'banner', active: true })

// Users State
const users = ref([])
const userSearch = ref('')
const userPage = ref(1)
const totalUsers = ref(0)
const limit = 20

// Settings State
const banScreenHtml = ref('')

// Loaders
const loading = ref(false)

onMounted(async () => {
  if (!authState.isAdmin) {
    router.push('/')
    return
  }
  loadAnnouncements()
})

const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'announcements') loadAnnouncements()
  if (tab === 'users') loadUsers()
  if (tab === 'settings') loadSettings()
}

// --- Announcements ---
const loadAnnouncements = async () => {
  const res = await axios.get('/api/announcements?active_only=false')
  announcements.value = res.data
}

const createAnnouncement = async () => {
  await axios.post('/api/admin/announcements', newAnnouncement.value)
  newAnnouncement.value = { content: '', type: 'banner', active: true }
  loadAnnouncements()
}

const toggleAnnouncement = async (ann) => {
  await axios.put(`/api/admin/announcements/${ann.id}`, {
    ...ann,
    active: !ann.active
  })
  loadAnnouncements()
}

const deleteAnnouncement = async (id) => {
  if (!confirm('Are you sure?')) return
  await axios.delete(`/api/admin/announcements/${id}`)
  loadAnnouncements()
}

// --- Users ---
const loadUsers = async () => {
  try {
    const res = await axios.get('/api/admin/users', {
      params: { q: userSearch.value, page: userPage.value, limit: limit }
    })
    users.value = res.data.items
    totalUsers.value = res.data.total
  } catch (e) {
    console.error("Failed to fetch users", e)
  }
}

const toggleBan = async (user) => {
  const reason = user.is_banned ? null : prompt("Reason for ban:")
  if (!user.is_banned && !reason) return

  try {
    await axios.post('/api/admin/users/ban', {
      user_id: user.id,
      is_banned: !user.is_banned,
      reason: reason
    })
    // Optimistic update or reload
    loadUsers()
  } catch (e) {
    alert("Failed to update ban status")
  }
}

const toggleAdmin = async (user) => {
  if (!confirm(`Are you sure you want to ${user.is_admin ? 'remove' : 'grant'} admin rights for ${user.username}?`)) return
  
  try {
    await axios.post('/api/admin/users/toggle_admin', {
      user_id: user.id,
      is_admin: !user.is_admin
    })
    loadUsers()
  } catch (e) {
    alert("Failed to update admin status")
  }
}

// --- Settings ---
const loadSettings = async () => {
  const res = await axios.get('/api/admin/settings/ban_screen')
  banScreenHtml.value = res.data.html
}

const saveBanScreen = async () => {
  await axios.post('/api/admin/settings/ban_screen', {
    key: 'ban_screen_html',
    value: banScreenHtml.value
  })
  alert('Saved!')
}
</script>

<template>
  <div class="min-h-screen bg-gray-100 p-8">
    <div class="max-w-6xl mx-auto">
      <div class="flex items-center justify-between mb-8">
        <h1 class="text-3xl font-bold text-gray-800 flex items-center">
            <Wrench class="w-8 h-8 mr-3 text-blue-600" />
            Admin Dashboard
        </h1>
        <router-link to="/" class="text-blue-600 hover:underline">Back to Site</router-link>
      </div>

      <div class="flex gap-6">
        <!-- Sidebar -->
        <div class="w-64 bg-white rounded-xl shadow-sm p-4 h-fit">
          <nav class="space-y-2">
            <button 
              @click="switchTab('announcements')"
              class="w-full text-left px-4 py-2 rounded-lg transition flex items-center"
              :class="activeTab === 'announcements' ? 'bg-blue-50 text-blue-600 font-bold' : 'hover:bg-gray-50 text-gray-600'"
            >
              <Megaphone class="w-5 h-5 mr-3" />
              Announcements
            </button>
            <button 
              @click="switchTab('users')"
              class="w-full text-left px-4 py-2 rounded-lg transition flex items-center"
              :class="activeTab === 'users' ? 'bg-blue-50 text-blue-600 font-bold' : 'hover:bg-gray-50 text-gray-600'"
            >
              <Users class="w-5 h-5 mr-3" />
              Users & Bans
            </button>
            <button 
              @click="switchTab('settings')"
              class="w-full text-left px-4 py-2 rounded-lg transition flex items-center"
              :class="activeTab === 'settings' ? 'bg-blue-50 text-blue-600 font-bold' : 'hover:bg-gray-50 text-gray-600'"
            >
              <Settings class="w-5 h-5 mr-3" />
              Settings
            </button>
          </nav>
        </div>

        <!-- Content -->
        <div class="flex-1 bg-white rounded-xl shadow-sm p-8">
          
          <!-- Announcements Tab -->
          <div v-if="activeTab === 'announcements'">
            <h2 class="text-xl font-bold mb-6">Manage Announcements</h2>
            
            <div class="bg-gray-50 p-4 rounded-lg mb-8 border border-gray-200">
              <h3 class="font-bold mb-2">New Announcement</h3>
              <div class="flex gap-4 mb-2">
                <input v-model="newAnnouncement.content" type="text" placeholder="Content" class="flex-1 p-2 border rounded">
                <select v-model="newAnnouncement.type" class="p-2 border rounded">
                  <option value="banner">Banner</option>
                  <option value="modal">Modal</option>
                  <option value="toast">Toast</option>
                </select>
                <button @click="createAnnouncement" class="px-4 py-2 bg-blue-600 text-white rounded font-bold">Create</button>
              </div>
            </div>

            <div class="space-y-4">
              <div v-for="ann in announcements" :key="ann.id" class="flex justify-between items-center p-4 border rounded-lg">
                <div>
                  <span class="font-bold mr-2" :class="ann.active ? 'text-green-600' : 'text-gray-400'">{{ ann.active ? 'ACTIVE' : 'INACTIVE' }}</span>
                  <span class="bg-gray-100 text-xs px-2 py-1 rounded mr-2 uppercase">{{ ann.type }}</span>
                  <span>{{ ann.content }}</span>
                </div>
                <div class="flex gap-2">
                  <button @click="toggleAnnouncement(ann)" class="text-sm px-3 py-1 border rounded hover:bg-gray-50">
                    {{ ann.active ? 'Deactivate' : 'Activate' }}
                  </button>
                  <button @click="deleteAnnouncement(ann.id)" class="text-sm px-3 py-1 border border-red-200 text-red-600 rounded hover:bg-red-50">Delete</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Users Tab -->
          <div v-if="activeTab === 'users'">
            <h2 class="text-xl font-bold mb-6">Manage Users</h2>
            
            <div class="mb-6 flex gap-2">
              <input 
                v-model="userSearch" 
                @keyup.enter="loadUsers"
                type="text" 
                placeholder="Search by username or ID..." 
                class="flex-1 p-2 border rounded"
              >
              <button @click="loadUsers" class="px-4 py-2 bg-gray-100 rounded font-bold">Search</button>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left">
                <thead>
                  <tr class="border-b text-gray-500 text-sm">
                    <th class="p-3">ID</th>
                    <th class="p-3">Username</th>
                    <th class="p-3">Role</th>
                    <th class="p-3">Status</th>
                    <th class="p-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="u in users" :key="u.id" class="border-b last:border-0 hover:bg-gray-50">
                    <td class="p-3">{{ u.id }}</td>
                    <td class="p-3 font-medium">{{ u.username }} <span class="text-gray-400 text-xs">({{ u.codemao_id }})</span></td>
                    <td class="p-3">
                      <span v-if="u.id === 1" class="text-red-600 font-bold text-xs bg-red-50 px-2 py-1 rounded">站长 SU</span>
                      <span v-else-if="u.is_admin" class="text-blue-600 font-bold text-xs bg-blue-50 px-2 py-1 rounded">管理员 Admin</span>
                      <span v-else class="text-gray-500 text-xs">User</span>
                    </td>
                    <td class="p-3">
                      <span v-if="u.is_banned" class="text-white bg-red-600 px-2 py-1 rounded text-xs font-bold">BANNED</span>
                      <span v-else class="text-green-600 text-xs font-bold">Active</span>
                    </td>
                    <td class="p-3 flex gap-2">
                      <button 
                        @click="toggleBan(u)"
                        class="text-xs font-bold px-3 py-1.5 rounded transition"
                        :class="u.is_banned ? 'bg-gray-200 text-gray-700' : 'bg-red-100 text-red-600 hover:bg-red-200'"
                      >
                        {{ u.is_banned ? 'Unban' : 'Ban' }}
                      </button>
                      <button 
                        v-if="authState.user?.id === 1 && u.id !== 1"
                        @click="toggleAdmin(u)"
                        class="text-xs font-bold px-3 py-1.5 rounded transition"
                        :class="u.is_admin ? 'bg-gray-200 text-gray-700' : 'bg-green-100 text-green-600 hover:bg-green-200'"
                      >
                        {{ u.is_admin ? 'Revoke Admin' : 'Make Admin' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Pagination -->
            <div class="mt-4 flex justify-between items-center text-sm text-gray-600">
                <button 
                    @click="userPage--; loadUsers()" 
                    :disabled="userPage === 1" 
                    class="px-4 py-2 border rounded disabled:opacity-50 hover:bg-gray-50 transition"
                >
                    Previous
                </button>
                <span>
                    Page {{ userPage }} of {{ Math.ceil(totalUsers / limit) || 1 }} (Total: {{ totalUsers }})
                </span>
                <button 
                    @click="userPage++; loadUsers()" 
                    :disabled="userPage * limit >= totalUsers" 
                    class="px-4 py-2 border rounded disabled:opacity-50 hover:bg-gray-50 transition"
                >
                    Next
                </button>
            </div>
          </div>

          <!-- Settings Tab -->
          <div v-if="activeTab === 'settings'">
            <h2 class="text-xl font-bold mb-6">Ban Screen Configuration</h2>
            <p class="text-gray-500 mb-4 text-sm">Enter the HTML content that will be displayed to banned users when they try to login.</p>
            
            <div class="border rounded-lg overflow-hidden mb-4">
              <!-- Using simple textarea for HTML editing -->
              <textarea v-model="banScreenHtml" class="w-full h-64 p-4 font-mono text-sm outline-none bg-gray-50" placeholder="<h1>You are banned</h1>..."></textarea>
            </div>
            
            <div class="flex justify-end">
              <button @click="saveBanScreen" class="px-6 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700">Save Settings</button>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>
