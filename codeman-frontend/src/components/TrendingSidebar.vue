<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useI18n } from '../i18n'

const { t } = useI18n()
const trendingPosts = ref([])
const trendingWorks = ref([])
const loading = ref(true)

const fetchTrending = async () => {
  loading.value = true
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
    loading.value = false
  }
}

const openWork = (id) => {
  window.open(`https://shequ.codemao.cn/work/${id}`, '_blank')
}

onMounted(() => {
  fetchTrending()
})
</script>

<template>
  <div class="space-y-6">
    <div v-if="loading" class="text-center py-8 text-gray-500">{{ t('common.loading') }}</div>
    
    <div v-else class="space-y-6">
      <!-- Trending Posts -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 class="font-bold text-gray-700 mb-4 border-b border-gray-100 pb-2 flex items-center">
          <span class="mr-2">🔥</span> {{ t('common.hotDiscuss') }}
        </h3>
        <div class="space-y-4">
          <div v-for="(post, index) in trendingPosts.slice(0, 5)" :key="post.id" class="flex items-start space-x-3 group">
            <span class="font-bold text-gray-300 w-4 flex-shrink-0 text-center" :class="{'text-yellow-500': index === 0, 'text-gray-400': index === 1, 'text-orange-400': index === 2}">{{ index + 1 }}</span>
            <div class="flex-1 min-w-0">
              <router-link :to="`/forum/${post.id}`" class="text-gray-900 text-sm font-medium hover:text-blue-600 line-clamp-2 transition">
                {{ post.title }}
              </router-link>
              <div class="text-xs text-gray-500 mt-1">
                {{ post.views }} {{ t('common.views') }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Trending Works -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 class="font-bold text-gray-700 mb-4 border-b border-gray-100 pb-2 flex items-center">
          <span class="mr-2">🎮</span> {{ t('common.hotWorks') }}
        </h3>
        <div class="space-y-4">
          <div v-for="(work, index) in trendingWorks.slice(0, 5)" :key="work.id" class="flex items-center space-x-3 cursor-pointer group" @click="openWork(work.id)">
            <span class="font-bold text-gray-300 w-4 flex-shrink-0 text-center" :class="{'text-yellow-500': index === 0, 'text-gray-400': index === 1, 'text-orange-400': index === 2}">{{ index + 1 }}</span>
            <img :src="work.image_url" class="w-10 h-10 rounded object-cover bg-gray-100">
            <div class="flex-1 min-w-0">
              <div class="text-gray-900 text-sm font-medium group-hover:text-blue-600 truncate transition">
                {{ work.title }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
