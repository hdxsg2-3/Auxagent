<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <!-- 标题区 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900">通用店铺自动对接</h2>
        <p class="text-sm text-slate-500 mt-1">免费即时开通 · 全自动上架 · 消息收发 · 浏览器自动化（备用） · 无需等待审核</p>
      </div>
      <div class="flex gap-3">
        <button @click="loadStatus" class="btn-secondary px-4 py-2.5 rounded-xl flex items-center gap-2">
          <RefreshCw class="w-4 h-4" /> 刷新状态
        </button>
      </div>
    </div>

    <!-- 平台概览卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- LocalShop -->
      <div class="card p-5 border-2 border-emerald-400 bg-emerald-50/50 relative">
        <div class="absolute top-3 right-3">
          <span class="text-xs bg-emerald-500 text-white px-2 py-0.5 rounded-full">推荐</span>
        </div>
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center">
            <Store class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="font-bold text-slate-800">LocalShop</h3>
            <p class="text-xs text-emerald-600">免费 · 即时开通</p>
          </div>
        </div>
        <p class="text-xs text-slate-500 mb-3">内建免费电商平台，零配置即时可用，真实数据持久化</p>
        <div class="flex items-center gap-2 text-xs">
          <span class="text-emerald-600 font-semibold">{{ platformStats['local-shop']?.active || 0 }}</span>
          <span class="text-slate-400">个活跃店铺</span>
        </div>
      </div>

      <!-- eBay -->
      <div class="card p-5">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center">
            <ShoppingBag class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="font-bold text-slate-800">eBay Sandbox</h3>
            <p class="text-xs text-blue-600">免费 · 真实上架</p>
          </div>
        </div>
        <p class="text-xs text-slate-500 mb-3">免费 Sandbox 环境真实上架，返回真实 Item ID，0 月租</p>
        <div class="flex items-center gap-2 text-xs">
          <span class="text-blue-600 font-semibold">{{ platformStats['ebay']?.active || 0 }}</span>
          <span class="text-slate-400">个活跃店铺</span>
        </div>
      </div>

      <!-- Amazon -->
      <div class="card p-5">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-orange-500 flex items-center justify-center">
            <Package class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="font-bold text-slate-800">Amazon SP-API</h3>
            <p class="text-xs text-orange-600">$39.99/月 · 需审核</p>
          </div>
        </div>
        <p class="text-xs text-slate-500 mb-3">需开发者注册审核，支持完整 SP-API（Mock 模式可演示）</p>
        <div class="flex items-center gap-2 text-xs">
          <span class="text-orange-600 font-semibold">{{ platformStats['amazon']?.active || 0 }}</span>
          <span class="text-slate-400">个活跃店铺</span>
        </div>
      </div>

      <!-- 浏览器自动化 -->
      <div class="card p-5" :class="{ 'border-2 border-violet-300': browserStatus.playwright_available }">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-violet-500 flex items-center justify-center">
            <Monitor class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="font-bold text-slate-800">浏览器自动化</h3>
            <p class="text-xs" :class="browserStatus.playwright_available ? 'text-violet-600' : 'text-slate-400'">
              {{ browserStatus.playwright_available ? 'Playwright 已安装' : '模拟模式' }}
            </p>
          </div>
        </div>
        <p class="text-xs text-slate-500 mb-3">{{ browserStatus.message }}</p>
        <div class="flex items-center gap-2 text-xs">
          <span class="text-violet-600 font-semibold">{{ browserStatus.supported_platforms?.length || 3 }}</span>
          <span class="text-slate-400">个平台支持</span>
        </div>
      </div>
    </div>

    <!-- 全自动演示区 -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Zap class="w-5 h-5 text-amber-500" /> 一键全自动演示
          </h3>
          <p class="text-sm text-slate-500 mt-1">
            点击按钮后，系统会自动完成：创建店铺 → 写商品文案 → 上架商品 → 拉取买家消息 → AI 读取消息并生成回复 → 自动发送回复
          </p>
        </div>
      </div>

      <!-- 演示选项 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <label class="text-sm font-medium text-slate-600 mb-1 block">目标平台</label>
          <el-select v-model="demoConfig.platform" style="width: 100%">
            <el-option label="LocalShop（推荐 · 免费即时）" value="local-shop" />
            <el-option label="Amazon（Mock 模式）" value="amazon" />
            <el-option label="eBay（Mock 模式）" value="ebay" />
            <el-option label="Temu（Mock 模式）" value="temu" />
          </el-select>
        </div>
        <div>
          <label class="text-sm font-medium text-slate-600 mb-1 block">上架方式</label>
          <el-select v-model="demoConfig.method" style="width: 100%">
            <el-option label="平台适配器（推荐）" value="adapter" />
            <el-option label="浏览器自动化兜底" value="browser" />
          </el-select>
        </div>
        <div>
          <label class="text-sm font-medium text-slate-600 mb-1 block">商品信息</label>
          <el-select v-model="demoConfig.productSource" style="width: 100%">
            <el-option label="AI 自动生成" value="ai" />
            <el-option label="使用默认商品" value="default" />
          </el-select>
        </div>
      </div>

      <!-- 执行按钮 -->
      <div class="flex gap-3">
        <button
          @click="runAutoDemo"
          :disabled="demoRunning"
          class="btn-primary px-6 py-3 rounded-xl flex items-center gap-2 disabled:opacity-50"
        >
          <Loader2 v-if="demoRunning" class="w-5 h-5 animate-spin" />
          <Play v-else class="w-5 h-5" />
          {{ demoRunning ? '演示进行中...' : '开始全自动演示' }}
        </button>
        <button
          v-if="!hasLocalShop"
          @click="createDemoShop"
          :disabled="creatingShop"
          class="btn-secondary px-6 py-3 rounded-xl flex items-center gap-2"
        >
          <Store class="w-5 h-5" />
          {{ creatingShop ? '创建中...' : '一键创建 LocalShop 店铺' }}
        </button>
      </div>

      <!-- 演示步骤进度 -->
      <div v-if="demoReport" class="mt-6">
        <!-- 顶部总结卡片 -->
        <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-4">
          <div class="flex items-center gap-2 mb-2">
            <CheckCircle2 v-if="demoReport.success" class="w-5 h-5 text-emerald-500" />
            <AlertCircle v-else class="w-5 h-5 text-amber-500" />
            <h4 class="font-bold text-slate-800">演示报告</h4>
            <span class="text-xs text-slate-400 ml-auto">{{ demoReport.started_at }} → {{ demoReport.completed_at }}</span>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div class="text-center">
              <p class="text-2xl font-bold text-emerald-600">{{ demoReport.summary?.successful_steps || 0 }}</p>
              <p class="text-xs text-slate-500">步骤成功</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-blue-600">{{ demoReport.summary?.messages_received || 0 }}</p>
              <p class="text-xs text-slate-500">买家消息</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-violet-600">{{ demoReport.summary?.replies_sent || 0 }}</p>
              <p class="text-xs text-slate-500">AI 已回复</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-emerald-600">{{ demoReport.summary?.listing_created ? '是' : '否' }}</p>
              <p class="text-xs text-slate-500">商品已上架</p>
            </div>
          </div>
        </div>

        <!-- 步骤时间线 -->
        <div class="space-y-2 mb-4">
          <div
            v-for="step in demoReport.steps"
            :key="step.step"
            class="flex items-start gap-3 p-3 rounded-lg"
            :class="{
              'bg-emerald-50': step.status === 'success',
              'bg-red-50': step.status === 'error',
              'bg-amber-50': step.status === 'fallback',
              'bg-slate-50': step.status === 'skipped',
            }"
          >
            <div class="flex-shrink-0 mt-0.5">
              <CheckCircle2 v-if="step.status === 'success'" class="w-4 h-4 text-emerald-500" />
              <XCircle v-else-if="step.status === 'error'" class="w-4 h-4 text-red-500" />
              <AlertCircle v-else-if="step.status === 'fallback'" class="w-4 h-4 text-amber-500" />
              <Minus v-else class="w-4 h-4 text-slate-400" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-700">{{ step.name }}</p>
              <p class="text-xs text-slate-500 mt-0.5">{{ step.detail }}</p>
            </div>
            <span class="text-xs text-slate-400 flex-shrink-0">{{ step.timestamp.split(' ')[1] }}</span>
          </div>
        </div>

        <!-- 上架结果 -->
        <div v-if="demoReport.listing" class="bg-slate-50 rounded-xl p-4 mb-3">
          <h5 class="text-sm font-bold text-slate-700 mb-2">上架结果</h5>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <span class="text-slate-400 text-xs">平台</span>
              <p class="font-medium text-slate-700">{{ demoReport.listing.platform || demoReport.shop?.platform }}</p>
            </div>
            <div>
              <span class="text-slate-400 text-xs">商品 ID</span>
              <p class="font-medium text-slate-700">{{ demoReport.listing.product_id || demoReport.listing.listing_id || 'N/A' }}</p>
            </div>
            <div>
              <span class="text-slate-400 text-xs">方式</span>
              <p class="font-medium text-slate-700">{{ demoReport.listing.mock ? 'Mock 模拟' : (demoReport.listing.mode || '真实 API') }}</p>
            </div>
            <div>
              <span class="text-slate-400 text-xs">状态</span>
              <p class="font-medium" :class="demoReport.listing.success ? 'text-emerald-600' : 'text-red-600'">
                {{ demoReport.listing.success ? '成功' : '失败' }}
              </p>
            </div>
          </div>
        </div>

        <!-- 拉取的买家消息 -->
        <div v-if="demoReport.messages && demoReport.messages.length > 0" class="bg-slate-50 rounded-xl p-4 mb-3">
          <h5 class="text-sm font-bold text-slate-700 mb-3">
            拉取的买家消息 ({{ demoReport.messages.length }} 条)
          </h5>
          <div class="space-y-3">
            <div
              v-for="(msg, idx) in demoReport.messages"
              :key="idx"
              class="p-3 bg-white rounded-lg border border-slate-100"
            >
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full font-medium">
                  {{ msg.buyer_name || msg.buyer_id || '未知买家' }}
                </span>
                <span class="text-xs text-slate-400">{{ msg.created_at }}</span>
              </div>
              <p class="text-sm text-slate-700">{{ msg.body || msg.content || msg.subject }}</p>
              <p v-if="msg.order_id" class="text-xs text-slate-400 mt-1">关联订单: {{ msg.order_id }}</p>
            </div>
          </div>
        </div>

        <!-- AI 自动回复（对话形式） -->
        <div v-if="demoReport.replies && demoReport.replies.length > 0" class="bg-slate-50 rounded-xl p-4">
          <h5 class="text-sm font-bold text-slate-700 mb-3">AI 自动回复对话记录</h5>
          <div class="space-y-4">
            <div
              v-for="(reply, idx) in demoReport.replies"
              :key="idx"
              class="border border-slate-100 rounded-lg overflow-hidden"
            >
              <!-- 买家问 -->
              <div class="bg-orange-50 p-3">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-xs bg-orange-200 text-orange-700 px-2 py-0.5 rounded-full font-bold">
                    {{ reply.buyer || '买家' }} 问
                  </span>
                </div>
                <p class="text-sm text-slate-700">{{ reply.original_message }}</p>
              </div>
              <!-- AI 答 -->
              <div class="bg-emerald-50 p-3">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-xs bg-emerald-200 text-emerald-700 px-2 py-0.5 rounded-full font-bold">
                    AI 客服 答
                  </span>
                  <span class="text-xs text-slate-400">
                    {{ reply.send_result?.success ? '已发送' : '发送失败' }}
                  </span>
                </div>
                <p class="text-sm text-slate-700">{{ reply.ai_reply }}</p>
                <div v-if="reply.reply_zh" class="mt-2 bg-blue-50 rounded p-2">
                  <p class="text-xs text-blue-700 font-medium">中文翻译（供商家核对）</p>
                  <p class="text-xs text-slate-600 mt-0.5">{{ reply.reply_zh }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 浏览器自动化兜底面板 -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Monitor class="w-5 h-5 text-violet-500" /> 浏览器自动化备用方案
          </h3>
          <p class="text-sm text-slate-500 mt-1">当 API 不可用时（无凭证 / 审核中 / 付费门槛），通过浏览器自动化完成操作</p>
        </div>
        <el-select v-model="browserPlatform" style="width: 160px" @change="loadBrowserStatus">
          <el-option label="Amazon" value="amazon" />
          <el-option label="eBay" value="ebay" />
          <el-option label="Temu" value="temu" />
        </el-select>
      </div>

      <!-- 浏览器自动化状态 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div class="bg-slate-50 rounded-xl p-4">
          <h4 class="text-sm font-bold text-slate-700 mb-2">运行状态</h4>
          <div class="space-y-2 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-500">Playwright</span>
              <span :class="browserDetail?.playwright_available ? 'text-emerald-600' : 'text-amber-600'" class="font-medium">
                {{ browserDetail?.playwright_available ? '已安装' : '未安装（模拟模式）' }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-500">目标平台</span>
              <span class="font-medium text-slate-700">{{ browserDetail?.platform_name || browserPlatform }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-500">运行模式</span>
              <span class="font-medium text-slate-700">{{ browserDetail?.mode === 'real_browser' ? '真实浏览器' : '模拟浏览器' }}</span>
            </div>
          </div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <h4 class="text-sm font-bold text-slate-700 mb-2">支持的操作</h4>
          <div class="space-y-2">
            <button
              v-for="action in browserActions"
              :key="action.key"
              @click="executeBrowserFallback(action.key)"
              :disabled="browserExecuting"
              class="w-full text-left px-3 py-2 rounded-lg bg-white hover:bg-violet-50 transition-all flex items-center justify-between disabled:opacity-50"
            >
              <span class="text-sm text-slate-700">{{ action.label }}</span>
              <Loader2 v-if="browserExecuting === action.key" class="w-4 h-4 animate-spin text-violet-500" />
              <ChevronRight v-else class="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>
      </div>

      <!-- 操作步骤预览 -->
      <div v-if="browserDetail?.steps_preview" class="bg-slate-50 rounded-xl p-4">
        <h4 class="text-sm font-bold text-slate-700 mb-3">操作步骤预览</h4>
        <el-tabs v-model="activeStepTab">
          <el-tab-pane label="上架 Listing" name="create_listing">
            <div class="space-y-1">
              <div v-for="(step, idx) in browserDetail.steps_preview.create_listing" :key="idx" class="flex items-center gap-2 text-sm text-slate-600 py-1">
                <span class="w-6 h-6 rounded-full bg-violet-100 text-violet-600 text-xs flex items-center justify-center flex-shrink-0">{{ idx + 1 }}</span>
                <span>{{ step }}</span>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="拉取消息" name="get_messages">
            <div class="space-y-1">
              <div v-for="(step, idx) in browserDetail.steps_preview.get_messages" :key="idx" class="flex items-center gap-2 text-sm text-slate-600 py-1">
                <span class="w-6 h-6 rounded-full bg-violet-100 text-violet-600 text-xs flex items-center justify-center flex-shrink-0">{{ idx + 1 }}</span>
                <span>{{ step }}</span>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="发送消息" name="send_message">
            <div class="space-y-1">
              <div v-for="(step, idx) in browserDetail.steps_preview.send_message" :key="idx" class="flex items-center gap-2 text-sm text-slate-600 py-1">
                <span class="w-6 h-6 rounded-full bg-violet-100 text-violet-600 text-xs flex items-center justify-center flex-shrink-0">{{ idx + 1 }}</span>
                <span>{{ step }}</span>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 浏览器自动化执行结果 -->
      <div v-if="browserResult" class="mt-4 bg-violet-50 rounded-xl p-4">
        <h4 class="text-sm font-bold text-slate-700 mb-2">执行结果</h4>
        <div class="space-y-2">
          <div class="flex items-center gap-2 text-sm">
            <CheckCircle2 v-if="browserResult.success" class="w-4 h-4 text-emerald-500" />
            <XCircle v-else class="w-4 h-4 text-red-500" />
            <span class="font-medium text-slate-700">{{ browserResult.message }}</span>
          </div>
          <div v-if="browserResult.execution_log" class="text-xs text-slate-500">
            模式: {{ browserResult.execution_log.mode }} | 步骤: {{ browserResult.execution_log.total_steps }}
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Store, ShoppingBag, Package, Monitor, Zap, Play, Loader2,
  RefreshCw, CheckCircle2, AlertCircle, XCircle, Minus, ChevronRight
} from 'lucide-vue-next'
import { demoStore } from '../store/demoStore.js'

// ========== 全局状态（切换页面不丢失） ==========
const demoRunning = computed(() => demoStore.state.demoRunning)
const demoReport = computed(() => demoStore.state.demoReport)
const demoError = computed(() => demoStore.state.demoError)
const demoConfig = demoStore.config

const browserPlatform = computed({
  get: () => demoStore.state.browserPlatform,
  set: (val) => { demoStore.setBrowserPlatform(val); loadBrowserStatus() }
})
const browserDetail = computed(() => demoStore.state.browserDetail)
const browserExecuting = computed(() => demoStore.state.browserExecuting)
const browserResult = computed(() => demoStore.state.browserResult)
const activeStepTab = ref('create_listing')

const loading = computed(() => demoStore.state.loading)
const statusData = computed(() => demoStore.state.statusData)
const shops = computed(() => demoStore.state.shops)

const creatingShop = ref(false)

const platformStats = computed(() => statusData.value?.platform_stats || {})
const browserStatus = computed(() => statusData.value?.browser_automation || {})
const supportedPlatforms = computed(() => statusData.value?.supported_platforms || [])
const hasLocalShop = computed(() => shops.value.some(s => s.platform === 'local-shop'))

const browserActions = [
  { key: 'create_listing', label: '上架商品（浏览器自动化）' },
  { key: 'get_messages', label: '拉取消息（浏览器自动化）' },
  { key: 'send_message', label: '发送消息（浏览器自动化）' },
]

// ========== 方法 ==========
async function loadStatus() {
  try {
    await demoStore.loadStatus()
  } catch (e) {
    ElMessage.error('加载状态失败: ' + (e.response?.data?.message || e.message))
  }
}

async function loadBrowserStatus() {
  try {
    await demoStore.loadBrowserStatus()
  } catch (e) {
    ElMessage.error('加载浏览器自动化状态失败')
  }
}

async function createDemoShop() {
  creatingShop.value = true
  try {
    const data = await demoStore.createDemoShop()
    ElMessage.success(data.message || 'LocalShop 店铺创建成功')
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.response?.data?.message || e.message))
  } finally {
    creatingShop.value = false
  }
}

async function runAutoDemo() {
  if (demoRunning.value) return
  const result = await demoStore.runAutoDemo()
  if (result.success) {
    ElMessage.success('全自动演示完成！')
  } else {
    ElMessage.error('演示失败: ' + result.error)
  }
}

async function executeBrowserFallback(action) {
  const payload = action === 'create_listing' ? {
    sku: `BF-${Date.now()}`,
    title: 'Browser Automation Demo Product',
    bullet_points: ['Demo bullet point 1', 'Demo bullet point 2'],
    description: 'This product was listed via browser automation fallback.',
    price: 19.99,
    stock: 50,
  } : action === 'send_message' ? {
    order_id: `ORD-${Date.now()}`,
    buyer_id: 'demo_buyer',
    text: 'Thank you for your inquiry. We will process your request shortly.',
  } : {}
  const result = await demoStore.executeBrowserFallback(action, payload)
  if (result.success) {
    ElMessage.success(result.data?.message || '操作完成')
  } else {
    ElMessage.error('操作失败: ' + result.error)
  }
}

// 监听演示错误
watch(demoError, (err) => {
  if (err) ElMessage.error(err)
})

onMounted(() => {
  loadStatus()
  loadBrowserStatus()
})
</script>
