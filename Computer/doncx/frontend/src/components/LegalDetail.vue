<template>
  <div>
    <!-- 返回按钮 + 标题 -->
    <div class="flex items-center gap-4 mb-8">
      <button
        @click="goBack"
        class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-violet-300 hover:text-violet-600 transition-all text-sm font-semibold"
      >
        <ArrowLeft class="w-4 h-4" />
        返回检索列表
      </button>
      <div>
        <h2 class="text-2xl font-bold text-slate-900">法规详情</h2>
      </div>
    </div>

    <!-- 无数据提示 -->
    <div v-if="!regulation" class="card p-12 text-center">
      <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-5">
        <FileText class="w-10 h-10 text-slate-400" />
      </div>
      <p class="text-slate-500 font-medium">未找到法规数据</p>
      <p class="text-sm text-slate-400 mt-1 mb-6">请从法规检索页面选择一条法规查看</p>
      <button
        @click="goBack"
        class="btn-primary px-6 py-2.5 rounded-xl text-sm font-semibold inline-flex items-center gap-2"
      >
        <ArrowLeft class="w-4 h-4" />
        返回检索
      </button>
    </div>

    <!-- 详情内容 -->
    <div v-else class="grid grid-cols-3 gap-6">
      <!-- 左侧：主要内容 -->
      <div class="col-span-2 space-y-6">
        <!-- 头部卡片 -->
        <div class="card p-8">
          <div class="flex items-center gap-3 mb-4">
            <span :class="[
              regulation.region === 'EU' ? 'bg-blue-50 text-blue-600' : '',
              regulation.region === 'US' ? 'bg-red-50 text-red-600' : '',
              regulation.region === 'JP' ? 'bg-pink-50 text-pink-600' : '',
              regulation.region === 'DE' ? 'bg-yellow-50 text-yellow-600' : '',
              regulation.region === 'UK' ? 'bg-blue-50 text-blue-600' : '',
              regulation.region === 'CN' ? 'bg-red-50 text-red-600' : ''
            ]" class="text-xs px-3 py-1 rounded-full font-semibold">
              {{ getRegionLabel(regulation.region) }}
            </span>
            <span class="text-xs text-slate-400">生效日期：{{ regulation.effective_date }}</span>
          </div>
          <h3 class="text-2xl font-bold text-slate-900 mb-4">{{ regulation.title }}</h3>
          <p class="text-sm text-slate-600 leading-relaxed">{{ regulation.description }}</p>
        </div>

        <!-- 适用产品范围 -->
        <div class="card p-8">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-9 h-9 rounded-lg bg-green-50 flex items-center justify-center">
              <Package class="w-5 h-5 text-green-600" />
            </div>
            <h4 class="text-lg font-bold text-slate-900">适用产品范围</h4>
          </div>
          <ul class="space-y-3">
            <li v-for="(item, idx) in regulation.scope" :key="idx" class="flex items-start gap-3 p-4 bg-slate-50 rounded-xl">
              <CheckCircle class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-slate-700 leading-relaxed">{{ item }}</span>
            </li>
          </ul>
        </div>

        <!-- 合规要求 -->
        <div class="card p-8">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center">
              <AlertCircle class="w-5 h-5 text-amber-600" />
            </div>
            <h4 class="text-lg font-bold text-slate-900">合规要求</h4>
          </div>
          <ul class="space-y-3">
            <li v-for="(req, idx) in regulation.requirements" :key="idx" class="flex items-start gap-3 p-4 bg-slate-50 rounded-xl">
              <ShieldCheck class="w-5 h-5 text-violet-500 flex-shrink-0 mt-0.5" />
              <span class="text-sm text-slate-700 leading-relaxed">{{ req }}</span>
            </li>
          </ul>
        </div>

        <!-- 摘要 -->
        <div v-if="regulation.summary" class="card p-8">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-9 h-9 rounded-lg bg-violet-50 flex items-center justify-center">
              <FileText class="w-5 h-5 text-violet-600" />
            </div>
            <h4 class="text-lg font-bold text-slate-900">法规摘要</h4>
          </div>
          <p class="text-sm text-slate-700 leading-relaxed">{{ regulation.summary }}</p>
        </div>
      </div>

      <!-- 右侧：快速信息 -->
      <div class="space-y-6">
        <!-- 基本信息 -->
        <div class="card p-6">
          <h4 class="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">基本信息</h4>
          <div class="space-y-4">
            <div>
              <p class="text-xs text-slate-400 mb-1">适用地区</p>
              <span :class="[
                regulation.region === 'EU' ? 'bg-blue-50 text-blue-600' : '',
                regulation.region === 'US' ? 'bg-red-50 text-red-600' : '',
                regulation.region === 'JP' ? 'bg-pink-50 text-pink-600' : '',
                regulation.region === 'DE' ? 'bg-yellow-50 text-yellow-600' : '',
                regulation.region === 'UK' ? 'bg-blue-50 text-blue-600' : '',
                regulation.region === 'CN' ? 'bg-red-50 text-red-600' : ''
              ]" class="inline-block text-sm px-3 py-1.5 rounded-lg font-semibold">
                {{ getRegionLabel(regulation.region) }}
              </span>
            </div>
            <div>
              <p class="text-xs text-slate-400 mb-1">生效日期</p>
              <p class="text-sm font-semibold text-slate-800">{{ regulation.effective_date }}</p>
            </div>
            <div v-if="regulation.penalty">
              <p class="text-xs text-slate-400 mb-1">违规处罚</p>
              <p class="text-sm font-semibold text-red-600">{{ regulation.penalty }}</p>
            </div>
          </div>
        </div>

        <!-- 相关法规 -->
        <div v-if="regulation.related_laws && regulation.related_laws.length" class="card p-6">
          <h4 class="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">相关法规</h4>
          <ul class="space-y-2">
            <li v-for="(law, idx) in regulation.related_laws" :key="idx" class="text-sm text-slate-600 hover:text-violet-600 cursor-pointer transition-colors">
              {{ law }}
            </li>
          </ul>
        </div>

        <!-- 回到顶部 -->
        <button
          @click="goBack"
          class="w-full btn-outline py-3 rounded-xl font-semibold text-sm"
        >
          返回检索列表
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { ArrowLeft, FileText, CheckCircle, AlertCircle, ShieldCheck, Package } from 'lucide-vue-next'

const regulation = inject('legalDetailData', null)
const navigateTo = inject('navigateTo', null)

const regionLabels = {
  EU: '欧盟',
  US: '美国',
  JP: '日本',
  DE: '德国',
  UK: '英国',
  CN: '中国'
}

function getRegionLabel(region) {
  return regionLabels[region] || region
}

function goBack() {
  if (navigateTo) {
    navigateTo('legal')
  }
}
</script>
