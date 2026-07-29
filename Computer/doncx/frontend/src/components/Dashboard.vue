<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">工作台</h2>
        <p class="text-sm text-slate-500 mt-2">欢迎回来，深圳卖家 · 今天是 {{ currentDate }}</p>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      <div v-for="card in statCards" :key="card.key" class="card stat-card p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm font-medium text-slate-500">{{ card.label }}</span>
          <div class="stat-icon w-12 h-12 rounded-xl flex items-center justify-center" :class="card.iconBg">
            <component :is="card.icon" class="w-6 h-6" :class="card.iconColor" />
          </div>
        </div>
        <div class="flex items-end gap-2">
          <span v-if="loading" class="text-4xl font-bold text-slate-300">--</span>
          <span v-else class="text-4xl font-bold text-slate-900 animate-count">{{ card.today }}</span>
          <span class="text-xs bg-slate-100 px-2 py-0.5 rounded-full mb-1.5 font-medium text-slate-500">今日</span>
        </div>
        <p class="text-xs text-slate-400 mt-3">累计 {{ card.total }} 条</p>
      </div>
    </div>

    <!-- 物流状态概览 -->
    <div v-if="!loading && logisticsByStatus && Object.keys(logisticsByStatus).length" class="card p-6 mb-8">
      <h3 class="text-lg font-bold text-slate-900 mb-5">物流状态概览</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div
          v-for="(count, status) in logisticsByStatus"
          :key="status"
          class="text-center p-4 rounded-xl"
          :class="logisticsStatusBg(status)"
        >
          <p class="text-2xl font-bold">{{ count }}</p>
          <p class="text-xs mt-1 font-medium">{{ statusLabel(status) }}</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 快捷功能 -->
      <div class="lg:col-span-2 card p-7">
        <div class="flex items-center justify-between mb-7">
          <h3 class="text-lg font-bold text-slate-900">快捷功能</h3>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <button
            v-for="item in quickActions"
            :key="item.id"
            @click="navigate(item.id)"
            class="feature-card card p-6 flex flex-col items-center text-center group cursor-pointer"
          >
            <div
              class="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 shadow-xl transition-all group-hover:scale-110"
              :class="item.bgClass"
            >
              <component :is="item.icon" class="w-7 h-7 text-white" />
            </div>
            <span class="font-semibold text-slate-800">{{ item.label }}</span>
            <span class="text-xs text-slate-500 mt-1.5">{{ item.desc }}</span>
          </button>
        </div>
      </div>

      <!-- 近期动态 -->
      <div class="card p-6">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-bold text-slate-900">近期动态</h3>
          <span v-if="loading" class="text-xs text-slate-400">加载中...</span>
        </div>
        <div v-if="!activities.length && !loading" class="text-center py-10">
          <Clock class="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p class="text-sm text-slate-400">暂无活动记录</p>
        </div>
        <div v-else class="space-y-3 max-h-[420px] overflow-y-auto">
          <div
            v-for="(item, idx) in activities"
            :key="idx"
            class="flex items-start gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors"
          >
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
              :class="activityBg(item.color)"
            >
              <span class="w-2 h-2 rounded-full" :class="activityDot(item.color)"></span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-slate-800">{{ item.label }}</p>
              <p class="text-xs text-slate-500 truncate">{{ item.detail }}</p>
              <p class="text-xs text-slate-400 mt-1">{{ formatTime(item.time) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, inject } from 'vue'
import {
  PenTool, MessageSquare, ShieldCheck, Package, Clock, Store, FileText, Globe, Zap
} from 'lucide-vue-next'
import { dashboardAPI } from '../api/client'

const navigateTo = inject('navigateTo', () => {})

const loading = ref(true)
const stats = reactive({
  copywriter: { total: 0, today: 0 },
  compliance: { total: 0, today: 0 },
  customer_service: { total: 0, today: 0 },
  logistics: { total: 0, today: 0, by_status: {} }
})
const activities = ref([])
const logisticsByStatus = ref({})

const statCards = [
  { key: 'copywriter', label: '文案生成', icon: PenTool, iconBg: 'bg-gradient-to-br from-violet-50 to-purple-50', iconColor: 'text-violet-600' },
  { key: 'customer_service', label: '客服应答', icon: MessageSquare, iconBg: 'bg-gradient-to-br from-emerald-50 to-teal-50', iconColor: 'text-emerald-600' },
  { key: 'compliance', label: '合规审查', icon: ShieldCheck, iconBg: 'bg-gradient-to-br from-amber-50 to-orange-50', iconColor: 'text-amber-600' },
  { key: 'logistics', label: '物流单据', icon: Package, iconBg: 'bg-gradient-to-br from-purple-50 to-pink-50', iconColor: 'text-purple-600' }
]

const currentDate = ref(formatDate())
let dateTimer = null

function formatDate() {
  const now = new Date()
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  const t = timeStr.replace('T', ' ').slice(0, 16)
  const today = new Date().toISOString().slice(0, 10)
  if (timeStr.startsWith(today)) return '今天 ' + timeStr.slice(11, 16)
  return t
}

function statusLabel(s) {
  const map = { generated: '已生成', shipped: '已发货', in_transit: '运输中', customs_clearance: '清关中', out_for_delivery: '派送中', delivered: '已签收' }
  return map[s] || s
}

function logisticsStatusBg(s) {
  const map = {
    delivered: 'bg-green-50 text-green-700', shipped: 'bg-blue-50 text-blue-700',
    in_transit: 'bg-violet-50 text-violet-700', generated: 'bg-slate-50 text-slate-700',
    customs_clearance: 'bg-orange-50 text-orange-700', out_for_delivery: 'bg-yellow-50 text-yellow-700'
  }
  return map[s] || 'bg-slate-50 text-slate-700'
}

function activityBg(color) {
  const map = { violet: 'bg-violet-100', emerald: 'bg-emerald-100', amber: 'bg-amber-100', purple: 'bg-purple-100', blue: 'bg-blue-100' }
  return map[color] || 'bg-slate-100'
}

function activityDot(color) {
  const map = { violet: 'bg-violet-600', emerald: 'bg-emerald-600', amber: 'bg-amber-600', purple: 'bg-purple-600', blue: 'bg-blue-600' }
  return map[color] || 'bg-slate-600'
}

function navigate(pageId) {
  if (navigateTo) navigateTo(pageId)
}

const quickActions = [
  { id: 'copywriter', label: '文案生成', desc: '多语种智能生成', icon: PenTool, bgClass: 'bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-600 shadow-violet-900/20' },
  { id: 'compliance', label: '合规审查', desc: '风险检测预警', icon: ShieldCheck, bgClass: 'bg-gradient-to-br from-amber-500 via-orange-500 to-red-500 shadow-amber-900/20' },
  { id: 'customer-service', label: '客服应答', desc: '7x24自动回复', icon: MessageSquare, bgClass: 'bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 shadow-emerald-900/20' },
  { id: 'legal', label: '法规检索', desc: '海外合规查询', icon: FileText, bgClass: 'bg-gradient-to-br from-amber-500 via-yellow-500 to-lime-500 shadow-amber-900/20' },
  { id: 'logistics', label: '物流单据', desc: '一键生成单据', icon: Package, bgClass: 'bg-gradient-to-br from-purple-500 via-pink-500 to-rose-500 shadow-purple-900/20' },
  { id: 'platform-shops', label: '店铺管理', desc: '多平台店铺', icon: Store, bgClass: 'bg-gradient-to-br from-cyan-500 via-blue-500 to-indigo-500 shadow-cyan-900/20' }
]

async function loadData() {
  loading.value = true
  try {
    const [statsRes, activityRes] = await Promise.all([
      dashboardAPI.getStats().catch(() => ({ data: { success: false } })),
      dashboardAPI.getActivity().catch(() => ({ data: { success: false } }))
    ])

    if (statsRes.data.success) {
      Object.assign(stats, statsRes.data.data)
      logisticsByStatus.value = stats.logistics.by_status || {}
    }

    if (activityRes.data.success) {
      activities.value = activityRes.data.data || []
    }
  } catch (e) {
    console.error('Dashboard load error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  dateTimer = setInterval(() => { currentDate.value = formatDate() }, 60 * 1000)
  loadData()
})

onUnmounted(() => {
  if (dateTimer) clearInterval(dateTimer)
})
</script>
