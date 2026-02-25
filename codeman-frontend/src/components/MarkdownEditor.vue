<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Write your content here...'
  },
  height: {
    type: String,
    default: '300px'
  }
})

const emit = defineEmits(['update:modelValue'])

const content = ref(props.modelValue || '')
const isPreview = ref(false)
const textareaRef = ref(null)

// Sync from parent
watch(() => props.modelValue, (val) => {
  if (val !== content.value) {
    content.value = val || ''
  }
})

// Sync to parent
watch(content, (val) => {
  emit('update:modelValue', val)
})

const parsedContent = computed(() => {
  if (!content.value) return ''
  try {
    // Pre-process [work:ID] to placeholders
    const text = content.value.replace(/\[work:(\d+)\]/g, '**(Work Card: $1)**')
    
    // Check parser availability
    const parser = marked.parse || marked
    if (typeof parser !== 'function') {
      throw new Error('Marked parser not found')
    }
    
    const html = parser(text)
    return DOMPurify.sanitize(html)
  } catch (e) {
    console.error("Markdown parsing error:", e)
    // Return error message visibly
    return `<div class="text-red-500 p-2 border border-red-200 rounded bg-red-50 text-sm">
      <strong>Rendering Error:</strong> ${e.message}<br>
      <span class="text-xs text-gray-500">Falling back to raw text...</span>
    </div><pre class="whitespace-pre-wrap text-sm text-gray-600 mt-2">${content.value}</pre>`
  }
})

const insertText = (before, after = '') => {
  const textarea = textareaRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  
  const currentVal = content.value || ''
  const selectedText = currentVal.substring(start, end)
  const replacement = before + selectedText + after
  
  content.value = currentVal.substring(0, start) + replacement + currentVal.substring(end)
  
  // Restore focus and selection
  // Need nextTick logic but setTimeout is simpler here
  setTimeout(() => {
    textarea.focus()
    textarea.setSelectionRange(start + before.length, end + before.length)
  }, 0)
}

const insertLink = () => {
  // Simple prompt for now, can be improved
  const url = prompt('Enter URL:')
  if (url) insertText('[Link Text](', `${url})`)
}

const insertImage = () => {
  const url = prompt('Enter Image URL:')
  if (url) insertText('![Image Alt](', `${url})`)
}

const insertWork = () => {
  const id = prompt('Enter Codemao Work ID (e.g., 123456):')
  if (id && /^\d+$/.test(id)) {
    insertText(`[work:${id}]`)
  } else if (id) {
    alert('Invalid Work ID. Must be numeric.')
  }
}

const toolbarItems = [
  { icon: '𝐁', label: 'Bold', action: () => insertText('**', '**') },
  { icon: '𝐼', label: 'Italic', action: () => insertText('*', '*') },
  { icon: '𝐇', label: 'Heading', action: () => insertText('### ') },
  { icon: '•', label: 'List', action: () => insertText('- ') },
  { icon: '', label: 'Code', action: () => insertText('`', '`') },
  { icon: '🔗', label: 'Link', action: insertLink },
  { icon: '🖼️', label: 'Image', action: insertImage },
  { icon: '🎮', label: 'Work', action: insertWork, title: 'Embed Codemao Work' },
]
</script>

<template>
  <div class="border border-gray-300 rounded-lg overflow-hidden bg-white flex flex-col transition-shadow focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 shadow-sm">
    <!-- Toolbar -->
    <div class="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-3 py-2">
      <div class="flex items-center space-x-1">
        <button 
          v-for="(item, index) in toolbarItems" 
          :key="index"
          @click.prevent="item.action"
          class="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition duration-200"
          :title="item.title || item.label"
          type="button"
        >
          <span class="text-lg w-6 h-6 flex items-center justify-center font-serif">{{ item.icon }}</span>
        </button>
      </div>
      
      <div class="flex bg-gray-200 rounded-lg p-0.5 text-xs font-medium">
        <button 
          @click.prevent="isPreview = false"
          class="px-3 py-1 rounded-md transition-all duration-200"
          :class="!isPreview ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          type="button"
        >
          Write
        </button>
        <button 
          @click.prevent="isPreview = true"
          class="px-3 py-1 rounded-md transition-all duration-200"
          :class="isPreview ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
          type="button"
        >
          Preview
        </button>
      </div>
    </div>

    <!-- Editor Area -->
    <div class="relative flex-1 bg-white">
      <textarea
        v-show="!isPreview"
        ref="textareaRef"
        v-model="content"
        :style="{ height: height }"
        class="w-full p-4 outline-none resize-none font-mono text-sm leading-relaxed text-gray-800"
        :placeholder="placeholder"
      ></textarea>
      
      <div 
        v-show="isPreview"
        :style="{ height: height }"
        class="w-full p-4 overflow-y-auto prose prose-sm max-w-none bg-white text-gray-800"
        v-html="parsedContent"
      ></div>
    </div>
    
    <div class="bg-gray-50 px-4 py-2 border-t border-gray-200 text-xs text-gray-500 flex justify-between items-center">
      <span class="flex items-center">
        <svg class="w-3 h-3 mr-1 text-gray-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>
        Markdown Supported
      </span>
      <a href="https://www.markdownguide.org/cheat-sheet/" target="_blank" class="hover:text-blue-600 hover:underline transition-colors">Syntax Guide</a>
    </div>
  </div>
</template>
