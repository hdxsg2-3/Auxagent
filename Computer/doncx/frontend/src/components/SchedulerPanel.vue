<template>
  <div>
    <h2 class="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-2"><Clock class="w-6 h-6 text-violet-600" />自动巡检状态</h2>
    <div v-if="!tasks.length" class="text-center py-8 card"><p class="text-slate-500">暂无任务</p></div>
    <div class="space-y-4">
      <div v-for="task in tasks" :key="task.id" class="card p-5 flex items-center justify-between">
        <div>
          <div class="flex items-center gap-3 mb-1">
            <span class="font-bold text-slate-900">{{ task.description }}</span>
            <span class="px-2 py-0.5 rounded-full text-xs font-semibold" :class="task.status==='active'?'bg-emerald-100 text-emerald-700':'bg-slate-100 text-slate-600'">{{ task.status === 'active' ? '运行中' : '已暂停' }}</span>
          </div>
          <div class="text-xs text-slate-500 space-x-4">
            <span>间隔: {{ task.interval_minutes }}分钟</span>
            <span v-if="task.last_run">上次: {{ task.last_run }}</span>
            <span v-else>尚未运行</span>
          </div>
          <div v-if="task.last_result" class="text-xs text-slate-400 mt-1">结果: {{ task.last_result }}</div>
        </div>
        <div class="flex gap-2">
          <button @click="triggerRun(task.id)" :disabled="running===task.id" class="btn-primary px-3 py-1.5 rounded-lg text-xs">{{ running===task.id?'执行中...':'立即执行' }}</button>
          <button @click="toggleTask(task.id)" class="btn-outline px-3 py-1.5 rounded-lg text-xs">{{ task.status==='active'?'暂停':'恢复' }}</button>
        </div>
      </div>
    </div>

    <!-- 执行历史 -->
    <div class="card p-6 mt-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2"><History class="w-5 h-5 text-violet-600" />执行历史</h3>
        <button v-if="runHistory.length" @click="clearHistory" class="text-xs text-slate-400 hover:text-red-500 flex items-center gap-1"><Trash2 class="w-3.5 h-3.5" />清空</button>
      </div>
      <div v-if="!runHistory.length" class="text-sm text-slate-400 py-4 text-center">暂无手动执行记录</div>
      <div v-else class="space-y-3 max-h-80 overflow-y-auto pr-2">
        <div v-for="(h, i) in runHistory" :key="i" class="bg-slate-50 rounded-lg p-3">
          <div class="flex items-center justify-between mb-1">
            <span class="text-sm font-semibold text-slate-800">{{ h.description }}</span>
            <span class="text-xs px-2 py-0.5 rounded-full" :class="h.success ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">{{ h.success ? '成功' : '失败' }}</span>
          </div>
          <p class="text-xs text-slate-500 mb-1">{{ h.created_at }}</p>
          <p class="text-xs text-slate-700">{{ h.result }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Clock, History, Trash2 } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const api = axios.create({ baseURL: '/api/scheduler' })
const tasks = ref([])
const running = ref('')

const HISTORY_KEY = 'gs_scheduler_history'
const runHistory = ref([])

function loadHistory() {
  try { runHistory.value = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') || [] }
  catch { runHistory.value = [] }
}

function saveHistory() {
  localStorage.setItem(HISTORY_KEY, JSON.stringify((runHistory.value || []).slice(0, 30)))
}

function clearHistory() {
  runHistory.value = []
  saveHistory()
}

async function loadTasks() {
  try {
    const r = await api.get('/tasks')
    if (r.data.success) tasks.value = r.data.data
  } catch (e) { console.error(e) }
}

async function triggerRun(id) {
  running.value = id
  const task = tasks.value.find(t => t.id === id)
  try {
    const r = await api.post(`/tasks/${id}/run`)
    if (r.data.success) {
      ElMessage.success('执行完成：' + (r.data.result || ''))
    } else {
      ElMessage.error(r.data.message || '执行失败')
    }
    runHistory.value.unshift({
      task_id: id,
      description: task?.description || id,
      success: r.data.success,
      result: r.data.result || r.data.message || '',
      created_at: new Date().toLocaleString()
    })
    saveHistory()
    await loadTasks()
  } catch (e) {
    console.error(e)
    runHistory.value.unshift({
      task_id: id,
      description: task?.description || id,
      success: false,
      result: e.message || '网络错误',
      created_at: new Date().toLocaleString()
    })
    saveHistory()
    ElMessage.error('请求失败：' + (e.message || '网络错误'))
  } finally { running.value = '' }
}

async function toggleTask(id) {
  try {
    await api.post(`/tasks/${id}/toggle`)
    await loadTasks()
    ElMessage.success('状态已切换')
  } catch (e) { ElMessage.error('切换失败') }
}

onMounted(() => {
  loadTasks()
  loadHistory()
})
</script>
