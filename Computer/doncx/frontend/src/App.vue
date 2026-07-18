<template>
  <div class="flex min-h-screen">
    <aside
      id="sidebar"
      class="sidebar fixed left-0 top-0 z-50 w-60 h-screen flex flex-col transition-all duration-300"
      :class="[
        sidebarVisible ? 'translate-x-0' : '-translate-x-full',
        'md:translate-x-0 md:static md:h-auto md:min-h-screen'
      ]"
    >
      <div class="h-full">
        <div class="p-6 border-b border-white/5">
          <div class="sidebar-logo flex items-center gap-3 relative">
            <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-600 flex items-center justify-center relative z-10 shadow-lg shadow-violet-900/30">
              <Globe class="w-5 h-5 text-white" />
            </div>
            <div class="relative z-10">
              <h1 class="text-lg font-bold text-white tracking-tight">GlobalSeller AI</h1>
              <p class="text-xs text-white/50">跨境电商智能平台</p>
            </div>
          </div>
        </div>

        <nav class="flex-1 p-4 space-y-2">
          <button
            v-for="item in navItems"
            :key="item.id"
            @click="navigateTo(item.id)"
            class="sidebar-nav-item w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left"
            :class="[
              currentPage === item.id
                ? 'active'
                : 'text-white/70'
            ]"
          >
            <component :is="item.icon" class="w-5 h-5" />
            <span class="font-medium">{{ item.label }}</span>
            <span
              v-if="item.badge"
              class="ml-auto bg-gradient-to-r from-red-500 to-pink-500 text-white text-xs px-2.5 py-0.5 rounded-full shadow-lg shadow-red-900/30"
            >
              {{ item.badge }}
            </span>
          </button>
        </nav>

        <div class="p-4 border-t border-white/5">
          <button
            @click="navigateTo('settings')"
            class="sidebar-nav-item w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left"
            :class="[
              currentPage === 'settings'
                ? 'active'
                : 'text-white/70'
            ]"
          >
            <Settings class="w-5 h-5" />
            <span class="font-medium">系统设置</span>
          </button>
        </div>
      </div>
    </aside>

    <div class="flex-1 flex flex-col" :class="{'md:ml-60': true}">
      <header class="h-16 header-glass flex items-center justify-between px-6 sticky top-0 z-40">
        <div class="flex items-center gap-4 flex-1 max-w-xl">
          <div class="relative flex-1">
            <Search class="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              class="input-field w-full pl-11 pr-4 py-2.5 text-sm"
              placeholder="搜索功能、商品、订单..."
            />
          </div>
          <button class="p-2.5 rounded-xl bg-white/10 hover:bg-white/20 transition-all relative">
            <Bell class="w-5 h-5 text-slate-600" />
            <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
        </div>

        <div class="flex items-center gap-4">
          <div class="hidden md:flex items-center gap-2.5 px-3.5 py-1.5 bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-xl border border-violet-500/20">
            <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            <span class="text-xs font-semibold text-violet-600">VIP会员</span>
          </div>
          <div class="flex items-center gap-3 cursor-pointer group">
            <div class="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 via-purple-500 to-indigo-500 flex items-center justify-center text-white font-semibold shadow-lg shadow-violet-900/30 group-hover:ring-2 ring-white/20 transition-all">
              S
            </div>
            <div class="hidden md:block">
              <p class="text-sm font-semibold text-slate-800">深圳卖家</p>
              <p class="text-xs text-slate-400">店铺ID: SHZ2024001</p>
            </div>
          </div>
          <button
            @click="sidebarVisible = !sidebarVisible"
            class="md:hidden p-2.5 rounded-xl bg-white/10 hover:bg-white/20 transition-all"
          >
            <Menu class="w-5 h-5 text-slate-600" />
          </button>
        </div>
      </header>

      <main class="flex-1 p-6 md:p-8 space-y-6 relative z-10">
        <component :is="currentComponent" class="page-transition" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Globe, LayoutDashboard, PenTool, ShieldCheck, MessageSquare,
  FileText, Package, Settings, Search, Bell, Menu
} from 'lucide-vue-next'

import Dashboard from './components/Dashboard.vue'
import Copywriter from './components/Copywriter.vue'
import Compliance from './components/Compliance.vue'
import CustomerService from './components/CustomerService.vue'
import Legal from './components/Legal.vue'
import Logistics from './components/Logistics.vue'
import SettingsPage from './components/Settings.vue'

const currentPage = ref('home')
const sidebarVisible = ref(false)

const navItems = [
  { id: 'home', label: '工作台', icon: LayoutDashboard },
  { id: 'copywriter', label: '文案生成', icon: PenTool },
  { id: 'compliance', label: '合规审查', icon: ShieldCheck },
  { id: 'customer-service', label: '客服应答', icon: MessageSquare, badge: '5' },
  { id: 'legal', label: '法规检索', icon: FileText },
  { id: 'logistics', label: '物流单据', icon: Package }
]

const pageComponents = {
  home: Dashboard,
  copywriter: Copywriter,
  compliance: Compliance,
  'customer-service': CustomerService,
  legal: Legal,
  logistics: Logistics,
  settings: SettingsPage
}

const currentComponent = computed(() => pageComponents[currentPage.value] || Dashboard)

function navigateTo(pageId) {
  currentPage.value = pageId
  sidebarVisible.value = false
}
</script>
