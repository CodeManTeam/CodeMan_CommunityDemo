
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Megaphone, Bell, X, Info } from 'lucide-vue-next'

const announcements = ref([])
const showModal = ref(false)
const modalContent = ref(null)

onMounted(async () => {
  try {
    const res = await axios.get('/api/announcements?active_only=true')
    announcements.value = res.data
    
    // Check for modal type
    const modalAnn = announcements.value.find(a => a.type === 'modal')
    if (modalAnn) {
        // Check if already seen in session
        if (!sessionStorage.getItem(`seen_announcement_${modalAnn.id}`)) {
            modalContent.value = modalAnn
            showModal.value = true
        }
    }
  } catch (err) {
    console.error(err)
  }
})

const closeBanner = (id) => {
    announcements.value = announcements.value.filter(a => a.id !== id)
}

const closeToast = (id) => {
    // Just hide it from view, effectively "closing" it for this session refresh
    announcements.value = announcements.value.filter(a => a.id !== id)
}

const closeModal = () => {
    if (modalContent.value) {
        sessionStorage.setItem(`seen_announcement_${modalContent.value.id}`, 'true')
    }
    showModal.value = false
}
</script>

<template>
  <div class="z-[90]">
    <!-- Banners (Top of screen) -->
    <div class="flex flex-col space-y-2 mb-4">
        <div 
        v-for="ann in announcements.filter(a => a.type === 'banner')" 
        :key="ann.id"
        class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3 shadow-md flex justify-between items-center relative overflow-hidden"
        >
        <div class="absolute inset-0 bg-white/5 pattern-dots"></div>
        <div class="container mx-auto flex justify-between items-center relative z-10">
            <div class="flex items-center space-x-3">
                <Megaphone class="w-6 h-6" />
                <span class="font-medium font-sans">{{ ann.content }}</span>
            </div>
            <button @click="closeBanner(ann.id)" class="text-white/80 hover:text-white transition rounded-full p-1 hover:bg-white/10">
                <X class="w-5 h-5" />
            </button>
        </div>
        </div>
    </div>

    <!-- Toasts (Bottom Right) -->
    <div class="fixed bottom-4 right-4 z-[100] flex flex-col space-y-3 pointer-events-none">
        <div 
            v-for="ann in announcements.filter(a => a.type === 'toast')" 
            :key="ann.id"
            class="bg-white border-l-4 border-blue-500 shadow-xl rounded-r-lg p-4 max-w-sm flex items-start space-x-3 pointer-events-auto transform transition-all animate-slide-in-right"
        >
            <div class="text-blue-500 mt-0.5">
                <Info class="w-5 h-5" />
            </div>
            <div class="flex-1">
                <p class="text-gray-800 text-sm font-medium">{{ ann.content }}</p>
            </div>
            <button @click="closeToast(ann.id)" class="text-gray-400 hover:text-gray-600 transition">
                <X class="w-4 h-4" />
            </button>
        </div>
    </div>

    <!-- Modal (Overlay) -->
    <div v-if="showModal && modalContent" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" @click="closeModal"></div>
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg relative z-10 p-8 transform scale-100 transition-all animate-bounce-in">
            <div class="absolute top-4 right-4">
                <button @click="closeModal" class="text-gray-400 hover:text-gray-600 transition">
                    <X class="w-6 h-6" />
                </button>
            </div>
            
            <div class="text-center">
                <div class="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Bell class="w-8 h-8" />
                </div>
                <h3 class="text-2xl font-bold text-gray-900 mb-4">Notification</h3>
                <div class="prose prose-blue mx-auto text-gray-600 mb-8">
                    <p class="whitespace-pre-wrap">{{ modalContent.content }}</p>
                </div>
                
                <button @click="closeModal" class="px-8 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition shadow-lg hover:shadow-xl transform active:scale-95">
                    Close
                </button>
            </div>
        </div>
    </div>
  </div>
</template>
