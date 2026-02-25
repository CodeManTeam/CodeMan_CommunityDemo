<script setup>
import { RouterLink, RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import GlobalAnnouncement from './components/GlobalAnnouncement.vue'
import { authState, logout } from './store'
import { useRouter } from 'vue-router'
import { useI18n } from './i18n'
import { ref, onMounted } from 'vue'

const router = useRouter()
const { t, locale, setLocale } = useI18n()
const showDevlog = ref(false)

// Devlog Configuration
const CURRENT_VERSION = '2026.02.25' // Update this date to trigger new devlog
const DEVLOG_CONTENT = [
  "🛡️ **举报功能**: 帖子详情页新增举报、编辑和删除功能（管理员）。",
  "🌍 **国际化支持**: 新增中英文切换功能。",
  "🔒 **安全升级**: 增强了反爬虫策略和登录加密机制。",
  "🐛 **Bug 修复**: 修复了作品提交时间线、论坛排序等问题。"
]

onMounted(() => {
  const lastVersion = localStorage.getItem('codeman_version')
  if (lastVersion !== CURRENT_VERSION) {
    showDevlog.value = true
  }
})

const closeDevlog = () => {
  showDevlog.value = false
  localStorage.setItem('codeman_version', CURRENT_VERSION)
}

const handleRelogin = () => {
  authState.showLoginModal = false
  logout()
  router.push('/login')
}

const handleCancelLogin = () => {
  authState.showLoginModal = false
  logout() // Still logout because token is invalid
}

const toggleLang = () => {
  setLocale(locale.value === 'zh' ? 'en' : 'zh')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans flex flex-col">
    <GlobalAnnouncement />
    <NavBar />
    <main class="container mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 flex-grow max-w-7xl">
      <RouterView />
    </main>
    <footer class="bg-white border-t border-gray-200 mt-12 py-8 text-center text-sm text-gray-500">
      <div class="flex flex-col items-center space-y-4">
        <a href="https://qm.qq.com/q/Py4iIbdHGu" target="_blank" class="text-blue-600 hover:underline font-bold text-base">
          点击链接加入群聊【BetterMao｜新生代编程猫创作者社区】
        </a>
        <p>{{ t('common.footerCopyright') }}</p>
        
        <div class="flex items-center space-x-4">
          <a href="https://github.com/CodeManTeam/CodeMan_CommunityDemo/releases/tag/Update" target="_blank" class="px-4 py-1.5 border border-gray-300 rounded-full hover:bg-gray-50 hover:text-gray-900 transition text-xs flex items-center space-x-2">
            <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path></svg>
            <span>{{ t('common.githubDemo') }}</span>
          </a>
          
          <button 
            @click="toggleLang"
            class="px-4 py-1.5 border border-gray-300 rounded-full hover:bg-gray-50 transition text-xs flex items-center space-x-2"
          >
            <span>🌐</span>
            <span>{{ locale === 'zh' ? 'English' : '中文' }}</span>
          </button>
        </div>
      </div>
    </footer>

    <!-- Session Expired Modal -->
    <div v-if="authState.showLoginModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-sm relative z-10 p-6 text-center transform scale-100 transition-all">
        <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ t('common.sessionExpired') }}</h3>
        <p class="text-gray-500 mb-6">{{ t('common.sessionExpiredDesc') }}</p>
        
        <div class="flex space-x-3">
          <button @click="handleCancelLogin" class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 font-bold rounded-lg hover:bg-gray-50 transition">
            {{ t('common.later') }}
          </button>
          <button @click="handleRelogin" class="flex-1 px-4 py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition shadow-lg">
            {{ t('common.loginNow') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Devlog Modal -->
    <div v-if="showDevlog" class="fixed inset-0 z-[110] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="closeDevlog"></div>
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md relative z-10 p-6 overflow-hidden animate-fade-in-up">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold text-gray-900 flex items-center">
            <span class="mr-2">📢</span> 
            <span>{{ t('common.whatsNew') }}</span>
            <span class="ml-2 text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">v{{ CURRENT_VERSION }}</span>
          </h3>
          <button @click="closeDevlog" class="text-gray-400 hover:text-gray-600 transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="space-y-3 mb-6">
          <div v-for="(log, index) in DEVLOG_CONTENT" :key="index" class="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 leading-relaxed border border-gray-100">
             <!-- Simple markdown-like rendering -->
             <span v-html="log.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')"></span>
          </div>
        </div>
        
        <button @click="closeDevlog" class="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-xl hover:shadow-lg transition transform hover:-translate-y-0.5">
          {{ t('common.gotIt') }}
        </button>
      </div>
    </div>
  </div>
</template>
