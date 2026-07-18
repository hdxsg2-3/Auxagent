<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">法规检索</h2>
        <p class="text-sm text-slate-500 mt-2">查询海外各国法律法规，确保合规运营</p>
      </div>
    </div>

    <div class="card p-7 mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex-1">
          <label class="block text-sm font-semibold text-slate-700 mb-2.5">搜索关键词</label>
          <div class="relative">
            <Search class="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              v-model="searchQuery"
              @keyup.enter="performSearch"
              class="input-field w-full pl-11 pr-4 py-3 text-sm"
              placeholder="搜索法规关键词，如：GDPR、电池法规、CE认证..."
            />
          </div>
        </div>
        <div class="md:w-64">
          <label class="block text-sm font-semibold text-slate-700 mb-2.5">目标地区</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="region in regions"
              :key="region.value"
              @click="toggleRegion(region.value)"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all"
              :class="[
                selectedRegions.includes(region.value)
                  ? 'border-violet-500 bg-violet-50 text-violet-600'
                  : 'border-slate-200 text-slate-600 hover:border-violet-300'
              ]"
            >
              {{ region.label }}
            </button>
          </div>
        </div>
        <div class="md:w-48 flex items-end">
          <button
            @click="performSearch"
            :disabled="loading"
            class="w-full py-3 rounded-xl flex items-center justify-center gap-2 text-sm font-semibold transition-all"
            :class="[
              loading
                ? 'bg-slate-400 cursor-not-allowed'
                : 'btn-primary'
            ]"
          >
            <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <Search v-else class="w-5 h-5" />
            {{ loading ? '搜索中...' : '搜索' }}
          </button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <div class="col-span-2">
        <div v-if="!results.length && !loading" class="card p-12 text-center">
          <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-5">
            <FileText class="w-10 h-10 text-slate-400" />
          </div>
          <p class="text-slate-500 font-medium">输入关键词开始搜索</p>
          <p class="text-sm text-slate-400 mt-1">支持搜索全球各地区法律法规</p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="(result, index) in results"
            :key="index"
            class="card p-6 cursor-pointer hover:shadow-xl transition-all"
            @click="selectResult(result)"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <span :class="[
                    result.region === 'EU' ? 'bg-blue-50 text-blue-600' : '',
                    result.region === 'US' ? 'bg-red-50 text-red-600' : '',
                    result.region === 'JP' ? 'bg-pink-50 text-pink-600' : '',
                    result.region === 'DE' ? 'bg-yellow-50 text-yellow-600' : '',
                    result.region === 'UK' ? 'bg-blue-50 text-blue-600' : '',
                    result.region === 'CN' ? 'bg-red-50 text-red-600' : ''
                  ]" class="text-xs px-3 py-1 rounded-full font-semibold">
                    {{ getRegionLabel(result.region) }}
                  </span>
                  <span class="text-xs text-slate-400">{{ result.effective_date }}</span>
                </div>
                <h3 class="text-lg font-bold text-slate-900 mb-2">{{ result.title }}</h3>
                <p class="text-sm text-slate-500 line-clamp-2">{{ result.summary }}</p>
              </div>
              <ChevronRight class="w-5 h-5 text-slate-400 flex-shrink-0" />
            </div>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-6">法规详情</h3>

        <div v-if="selectedResult">
          <div class="flex items-center gap-3 mb-4">
            <span :class="[
              selectedResult.region === 'EU' ? 'bg-blue-50 text-blue-600' : '',
              selectedResult.region === 'US' ? 'bg-red-50 text-red-600' : '',
              selectedResult.region === 'JP' ? 'bg-pink-50 text-pink-600' : '',
              selectedResult.region === 'DE' ? 'bg-yellow-50 text-yellow-600' : '',
              selectedResult.region === 'UK' ? 'bg-blue-50 text-blue-600' : '',
              selectedResult.region === 'CN' ? 'bg-red-50 text-red-600' : ''
            ]" class="text-xs px-3 py-1 rounded-full font-semibold">
              {{ getRegionLabel(selectedResult.region) }}
            </span>
            <span class="text-xs text-slate-400">{{ selectedResult.effective_date }}</span>
          </div>
          <h4 class="text-lg font-bold text-slate-900 mb-4">{{ selectedResult.title }}</h4>
          <div class="space-y-4">
            <div>
              <h5 class="text-sm font-semibold text-slate-600 mb-2">法规简介</h5>
              <p class="text-sm text-slate-700 leading-relaxed">{{ selectedResult.description }}</p>
            </div>
            <div>
              <h5 class="text-sm font-semibold text-slate-600 mb-2">适用范围</h5>
              <ul class="space-y-1.5">
                <li v-for="(item, idx) in selectedResult.scope" :key="idx" class="text-sm text-slate-700 flex items-center gap-2">
                  <CheckCircle class="w-4 h-4 text-green-500 flex-shrink-0" />
                  {{ item }}
                </li>
              </ul>
            </div>
            <div>
              <h5 class="text-sm font-semibold text-slate-600 mb-2">合规要求</h5>
              <ul class="space-y-1.5">
                <li v-for="(req, idx) in selectedResult.requirements" :key="idx" class="text-sm text-slate-700 flex items-center gap-2">
                  <AlertCircle class="w-4 h-4 text-amber-500 flex-shrink-0" />
                  {{ req }}
                </li>
              </ul>
            </div>
          </div>
          <button class="w-full mt-6 btn-outline py-3 rounded-xl font-semibold">
            查看完整法规
          </button>
        </div>

        <div v-else class="text-center py-12">
          <div class="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
            <FileText class="w-8 h-8 text-slate-400" />
          </div>
          <p class="text-slate-500 font-medium">选择一条法规查看详情</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, FileText, ChevronRight, CheckCircle, AlertCircle } from 'lucide-vue-next'
import { legalAPI } from '../api/client'
import { ElMessage } from 'element-plus'

const searchQuery = ref('')
const selectedRegions = ref(['EU', 'US'])
const loading = ref(false)
const results = ref([])
const selectedResult = ref(null)

const regions = [
  { value: 'EU', label: '欧盟' },
  { value: 'US', label: '美国' },
  { value: 'JP', label: '日本' },
  { value: 'DE', label: '德国' },
  { value: 'UK', label: '英国' },
  { value: 'CN', label: '中国' }
]

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

function toggleRegion(region) {
  const index = selectedRegions.value.indexOf(region)
  if (index > -1) {
    selectedRegions.value.splice(index, 1)
  } else {
    selectedRegions.value.push(region)
  }
}

async function performSearch() {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  results.value = []
  selectedResult.value = null

  try {
    const response = await legalAPI.search({
      query: searchQuery.value,
      regions: selectedRegions.value
    })

    if (response.data.success) {
      results.value = response.data.data
    } else {
      ElMessage.error('搜索失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('搜索过程中发生错误')
  } finally {
    loading.value = false
  }
}

function selectResult(result) {
  selectedResult.value = result
}
</script>
