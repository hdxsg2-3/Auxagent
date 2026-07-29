<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">竞品分析</h2>
        <p class="text-sm text-slate-500 mt-2">输入竞品链接/ASIN/标题，AI 生成深度分析报告</p>
      </div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-4">输入竞品信息</h3>
        <div class="space-y-4">
          <input v-model="query" class="input-field w-full px-4 py-3 text-sm" placeholder="竞品链接、ASIN 或商品标题..." @keyup.enter="analyze" />
          <button @click="analyze" :disabled="loading || !query" class="w-full py-3 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm" :class="loading?'bg-slate-400 cursor-not-allowed':'btn-primary'">
            <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            {{ loading ? '分析中...' : '开始分析' }}
          </button>
        </div>
      </div>
      <div class="card p-6" v-if="result">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-slate-900">分析报告</h3>
          <span class="text-sm font-bold px-3 py-1 rounded-full bg-violet-100 text-violet-700">综合评分 {{ result.overall_score }}</span>
        </div>
        <p class="text-sm text-slate-600 mb-4">{{ result.product_summary }}</p>
        <div class="grid grid-cols-2 gap-4">
          <div><h4 class="text-xs font-bold text-emerald-700 mb-2">优势</h4><ul class="space-y-1"><li v-for="s in result.strengths" :key="s" class="text-xs text-slate-600 flex gap-1"><span class="text-emerald-500">+</span>{{ s }}</li></ul></div>
          <div><h4 class="text-xs font-bold text-red-600 mb-2">劣势</h4><ul class="space-y-1"><li v-for="w in result.weaknesses" :key="w" class="text-xs text-slate-600 flex gap-1"><span class="text-red-500">-</span>{{ w }}</li></ul></div>
        </div>
        <div class="mt-4"><h4 class="text-xs font-bold text-slate-700 mb-2">差异化建议</h4><ul class="space-y-1"><li v-for="d in result.differentiation_suggestions" :key="d" class="text-xs text-slate-600">• {{ d }}</li></ul></div>
        <div class="mt-4 text-xs text-slate-500">定价分析: {{ result.pricing_analysis }}</div>
      </div>
      <div v-else class="card p-6 flex items-center justify-center"><p class="text-sm text-slate-400">输入竞品信息查看分析报告</p></div>
    </div>

    <!-- 历史记录 -->
    <div class="card p-6 mt-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2"><History class="w-5 h-5 text-violet-600" />历史记录</h3>
        <button v-if="history.length" @click="clearHistory" class="text-xs text-slate-400 hover:text-red-500 flex items-center gap-1"><Trash2 class="w-3.5 h-3.5" />清空</button>
      </div>
      <div v-if="!history.length" class="text-sm text-slate-400 py-4 text-center">暂无分析记录</div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="(h, i) in history" :key="i" @click="restoreItem(h)" class="bg-slate-50 rounded-lg p-4 cursor-pointer hover:bg-violet-50 transition-colors">
          <div class="flex items-center justify-between mb-2">
            <p class="text-sm font-semibold text-slate-800 truncate flex-1" :title="h.query">{{ h.query }}</p>
            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-violet-100 text-violet-700">{{ h.score }}</span>
          </div>
          <p class="text-xs text-slate-500 line-clamp-2 mb-2">{{ h.summary }}</p>
          <p class="text-xs text-slate-400">{{ h.created_at }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { History, Trash2 } from 'lucide-vue-next'

const query = ref('')
const loading = ref(false)
const result = ref(null)

const HISTORY_KEY = 'gs_competitor_history'
const history = ref([])

function loadHistory() {
  try { history.value = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') }
  catch { history.value = [] }
}

function saveHistory() {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value.slice(0, 20)))
}

function clearHistory() {
  history.value = []
  saveHistory()
}

function restoreItem(item) {
  query.value = item.query
  result.value = item.result
}

async function analyze() {
  if (!query.value) return
  loading.value = true; result.value = null
  try {
    const r = await axios.post('/api/competitor/analyze', { title: query.value })
    if (r.data.success) {
      result.value = r.data.data
      history.value.unshift({
        query: query.value,
        result: r.data.data,
        summary: r.data.data.product_summary ? r.data.data.product_summary.slice(0, 60) + '...' : '',
        score: r.data.data.overall_score,
        created_at: new Date().toLocaleString()
      })
      saveHistory()
    }
    else ElMessage.error(r.data.message || '分析失败')
  } catch (e) { ElMessage.error('请求失败') }
  finally { loading.value = false }
}

onMounted(loadHistory)
</script>
