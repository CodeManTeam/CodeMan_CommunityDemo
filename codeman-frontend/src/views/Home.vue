<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useI18n } from '../i18n'

const router = useRouter()
const { t } = useI18n()
const works = ref([])
const banners = ref([])
const recentPosts = ref([])
const loading = ref(true)
const loadingPosts = ref(true)
const page = ref(1)
const limit = 20
const hasMore = ref(true)
const currentBannerIndex = ref(0)

const trendingPosts = ref([])
const trendingWorks = ref([])
const loadingTrending = ref(true)

// Fetch trending content
const fetchTrending = async () => {
  loadingTrending.value = true
  try {
    const [postsRes, worksRes] = await Promise.all([
      axios.get('/api/trending/posts'),
      axios.get('/api/trending/works')
    ])
    trendingPosts.value = postsRes.data
    trendingWorks.value = worksRes.data
  } catch (e) {
    console.error("Failed to fetch trending", e)
  } finally {
    loadingTrending.value = false
  }
}

// Fetch banners
const fetchBanners = async () => {
  try {
    const res = await axios.get('/api/banners')
    banners.value = res.data
  } catch (e) {
    console.error("Failed to fetch banners", e)
  }
}

// Fetch recent posts
const fetchPosts = async () => {
  loadingPosts.value = true
  try {
    const res = await axios.get('/api/posts?limit=5')
    recentPosts.value = res.data
  } catch (e) {
    console.error("Failed to fetch posts", e)
  } finally {
    loadingPosts.value = false
  }
}

// Fetch works from backend
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
  // Use internal route instead of external link
  router.push(`/work/${workId}`)
}

const downloadBcm = (url, event) => {
  event.stopPropagation()
  if (url) {
    window.open(url, '_blank')
  }
}

onMounted(async () => {
  fetchPosts()
  fetchWorks(true)
  fetchTrending()
  await fetchBanners()
  
  // Auto rotate banners
  setInterval(() => {
    if (banners.value.length > 0) {
      currentBannerIndex.value = (currentBannerIndex.value + 1) % banners.value.length
    }
  }, 5000)
})
</script>

<template>
  <div class="space-y-16">
    <!-- Hero Banner -->
    <section v-if="banners.length > 0" class="relative rounded-2xl overflow-hidden shadow-xl aspect-[2/1] md:aspect-[2.61/1] transform hover:scale-[1.01] transition duration-500">
      <div  
        v-for="(banner, index) in banners" 
        :key="banner.id"
        class="absolute inset-0 transition-opacity duration-1000 ease-in-out"
        :class="index === currentBannerIndex ? 'opacity-100 z-10' : 'opacity-0 z-0'"
      >
        <a :href="banner.target_url" target="_blank" class="block w-full h-full relative group">
          <picture>
            <source media="(max-width: 768px)" :srcset="banner.small_background_url">
            <img 
              :src="banner.background_url" 
              class="w-full h-full object-cover" 
              :alt="banner.title"
              :fetchpriority="index === 0 ? 'high' : 'auto'"
              :loading="index === 0 ? 'eager' : 'lazy'"
              width="1200"
              height="460"
            >
          </picture>
          
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex items-end p-6 md:p-10">
            <h2 class="text-white text-xl md:text-3xl font-bold opacity-90 group-hover:opacity-100 transition drop-shadow-md">{{ banner.title }}</h2>
          </div>
        </a>
      </div>
      
      <!-- Indicators -->
      <div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2 z-20">
        <button 
          v-for="(_, index) in banners" 
          :key="index"
          @click="currentBannerIndex = index"
          class="w-2 h-2 rounded-full transition-all duration-300"
          :class="index === currentBannerIndex ? 'bg-white w-6' : 'bg-white/50 hover:bg-white/80'"
        ></button>
      </div>
    </section>

    <!-- Fallback Hero if no banners -->
    <section v-else class="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-12 text-white shadow-xl text-center md:text-left">
      <h1 class="text-4xl md:text-5xl font-extrabold mb-4">{{ t('common.welcome') }}</h1>
      <p class="text-xl text-blue-100 mb-8 max-w-2xl">{{ t('common.welcomeDesc') }}</p>
      <div class="flex flex-col md:flex-row gap-4 justify-center md:justify-start">
        <button class="px-8 py-3 bg-white text-blue-700 font-bold rounded-lg hover:bg-gray-100 transition">{{ t('common.joinDiscussion') }}</button>
        <button class="px-8 py-3 bg-blue-500 bg-opacity-30 border border-blue-400 text-white font-bold rounded-lg hover:bg-opacity-40 transition">{{ t('common.exploreProjects') }}</button>
      </div>
    </section>
    
    <!-- Trending Section -->
    <section>
      <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
        <span class="mr-2">🔥</span> {{ t('common.trending') }}
      </h2>
      
      <div v-if="loadingTrending" class="text-center py-8 text-gray-500">{{ t('common.loading') }}</div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-10">
        <!-- Trending Posts -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 hover:shadow-md transition">
          <h3 class="font-bold text-gray-800 text-lg mb-6 border-b border-gray-100 pb-3 flex items-center">
            <span class="mr-2 text-2xl">💬</span> {{ t('common.hotDiscuss') }}
          </h3>
          <div class="space-y-6">
            <div v-for="(post, index) in trendingPosts" :key="post.id" class="flex items-start space-x-4 group p-3 hover:bg-gray-50 rounded-xl transition">
              <span class="text-xl font-bold text-gray-300 w-6 flex-shrink-0 text-center mt-0.5" :class="{'text-yellow-500': index === 0, 'text-gray-400': index === 1, 'text-orange-400': index === 2}">{{ index + 1 }}</span>
              <div class="flex-1 min-w-0">
                <router-link :to="`/forum/${post.id}`" class="text-gray-900 font-semibold text-lg hover:text-blue-600 line-clamp-1 block transition mb-1">
                  {{ post.title }}
                </router-link>
                <div class="flex items-center text-sm text-gray-500 mt-1 space-x-3">
                  <div class="flex items-center space-x-1.5">
                     <img :src="post.user?.avatar_url || 'https://via.placeholder.com/20'" class="w-5 h-5 rounded-full border border-gray-200">
                     <span class="truncate max-w-[100px]">{{ post.user?.username }}</span>
                  </div>
                  <span>•</span>
                  <span>{{ post.likes }} {{ t('common.likes') }}</span>
                  <span>•</span>
                  <span>{{ post.views }} {{ t('common.views') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Trending Works -->
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 hover:shadow-md transition">
          <h3 class="font-bold text-gray-800 text-lg mb-6 border-b border-gray-100 pb-3 flex items-center">
            <span class="mr-2 text-2xl">🎮</span> {{ t('common.hotWorks') }}
          </h3>
          <div class="space-y-6">
            <div v-for="(work, index) in trendingWorks" :key="work.id" class="flex items-center space-x-4 cursor-pointer group p-3 hover:bg-gray-50 rounded-xl transition" @click="openWork(work.id)">
              <span class="text-xl font-bold text-gray-300 w-6 flex-shrink-0 text-center" :class="{'text-yellow-500': index === 0, 'text-gray-400': index === 1, 'text-orange-400': index === 2}">{{ index + 1 }}</span>
              <div class="relative w-16 h-16 flex-shrink-0 shadow-sm rounded-lg overflow-hidden">
                <img 
                  :src="work.image_url" 
                  class="w-full h-full object-cover bg-gray-100 group-hover:scale-110 transition duration-500"
                  loading="lazy"
                  width="64"
                  height="64"
                >
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-gray-900 font-semibold text-lg group-hover:text-blue-600 truncate transition mb-1">
                  {{ work.title }}
                </div>
                <div class="text-sm text-gray-500 truncate flex items-center">
                  {{ work.subtitle }}
                </div>
              </div>
              <div class="text-gray-300 group-hover:text-blue-500 transition transform group-hover:translate-x-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Recent Discussions Section -->
    <section>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-800">{{ t('common.recentDiscuss') }}</h2>
        <router-link to="/forum" class="text-blue-600 hover:underline">{{ t('common.viewForum') }}</router-link>
      </div>
      
      <div v-if="loadingPosts" class="text-center py-8 text-gray-500">{{ t('common.loading') }}</div>
      
      <div v-else class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden divide-y divide-gray-100 hover:shadow-md transition">
        <div v-for="post in recentPosts" :key="post.id" class="p-8 hover:bg-gray-50 transition">
          <div class="flex items-start justify-between">
            <div>
              <router-link :to="`/forum/${post.id}`" class="text-xl font-bold text-gray-900 hover:text-blue-600 transition block mb-2">
                {{ post.title }}
              </router-link>
              <div class="flex items-center text-sm text-gray-500 space-x-4">
                <div class="flex items-center space-x-2">
                  <img 
                    :src="post.user.avatar_url || 'https://via.placeholder.com/24'" 
                    class="w-6 h-6 rounded-full border border-gray-200" 
                    alt="Avatar"
                    width="24"
                    height="24"
                    loading="lazy"
                  >
                  <span class="font-medium text-gray-700">{{ post.user.username }}</span>
                </div>
                <span>•</span>
                <span>{{ new Date(post.created_at).toLocaleDateString() }}</span>
                <span v-if="post.views > 0">• {{ post.views }} {{ t('common.views') }}</span>
              </div>
            </div>
            <span class="px-4 py-1.5 bg-blue-50 text-blue-700 text-xs font-bold rounded-full uppercase tracking-wide">
              {{ t('common.post') }}
            </span>
          </div>
        </div>
        
        <div v-if="recentPosts.length === 0" class="p-8 text-center text-gray-500">
          {{ t('common.noDiscussions') }}
        </div>
      </div>
    </section>

    <!-- Works Gallery -->
    <section>
      <div class="flex items-center justify-between mb-8">
        <h2 class="text-2xl font-bold text-gray-800">{{ t('common.featuredWorks') }}</h2>
        <router-link to="/showcase" class="text-blue-600 hover:underline">{{ t('common.viewShowcase') }}</router-link>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
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
          
          <!-- Work Info -->
          <div class="p-6 flex-1 flex flex-col">
            <h3 class="font-bold text-gray-800 mb-2 line-clamp-1 text-lg group-hover:text-blue-600 transition">{{ work.work_name }}</h3>
            
            <div class="flex items-center space-x-2.5 mb-5">
              <img 
                :src="work.avatar_url" 
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
                <span class="flex items-center" title="Views"><span class="mr-1">👁️</span> {{ work.views_count }}</span>
                <span class="flex items-center" title="Likes"><span class="mr-1">❤️</span> {{ work.likes_count }}</span>
              </div>
              
              <button 
                @click="downloadBcm(work.bcm_url, $event)"
                :disabled="!work.bcm_url"
                class="text-xs font-bold px-3 py-1.5 rounded-full transition-colors flex items-center space-x-1"
                :class="work.bcm_url ? 'bg-blue-50 text-blue-600 hover:bg-blue-100' : 'bg-gray-50 text-gray-400 cursor-not-allowed'"
                :title="t('common.download')"
              >
                <span>{{ t('common.download') }}</span>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Load More / Loading State -->
      <div class="text-center py-8">
        <div v-if="loading" class="text-gray-500 flex items-center justify-center space-x-2">
          <svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{{ t('common.loading') }}</span>
        </div>
        
        <button 
          v-else-if="hasMore"
          @click="loadMore"
          class="px-8 py-3 bg-white border border-gray-200 text-gray-700 font-bold rounded-full hover:bg-gray-50 hover:border-gray-300 transition shadow-sm hover:shadow"
        >
          {{ t('common.loadMore') }}
        </button>
        
        <p v-else class="text-gray-400 text-sm">
          {{ t('common.noMore') }}
        </p>
      </div>
    </section>
  </div>
</template>
