<template>
  <div class="flex min-h-screen">
    <aside
      id="sidebar"
      class="sidebar fixed left-0 top-0 z-50 w-52 h-screen flex flex-col transition-all duration-300 overflow-y-auto"
      :class="[
        sidebarVisible ? 'translate-x-0' : '-translate-x-full',
        'md:translate-x-0'
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

    <div class="flex-1 flex flex-col md:ml-52">
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
        <KeepAlive max="12">
          <component :is="currentComponent" @pending-count-changed="pendingCount = $event" class="page-transition" />
        </KeepAlive>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import {
  Globe, LayoutDashboard, PenTool, ShieldCheck, MessageSquare,
  FileText, Package, Settings, Bell, Menu, Store, Zap, ShoppingCart, Clock, Eye, Image
} from 'lucide-vue-next'

import Dashboard from './components/Dashboard.vue'
import Copywriter from './components/Copywriter.vue'
import Compliance from './components/Compliance.vue'
import CustomerService from './components/CustomerService.vue'
import Legal from './components/Legal.vue'
import Logistics from './components/Logistics.vue'
import ListingManager from './components/ListingManager.vue'
import SettingsPage from './components/Settings.vue'
import PlatformShops from './components/PlatformShops.vue'
import UniversalIntegration from './components/UniversalIntegration.vue'
import LegalDetail from './components/LegalDetail.vue'
import SchedulerPanel from './components/SchedulerPanel.vue'
import ImageTools from './components/ImageTools.vue'
import CompetitorAnalysis from './components/CompetitorAnalysis.vue'
import UserMemory from './components/UserMemory.vue'

const currentPage = ref('home')
const sidebarVisible = ref(false)
const legalDetailData = ref(null)
const pendingCount = ref(0)

const navItems = computed(() => [
  { id: 'home', label: '工作台', icon: LayoutDashboard },
  { id: 'universal-integration', label: '自动对接', icon: Zap },
  { id: 'copywriter', label: '文案生成', icon: PenTool },
  { id: 'compliance', label: '合规审查', icon: ShieldCheck },
  { id: 'customer-service', label: '客服应答', icon: MessageSquare, badge: pendingCount.value > 0 ? String(pendingCount.value) : null },
  { id: 'platform-shops', label: '店铺管理', icon: Store },
  { id: 'legal', label: '法规检索', icon: FileText },
  { id: 'logistics', label: '物流单据', icon: Package },
  { id: 'listing-manager', label: '商品管理', icon: ShoppingCart },
  { id: 'competitor', label: '竞品分析', icon: Eye },
  { id: 'image-tools', label: '图片处理', icon: Image },
  { id: 'scheduler', label: '自动巡检', icon: Clock },
])

const pageComponents = {
  home: Dashboard,
  'universal-integration': UniversalIntegration,
  copywriter: Copywriter,
  compliance: Compliance,
  'customer-service': CustomerService,
  'platform-shops': PlatformShops,
  legal: Legal,
  'legal-detail': LegalDetail,
  logistics: Logistics,
  'listing-manager': ListingManager,
  competitor: CompetitorAnalysis,
  'image-tools': ImageTools,
  scheduler: SchedulerPanel,
  memory: UserMemory,
  settings: SettingsPage
}

const currentComponent = computed(() => pageComponents[currentPage.value] || Dashboard)

function navigateTo(pageId) {
  currentPage.value = pageId
  sidebarVisible.value = false
}

function navigateToLegalDetail(data) {
  legalDetailData.value = data
  currentPage.value = 'legal-detail'
}

provide('legalDetailData', legalDetailData)
provide('navigateTo', navigateTo)
provide('navigateToLegalDetail', navigateToLegalDetail)
</script>
