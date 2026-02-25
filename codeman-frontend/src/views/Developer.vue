
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../i18n'

const { t } = useI18n()
const router = useRouter()

const menuItems = [
  { id: 'docs', label: 'Documentation', icon: '📚', path: '/developer/docs' },
  { id: 'dashboard', label: 'My Apps', icon: '🚀', path: '/developer/dashboard' },
]
</script>

<template>
  <div class="flex flex-col md:flex-row gap-8 min-h-[600px]">
    <!-- Sidebar -->
    <div class="w-full md:w-64 flex-shrink-0">
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sticky top-24">
        <h2 class="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <span class="mr-2">🛠️</span> Developers
        </h2>
        
        <nav class="space-y-2">
          <router-link 
            v-for="item in menuItems" 
            :key="item.id"
            :to="item.path"
            class="flex items-center px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition"
            active-class="bg-blue-50 text-blue-600 font-bold"
          >
            <span class="mr-3">{{ item.icon }}</span>
            {{ item.label }}
          </router-link>
        </nav>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 p-8">
      <router-view></router-view>
    </div>
  </div>
</template>
