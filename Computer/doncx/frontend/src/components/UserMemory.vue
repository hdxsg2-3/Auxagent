<template>
  <div class="max-w-2xl">
    <h2 class="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-2"><Brain class="w-6 h-6 text-violet-600" />用户画像</h2>
    <p class="text-sm text-slate-500 mb-6">Agent 会记住你的偏好，提供更精准的建议</p>
    <div class="card p-6 space-y-5">
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-2">主营品类</label>
        <div class="flex flex-wrap gap-2">
          <span v-for="c in categories" :key="c" @click="toggleCategory(c)" class="px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-colors" :class="prefs.preferred_categories.includes(c) ? 'bg-violet-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'">{{ c }}</span>
        </div>
      </div>
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-2">偏好平台</label>
        <div class="flex gap-2">
          <span v-for="p in platforms" :key="p" @click="prefs.preferred_platform = p" class="px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-colors" :class="prefs.preferred_platform===p?'bg-emerald-600 text-white':'bg-slate-100 text-slate-600 hover:bg-slate-200'">{{ p }}</span>
        </div>
      </div>
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-2">偏好语种</label>
        <input v-model="prefs.preferred_language" class="input-field w-full px-4 py-2.5 text-sm" placeholder="如: en, es, de" />
      </div>
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-2">商店名称</label>
        <input v-model="prefs.store_name" class="input-field w-full px-4 py-2.5 text-sm" placeholder="你的跨境店名称" />
      </div>
      <button @click="save" :disabled="saving" class="btn-primary px-6 py-3 rounded-xl font-semibold">
        {{ saving ? '保存中...' : '保存偏好' }}
      </button>
      <div v-if="saved" class="text-xs text-emerald-600">✓ 已保存</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Brain } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'

const saving = ref(false)
const saved = ref(false)

const categories = ['电子产品', '家居用品', '服装', '美妆', '运动户外', '玩具', '汽配', '宠物用品']
const platforms = ['Amazon', 'eBay', 'Temu', '速卖通', 'Shopify']

const prefs = reactive({
  preferred_categories: JSON.parse(localStorage.getItem('user_prefs_categories') || '[]'),
  preferred_platform: localStorage.getItem('user_prefs_platform') || 'Amazon',
  preferred_language: localStorage.getItem('user_prefs_language') || 'en',
  store_name: localStorage.getItem('user_prefs_store') || '',
})

function toggleCategory(c) {
  const idx = prefs.preferred_categories.indexOf(c)
  if (idx >= 0) prefs.preferred_categories.splice(idx, 1)
  else prefs.preferred_categories.push(c)
}

function save() {
  saving.value = true
  localStorage.setItem('user_prefs_categories', JSON.stringify(prefs.preferred_categories))
  localStorage.setItem('user_prefs_platform', prefs.preferred_platform)
  localStorage.setItem('user_prefs_language', prefs.preferred_language)
  localStorage.setItem('user_prefs_store', prefs.store_name)
  setTimeout(() => { saving.value = false; saved.value = true; ElMessage.success('偏好已保存') }, 300)
}
</script>
