<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">图片处理</h2>
        <p class="text-sm text-slate-500 mt-2">上传图片调整尺寸，适配各平台要求</p>
      </div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-4">上传图片</h3>
        <div class="space-y-4">
          <div class="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-violet-400 transition-colors cursor-pointer" @click="$refs.fileInput.click()" @dragover.prevent @drop.prevent="onDrop">
            <input ref="fileInput" type="file" accept="image/*" @change="onFileSelect" class="hidden" />
            <Image class="w-12 h-12 text-slate-400 mx-auto mb-3" />
            <p class="text-sm text-slate-500">{{ file ? file.name : '点击或拖拽上传图片' }}</p>
          </div>
          <div v-if="file" class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs text-slate-500 mb-1">目标宽度</label>
              <input v-model.number="resizeW" type="number" class="input-field w-full px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">目标高度</label>
              <input v-model.number="resizeH" type="number" class="input-field w-full px-3 py-2 text-sm" />
            </div>
          </div>
          <button @click="doResize" :disabled="!file || processing" class="w-full py-3 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm" :class="processing?'bg-slate-400 cursor-not-allowed':'btn-primary'">
            {{ processing ? '处理中...' : '调整尺寸并下载' }}
          </button>
        </div>
        <div v-if="imgInfo" class="mt-4 text-xs text-slate-500 bg-slate-50 rounded-lg p-3">
          原图: {{ imgInfo.width }}x{{ imgInfo.height }}, {{ imgInfo.format }}, {{ imgInfo.size_kb }}KB
        </div>
      </div>
      <div class="card p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-4">各平台图片尺寸参考</h3>
        <div class="space-y-3 text-sm">
          <div v-for="p in sizeRef" :key="p.name" class="flex justify-between py-2 border-b border-slate-100">
            <span class="font-semibold text-slate-800">{{ p.name }}</span>
            <span class="text-slate-500">{{ p.size }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <div class="card p-6 mt-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2"><History class="w-5 h-5 text-violet-600" />历史记录</h3>
        <button v-if="imageHistory.length" @click="clearHistory" class="text-xs text-slate-400 hover:text-red-500 flex items-center gap-1"><Trash2 class="w-3.5 h-3.5" />清空</button>
      </div>
      <div v-if="!imageHistory.length" class="text-sm text-slate-400 py-4 text-center">暂无处理记录</div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="(h, i) in imageHistory" :key="i" class="bg-slate-50 rounded-lg p-3">
          <p class="text-sm font-medium text-slate-800 truncate" :title="h.name">{{ h.name }}</p>
          <p class="text-xs text-slate-500 mt-1">{{ h.original }} → {{ h.target }}</p>
          <p class="text-xs text-slate-400 mt-1">{{ h.created_at }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Image, History, Trash2 } from 'lucide-vue-next'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const file = ref(null)
const processing = ref(false)
const imgInfo = ref(null)
const resizeW = ref(1000)
const resizeH = ref(1000)

const IMAGE_HISTORY_KEY = 'gs_image_history'
const imageHistory = ref([])

function loadHistory() {
  try { imageHistory.value = JSON.parse(localStorage.getItem(IMAGE_HISTORY_KEY) || '[]') || [] }
  catch { imageHistory.value = [] }
}

function saveHistory() {
  localStorage.setItem(IMAGE_HISTORY_KEY, JSON.stringify((imageHistory.value || []).slice(0, 20)))
}

function clearHistory() {
  imageHistory.value = []
  saveHistory()
}

const sizeRef = [
  { name: 'Amazon 主图', size: '1000x1000(白底)' },
  { name: 'eBay 主图', size: '800x800(min)' },
  { name: 'Temu 主图', size: '800x800' },
  { name: '速卖通 主图', size: '800x800' },
  { name: 'Shopee 主图', size: '800x800' },
]

function onFileSelect(e) {
  file.value = e.target.files[0]
  e.target.value = ''
  loadInfo()
}
function onDrop(e) { file.value = e.dataTransfer.files[0]; loadInfo() }

async function loadInfo() {
  if (!file.value) return
  const fd = new FormData(); fd.append('image', file.value)
  try {
    const r = await axios.post('/api/image-tools/info', fd)
    if (r.data.success) imgInfo.value = r.data.data
    else ElMessage.error(r.data.message || '读取图片信息失败')
  } catch (e) {
    console.error(e)
    ElMessage.error('读取图片信息失败')
  }
}

async function doResize() {
  if (!file.value) return
  processing.value = true
  try {
    const fd = new FormData()
    fd.append('image', file.value)
    fd.append('width', resizeW.value)
    fd.append('height', resizeH.value)
    const r = await axios.post('/api/image-tools/resize', fd, { responseType: 'blob' })
    if (r.data?.type === 'application/json') {
      const text = await r.data.text()
      const err = JSON.parse(text)
      ElMessage.error(err.message || '处理失败')
      return
    }
    const url = URL.createObjectURL(r.data)
    const a = document.createElement('a')
    a.href = url; a.download = `resized_${file.value.name}`; a.click()
    URL.revokeObjectURL(url)
    imageHistory.value.unshift({
      name: file.value.name,
      original: imgInfo.value ? `${imgInfo.value.width}x${imgInfo.value.height}` : '-',
      target: `${resizeW.value}x${resizeH.value}`,
      created_at: new Date().toLocaleString()
    })
    saveHistory()
    ElMessage.success('下载完成')
  } catch (e) {
    console.error(e)
    ElMessage.error('处理失败：' + (e.message || '未知错误'))
  } finally { processing.value = false }
}

onMounted(loadHistory)
</script>
