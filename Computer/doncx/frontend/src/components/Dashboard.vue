<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">工作台</h2>
        <p class="text-sm text-slate-500 mt-2">欢迎回来，深圳卖家 · 今天是 2024年1月15日</p>
      </div>
      <button class="btn-primary flex items-center gap-2 px-6 py-3 rounded-xl font-semibold">
        <PlusCircle class="w-5 h-5" />
        新建任务
      </button>
    </div>

    <div class="grid grid-cols-4 gap-5 mb-8">
      <div class="card stat-card p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm font-medium text-slate-500">文案生成</span>
          <div class="stat-icon w-12 h-12 rounded-xl bg-gradient-to-br from-violet-50 to-purple-50 flex items-center justify-center">
            <PenTool class="w-6 h-6 text-violet-600" />
          </div>
        </div>
        <div class="flex items-end gap-2">
          <span class="text-4xl font-bold text-slate-900">28</span>
          <span class="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full mb-1.5 font-medium">+12%</span>
        </div>
        <p class="text-xs text-slate-400 mt-3">今日完成</p>
      </div>

      <div class="card stat-card p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm font-medium text-slate-500">客服回复</span>
          <div class="stat-icon w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center">
            <MessageSquare class="w-6 h-6 text-emerald-600" />
          </div>
        </div>
        <div class="flex items-end gap-2">
          <span class="text-4xl font-bold text-slate-900">156</span>
          <span class="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full mb-1.5 font-medium">+8%</span>
        </div>
        <p class="text-xs text-slate-400 mt-3">今日完成</p>
      </div>

      <div class="card stat-card p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm font-medium text-slate-500">合规审查</span>
          <div class="stat-icon w-12 h-12 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50 flex items-center justify-center">
            <ShieldCheck class="w-6 h-6 text-amber-600" />
          </div>
        </div>
        <div class="flex items-end gap-2">
          <span class="text-4xl font-bold text-slate-900">12</span>
          <span class="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full mb-1.5 font-medium">持平</span>
        </div>
        <p class="text-xs text-slate-400 mt-3">今日完成</p>
      </div>

      <div class="card stat-card p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm font-medium text-slate-500">单据生成</span>
          <div class="stat-icon w-12 h-12 rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center">
            <Package class="w-6 h-6 text-purple-600" />
          </div>
        </div>
        <div class="flex items-end gap-2">
          <span class="text-4xl font-bold text-slate-900">8</span>
          <span class="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full mb-1.5 font-medium">+5%</span>
        </div>
        <p class="text-xs text-slate-400 mt-3">今日完成</p>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <div class="col-span-2 card p-7">
        <div class="flex items-center justify-between mb-7">
          <h3 class="text-lg font-bold text-slate-900">快捷功能</h3>
          <a href="#" class="text-sm text-violet-600 hover:text-violet-700 font-medium">查看全部</a>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <button
            v-for="item in quickActions"
            :key="item.id"
            @click="$emit('navigate', item.id)"
            class="feature-card card p-6 flex flex-col items-center text-center group cursor-pointer"
          >
            <div class="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 shadow-xl transition-all group-hover:scale-110"
                 :class="item.bgClass">
              <component :is="item.icon" class="w-7 h-7 text-white" />
            </div>
            <span class="font-semibold text-slate-800">{{ item.label }}</span>
            <span class="text-xs text-slate-500 mt-1.5">{{ item.desc }}</span>
          </button>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-bold text-slate-900">近期提醒</h3>
          <Bell class="w-5 h-5 text-slate-400" />
        </div>
        <div class="space-y-4">
          <div class="p-4 bg-red-50 rounded-xl border border-red-100 hover:border-red-200 transition-colors">
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                <AlertCircle class="w-4 h-4 text-red-600" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-red-700">高风险文案待处理</p>
                <p class="text-xs text-red-500 mt-1">3条文案存在极限词风险，请尽快审查</p>
                <button class="text-xs text-red-600 hover:text-red-700 font-semibold mt-2">立即处理</button>
              </div>
            </div>
          </div>

          <div class="p-4 bg-amber-50 rounded-xl border border-amber-100 hover:border-amber-200 transition-colors">
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                <Clock class="w-4 h-4 text-amber-600" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-amber-700">欧盟新法规即将生效</p>
                <p class="text-xs text-amber-500 mt-1">GDPR更新条款将于下月生效</p>
                <button class="text-xs text-amber-600 hover:text-amber-700 font-semibold mt-2">了解详情</button>
              </div>
            </div>
          </div>

          <div class="p-4 bg-violet-50 rounded-xl border border-violet-100 hover:border-violet-200 transition-colors">
            <div class="flex items-start gap-3">
              <div class="w-9 h-9 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0">
                <MessageSquare class="w-4 h-4 text-violet-600" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-violet-700">待人工处理消息</p>
                <p class="text-xs text-violet-500 mt-1">5条客户消息需要人工回复</p>
                <button class="text-xs text-violet-600 hover:text-violet-700 font-semibold mt-2">查看消息</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  PlusCircle, PenTool, MessageSquare, ShieldCheck, Package,
  Bell, AlertCircle, Clock, Settings, FileText
} from 'lucide-vue-next'

defineEmits(['navigate'])

const quickActions = [
  { id: 'copywriter', label: '文案生成', desc: '多语种智能生成', icon: PenTool, bgClass: 'bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-600 shadow-violet-900/20' },
  { id: 'compliance', label: '合规审查', desc: '风险检测预警', icon: ShieldCheck, bgClass: 'bg-gradient-to-br from-amber-500 via-orange-500 to-red-500 shadow-amber-900/20' },
  { id: 'customer-service', label: '客服应答', desc: '7x24自动回复', icon: MessageSquare, bgClass: 'bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 shadow-emerald-900/20' },
  { id: 'legal', label: '法规检索', desc: '海外合规查询', icon: FileText, bgClass: 'bg-gradient-to-br from-amber-500 via-yellow-500 to-lime-500 shadow-amber-900/20' },
  { id: 'logistics', label: '物流单据', desc: '一键生成单据', icon: Package, bgClass: 'bg-gradient-to-br from-purple-500 via-pink-500 to-rose-500 shadow-purple-900/20' },
  { id: 'settings', label: '系统设置', desc: 'API配置管理', icon: Settings, bgClass: 'bg-gradient-to-br from-slate-500 via-slate-600 to-slate-700 shadow-slate-900/20' }
]
</script>
