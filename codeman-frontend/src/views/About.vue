<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto space-y-12">
      
      <!-- Hero Section -->
      <div class="text-center space-y-4">
        <h1 class="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl">
          {{ t('common.slogan') }}
        </h1>
        <p class="text-xl text-gray-500 max-w-2xl mx-auto">
          {{ t('common.mission') }}
        </p>
      </div>

      <!-- Features Grid -->
      <div class="grid grid-cols-1 gap-8 md:grid-cols-3">
        <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow">
          <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 text-blue-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">{{ t('common.featureSource') }}</h3>
          <p class="text-gray-500 text-sm">
            {{ t('common.featureSourceDesc') }}
          </p>
        </div>

        <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow">
          <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 text-green-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">{{ t('common.featureSafe') }}</h3>
          <p class="text-gray-500 text-sm">
            {{ t('common.featureSafeDesc') }}
          </p>
        </div>

        <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow">
          <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 text-purple-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">{{ t('common.featureApi') }}</h3>
          <p class="text-gray-500 text-sm">
            {{ t('common.featureApiDesc') }}
          </p>
        </div>
      </div>

      <!-- Developer & Maintainer -->
      <div class="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
        <div class="px-6 py-8 sm:p-10">
          <div class="sm:flex sm:items-center sm:justify-between">
            <div>
              <h3 class="text-lg leading-6 font-medium text-gray-900">
                {{ t('common.team') }}
              </h3>
              <div class="mt-2 max-w-xl text-sm text-gray-500">
                <p>{{ t('common.maintainer') }}</p>
              </div>
            </div>
            <div class="mt-5 sm:mt-0 sm:ml-6 sm:flex-shrink-0 sm:flex sm:items-center">
               <div class="flex items-center space-x-2">
                 <div class="h-10 w-10 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                   S
                 </div>
                 <span class="font-medium text-gray-900">Skyworld</span>
               </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Integration Info -->
      <div class="bg-indigo-50 rounded-2xl p-6 sm:p-10 border border-indigo-100">
        <h3 class="text-lg font-bold text-indigo-900 mb-4">{{ t('common.devService') }}</h3>
        <p class="text-indigo-700 mb-4">
          {{ t('common.devServiceDesc') }}
        </p>
        <div class="bg-white rounded-lg p-4 font-mono text-sm text-gray-600 border border-indigo-200 overflow-x-auto">
          <code>
            // 示例 SDK 调用<br>
            import CodeManAuth from '@codeman/auth-sdk';<br>
            <br>
            CodeManAuth.init({<br>
              appId: 'YOUR_APP_ID',<br>
              mode: 'iframe'<br>
            });
          </code>
        </div>
      </div>

      <!-- Acknowledgments -->
      <div class="text-center py-8">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">{{ t('common.ack') }}</h3>
        <div class="flex flex-wrap justify-center gap-4 text-gray-600 font-medium">
          <span class="bg-white px-4 py-2 rounded-full shadow-sm border border-gray-100">技术喵</span>
          <span class="bg-white px-4 py-2 rounded-full shadow-sm border border-gray-100">钻石</span>
          <span class="bg-white px-4 py-2 rounded-full shadow-sm border border-gray-100">编程猫作品自荐群全体成员</span>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { useI18n } from '../i18n'
const { t } = useI18n()
</script>
