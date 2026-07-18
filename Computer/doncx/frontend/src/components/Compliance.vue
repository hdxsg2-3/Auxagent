<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">合规审查</h2>
        <p class="text-sm text-slate-500 mt-2">智能检测文案风险，提前预警避免店铺处罚</p>
      </div>
    </div>

    <!-- 使用记录（本地持久化，刷新不丢） -->
    <div class="mb-7 card p-4">
      <div class="flex items-center justify-between">
        <button @click="showHistory = !showHistory" class="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-violet-600 transition-colors">
          <History class="w-4 h-4" />
          使用记录（{{ history.length }}）
        </button>
        <button v-if="history.length" @click="clearHistory" class="text-xs text-slate-400 hover:text-red-500 transition-colors">清空</button>
      </div>
      <div v-if="showHistory && history.length" class="mt-3 space-y-2 max-h-72 overflow-y-auto scrollbar-thin">
        <div
          v-for="item in history"
          :key="item.id"
          class="flex items-center justify-between gap-3 p-3 rounded-lg border border-slate-200 hover:border-violet-300 hover:bg-violet-50/50 transition-all"
        >
          <button @click="restoreHistory(item)" class="flex-1 text-left min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-xs px-2 py-0.5 rounded-full bg-violet-50 text-violet-600">审查</span>
              <span class="text-xs text-slate-400">{{ formatTime(item.created_at) }}</span>
              <span
                v-if="item.result && item.result.overall_risk"
                class="text-xs px-2 py-0.5 rounded-full"
                :class="item.result.overall_risk === 'high' ? 'bg-red-50 text-red-600' : item.result.overall_risk === 'medium' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'"
              >{{ item.result.overall_risk === 'high' ? '高' : item.result.overall_risk === 'medium' ? '中' : '低' }}</span>
            </div>
            <p class="text-sm text-slate-700 truncate mt-1">{{ historySummary(item) }}</p>
          </button>
          <button @click="removeHistory(item.id)" class="text-slate-300 hover:text-red-500 transition-colors shrink-0">
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>
      <p v-if="showHistory && !history.length" class="mt-3 text-sm text-slate-400">暂无使用记录，审查后会自动保存到这里</p>
    </div>

    <div class="grid grid-cols-2 gap-7">
      <div class="card p-7">
        <h3 class="text-lg font-bold text-slate-900 mb-6">审查内容输入</h3>

        <div class="space-y-6">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2.5">商品文案</label>
            <textarea
              v-model="form.content"
              class="input-field w-full h-48 p-4 text-sm resize-none"
              placeholder="请输入要审查的商品文案内容..."
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2.5">上传图片（可选）</label>
            <div class="border-2 border-dashed border-violet-200 rounded-xl p-6 text-center hover:border-violet-400 transition-colors cursor-pointer"
                 @click="triggerFileInput">
              <ImageIcon class="w-10 h-10 text-violet-400 mx-auto mb-3" />
              <p class="text-sm text-slate-500">点击或拖拽上传图片</p>
              <p class="text-xs text-slate-400 mt-1">支持 JPG、PNG、GIF 格式</p>
            </div>
            <input type="file" ref="fileInput" class="hidden" multiple accept="image/*" @change="handleFileSelect" />
          </div>

          <div v-if="form.images.length > 0" class="flex flex-wrap gap-2">
            <span v-for="(img, index) in form.images" :key="index"
                  class="px-3 py-1 bg-violet-50 text-violet-600 text-xs rounded-full">
              {{ img }}
            </span>
          </div>

          <div class="flex flex-wrap gap-3">
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="form.check_extreme_words" class="w-4 h-4 rounded border-violet-300 text-violet-600 focus:ring-violet-500" checked />
              <span class="text-sm font-medium text-slate-700">检测极限词</span>
            </label>
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="form.check_copyright" class="w-4 h-4 rounded border-violet-300 text-violet-600 focus:ring-violet-500" checked />
              <span class="text-sm font-medium text-slate-700">检测版权风险</span>
            </label>
            <label class="flex items-center gap-2.5 cursor-pointer">
              <input type="checkbox" v-model="form.check_forbidden_words" class="w-4 h-4 rounded border-violet-300 text-violet-600 focus:ring-violet-500" checked />
              <span class="text-sm font-medium text-slate-700">检测违禁词</span>
            </label>
          </div>

          <button
            @click="startCompliance"
            :disabled="loading"
            class="w-full py-3.5 rounded-xl flex items-center justify-center gap-2.5 text-sm font-semibold transition-all"
            :class="[
              loading
                ? 'bg-slate-400 cursor-not-allowed'
                : 'btn-primary'
            ]"
          >
            <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <ShieldCheck v-else class="w-5 h-5" />
            {{ loading ? '审查中...' : '开始审查' }}
          </button>
        </div>
      </div>

      <div class="card p-7">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-slate-900">审查结果</h3>
          <div v-if="result" class="flex items-center gap-2">
            <span :class="[
              result.overall_risk === 'high' ? 'tag-high' : '',
              result.overall_risk === 'medium' ? 'tag-medium' : '',
              result.overall_risk === 'low' ? 'tag-low' : ''
            ]" class="px-3 py-1 rounded-full text-xs font-semibold">
              {{ result.overall_risk === 'high' ? '高风险' : result.overall_risk === 'medium' ? '中风险' : '低风险' }}
            </span>
          </div>
        </div>

        <div v-if="!result" class="text-center py-16">
          <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-5">
            <ShieldCheck class="w-10 h-10 text-slate-400" />
          </div>
          <p class="text-slate-500 font-medium">输入文案后点击"开始审查"</p>
        </div>

        <div v-else class="space-y-6">
          <div v-if="result.extreme_words && result.extreme_words.length > 0">
            <h4 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <AlertTriangle class="w-4 h-4 text-red-500" />
              极限词检测
            </h4>
            <ul class="space-y-2">
              <li v-for="(item, index) in result.extreme_words" :key="index"
                  class="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <span class="text-sm text-red-700">{{ item.word }}</span>
                <span class="text-xs text-red-500">{{ item.suggestion }}</span>
              </li>
            </ul>
          </div>

          <div v-if="result.copyright_issues && result.copyright_issues.length > 0">
            <h4 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <Copyright class="w-4 h-4 text-amber-500" />
              版权风险检测
            </h4>
            <ul class="space-y-2">
              <li v-for="(item, index) in result.copyright_issues" :key="index"
                  class="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                <span class="text-sm text-amber-700">{{ item.description }}</span>
                <span class="text-xs text-amber-500">{{ item.risk_level }}</span>
              </li>
            </ul>
          </div>

          <div v-if="result.forbidden_words && result.forbidden_words.length > 0">
            <h4 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <XCircle class="w-4 h-4 text-orange-500" />
              违禁词检测
            </h4>
            <ul class="space-y-2">
              <li v-for="(item, index) in result.forbidden_words" :key="index"
                  class="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <span class="text-sm text-orange-700">{{ item.word }}</span>
                <span class="text-xs text-orange-500">{{ item.category }}</span>
              </li>
            </ul>
          </div>

          <div v-if="result.clean">
            <div class="text-center py-8">
              <div class="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <CheckCircle class="w-8 h-8 text-green-600" />
              </div>
              <p class="text-lg font-bold text-green-700">审查通过</p>
              <p class="text-sm text-green-500 mt-1">未发现风险问题</p>
            </div>
          </div>

          <div v-if="result.suggestions && result.suggestions.length > 0">
            <h4 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <Lightbulb class="w-4 h-4 text-violet-500" />
              优化建议
            </h4>
            <ul class="space-y-2">
              <li v-for="(suggestion, index) in result.suggestions" :key="index"
                  class="p-3 bg-violet-50 rounded-lg text-sm text-violet-700">
                {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ShieldCheck, Image as ImageIcon, AlertTriangle, Copyright, XCircle, CheckCircle, Lightbulb, History, Trash2 } from 'lucide-vue-next'
import { complianceAPI } from '../api/client'
import { ElMessage } from 'element-plus'
import { complianceHistoryAPI } from '../api/client'

const loading = ref(false)
const result = ref(null)
const fileInput = ref(null)

const form = reactive({
  content: '',
  images: [],
  check_extreme_words: true,
  check_copyright: true,
  check_forbidden_words: true
})

// ============ 使用记录（后端持久化） ============
const HISTORY_MAX = 50
const showHistory = ref(false)
const history = ref([])

async function loadHistory() {
  try {
    const res = await complianceHistoryAPI.list()
    if (res.data.success) {
      history.value = res.data.data
    }
  } catch (e) {
    console.error('加载审查历史失败', e)
  }
}

async function pushHistory(record) {
  try {
    await complianceHistoryAPI.add(record)
    await loadHistory()
  } catch (e) {
    console.error('保存审查历史失败', e)
  }
}

function restoreHistory(item) {
  form.content = item.content || ''
  const opt = item.options || {}
  form.check_extreme_words = opt.check_extreme_words !== false
  form.check_copyright = opt.check_copyright !== false
  form.check_forbidden_words = opt.check_forbidden_words !== false
  result.value = item.result
  showHistory.value = false
}

async function removeHistory(id) {
  try {
    await complianceHistoryAPI.remove(id)
    history.value = history.value.filter(h => h.id !== id)
  } catch (e) {
    console.error('删除历史失败', e)
  }
}

async function clearHistory() {
  try {
    await complianceHistoryAPI.clear()
    history.value = []
  } catch (e) {
    console.error('清空历史失败', e)
  }
}

function formatTime(value) {
  return value ? String(value) : ''
}

function historySummary(item) {
  const c = (item.content || '').trim()
  return c ? c.slice(0, 30) + (c.length > 30 ? '…' : '') : '空内容审查'
}

onMounted(() => {
  loadHistory()
})

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const files = event.target.files
  if (files) {
    form.images = Array.from(files).map(f => f.name)
    ElMessage.success(`已选择 ${files.length} 张图片`)
  }
}

async function startCompliance() {
  if (!form.content.trim()) {
    ElMessage.warning('请输入商品文案')
    return
  }

  loading.value = true
  result.value = null

  try {
    const response = await complianceAPI.scan(form)
    if (response.data.success) {
      result.value = response.data.data
      pushHistory({
        content: form.content,
        check_extreme_words: form.check_extreme_words,
        check_copyright: form.check_copyright,
        check_forbidden_words: form.check_forbidden_words,
        result: response.data.data
      })
      if (result.value.overall_risk === 'high') {
        ElMessage.warning('检测到高风险问题')
      } else if (result.value.overall_risk === 'medium') {
        ElMessage.info('检测到中风险问题')
      } else {
        ElMessage.success('审查通过，未发现风险')
      }
    } else {
      ElMessage.error(response.data.message || '审查失败')
    }
  } catch (error) {
    console.error(error)
    const errorMsg = error.response?.data?.message || error.message || '审查过程中发生错误'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>
