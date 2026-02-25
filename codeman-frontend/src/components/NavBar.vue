<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { authState, logout as authLogout } from '../store'
import SearchBar from './SearchBar.vue'
import NotificationCenter from './NotificationCenter.vue'
import { useI18n } from '../i18n'
import { Menu, ShieldCheck, MessageCircle } from 'lucide-vue-next'

const router = useRouter()
const isMenuOpen = ref(false)
const { t } = useI18n()

const logout = () => {
  authLogout()
  router.push('/login')
  isMenuOpen.value = false
}
</script>

<template>
  <header class="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
    <div class="container mx-auto px-4 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <!-- Mobile Menu Button -->
        <button @click="isMenuOpen = !isMenuOpen" class="lg:hidden p-2 text-gray-600 hover:text-blue-600">
          <Menu class="w-6 h-6" />
        </button>

        <RouterLink to="/" class="flex items-center space-x-2">
          <span class="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent tracking-tight">CodeMan</span>
        </RouterLink>
      </div>
      
      <nav class="hidden lg:flex space-x-4 xl:space-x-6">
        <RouterLink to="/" class="text-gray-600 hover:text-blue-600 font-medium transition-colors whitespace-nowrap">{{ t('common.home') }}</RouterLink>
        <RouterLink to="/forum" class="text-gray-600 hover:text-blue-600 font-medium transition-colors whitespace-nowrap">{{ t('common.forum') }}</RouterLink>
        <RouterLink to="/showcase" class="text-gray-600 hover:text-blue-600 font-medium transition-colors whitespace-nowrap">{{ t('common.showcase') }}</RouterLink>
        <RouterLink to="/developer" class="text-gray-600 hover:text-blue-600 font-medium transition-colors whitespace-nowrap">{{ t('common.developer') }}</RouterLink>
        <RouterLink v-if="authState.isAdmin" to="/admin" class="flex items-center font-bold transition-colors whitespace-nowrap" :class="authState.user?.id === 1 ? 'text-red-600 hover:text-red-800' : 'text-blue-600 hover:text-blue-800'">
            <ShieldCheck class="w-4 h-4 mr-1" />
            <span class="hidden xl:inline">{{ authState.user?.id === 1 ? '站长' : '管理员' }}</span> {{ authState.user?.id === 1 ? 'SU' : 'Admin' }}
        </RouterLink>
        <RouterLink to="/about" class="text-gray-600 hover:text-blue-600 font-medium transition-colors whitespace-nowrap">{{ t('common.about') }}</RouterLink>
      </nav>
      
      <!-- Search Bar (Desktop) -->
      <div class="hidden lg:block w-48 xl:w-64 mx-4">
        <SearchBar />
      </div>

      <div class="flex items-center space-x-4">
        <NotificationCenter />
        
        <div v-if="authState.user" class="hidden md:flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <RouterLink :to="`/user/${authState.user.id}`" class="flex items-center space-x-2 hover:opacity-80 transition">
              <img :src="authState.user.avatar_url || 'https://via.placeholder.com/32'" alt="Avatar" class="w-8 h-8 rounded-full border border-gray-200 object-cover">
              <span class="text-sm font-medium text-gray-700 max-w-[100px] truncate">{{ authState.user.username }}</span>
            </RouterLink>
          </div>
          <button @click="logout" class="text-sm text-red-500 hover:text-red-700 font-medium whitespace-nowrap">{{ t('common.logout') }}</button>
        </div>
        <RouterLink v-else to="/login" class="px-5 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors font-medium text-sm shadow-md hover:shadow-lg transform hover:-translate-y-0.5 duration-200 whitespace-nowrap">
          {{ t('common.login') }}
        </RouterLink>
      </div>
    </div>

    <!-- Mobile Menu -->
    <div v-if="isMenuOpen" class="lg:hidden bg-white border-t border-gray-100 absolute w-full left-0 shadow-lg animate-fade-in-down z-50">
      <div class="p-4 space-y-4">
        <div class="mb-4">
          <SearchBar />
        </div>
        <nav class="flex flex-col space-y-2">
          <RouterLink @click="isMenuOpen = false" to="/" class="px-4 py-2 rounded-lg hover:bg-gray-50 text-gray-700 font-medium">{{ t('common.home') }}</RouterLink>
          <RouterLink @click="isMenuOpen = false" to="/forum" class="px-4 py-2 rounded-lg hover:bg-gray-50 text-gray-700 font-medium">{{ t('common.forum') }}</RouterLink>
          <RouterLink @click="isMenuOpen = false" to="/showcase" class="px-4 py-2 rounded-lg hover:bg-gray-50 text-gray-700 font-medium">{{ t('common.showcase') }}</RouterLink>
          <RouterLink @click="isMenuOpen = false" to="/developer" class="px-4 py-2 rounded-lg hover:bg-gray-50 text-gray-700 font-medium">{{ t('common.developer') }}</RouterLink>
          <RouterLink v-if="authState.isAdmin" @click="isMenuOpen = false" to="/admin" class="px-4 py-2 rounded-lg hover:bg-gray-50 font-bold flex items-center" :class="authState.user?.id === 1 ? 'text-red-600' : 'text-blue-600'">
             <ShieldCheck class="w-4 h-4 mr-2" />
             {{ authState.user?.id === 1 ? '站长 SU' : '管理员 Admin' }}
          </RouterLink>
          <RouterLink @click="isMenuOpen = false" to="/about" class="px-4 py-2 rounded-lg hover:bg-gray-50 text-gray-700 font-medium">{{ t('common.about') }}</RouterLink>
        </nav>
        
        <div v-if="authState.user" class="pt-4 border-t border-gray-100">
          <div class="flex items-center space-x-3 px-4 mb-3">
            <img :src="authState.user.avatar_url || 'https://via.placeholder.com/32'" class="w-10 h-10 rounded-full border border-gray-200">
            <div>
              <div class="font-bold text-gray-800">{{ authState.user.username }}</div>
              <div class="text-xs text-gray-500">{{ t('common.login') }}</div> 
            </div>
          </div>
          <RouterLink @click="isMenuOpen = false" :to="`/user/${authState.user.id}`" class="block px-4 py-2 text-gray-600 hover:text-blue-600">{{ t('common.profile') }}</RouterLink>
          <button @click="logout" class="w-full text-left px-4 py-2 text-red-600 font-medium">{{ t('common.logout') }}</button>
        </div>
      </div>
    </div>
  </header>
</template>
