<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">系统设置</h2>
        <p class="text-sm text-slate-500 mt-2">配置API密钥和系统参数</p>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <div class="col-span-2">
        <div class="card p-7 mb-6">
          <h3 class="text-lg font-bold text-slate-900 mb-6 flex items-center gap-3">
            <Key class="w-5 h-5 text-violet-600" />
            API配置
          </h3>

          <div class="space-y-6">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-2.5">API密钥</label>
              <input
                v-model="settings.api_key"
                type="password"
                class="input-field w-full px-4 py-3 text-sm"
                placeholder="请输入您的API密钥"
              />
              <p class="text-xs text-slate-400 mt-2">请在平台获取您的API密钥，确保密钥安全</p>
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-2.5">API接口地址</label>
              <input
                v-model="settings.api_endpoint"
                class="input-field w-full px-4 py-3 text-sm"
                placeholder="例如：https://api.example.com/v1"
              />
              <p class="text-xs text-slate-400 mt-2">支持兼容OpenAI格式的API接口</p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2.5">模型 / 接入点 ID</label>
                <input
                  v-model="settings.model"
                  type="text"
                  placeholder="ep-xxxxxxxx（方舟接入点）或模型 ID"
                  class="input-field w-full px-4 py-3 text-sm"
                />
                <p class="text-xs text-slate-400 mt-2">保存后立即生效，无需重启；推理型模型（如 DeepSeek-R1）单次生成可能耗时 1-2 分钟</p>
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2.5">温度参数</label>
                <input
                  v-model="settings.temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  class="input-field w-full px-4 py-3 text-sm"
                />
                <p class="text-xs text-slate-400 mt-2">0-1之间，值越大输出越随机</p>
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2.5">最大Token数</label>
                <input
                  v-model="settings.max_tokens"
                  type="number"
                  class="input-field w-full px-4 py-3 text-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2.5">请求超时(秒)</label>
                <input
                  v-model="settings.timeout"
                  type="number"
                  class="input-field w-full px-4 py-3 text-sm"
                />
              </div>
            </div>

            <button
              @click="saveSettings"
              :disabled="saving"
              class="w-full py-3.5 rounded-xl flex items-center justify-center gap-2.5 text-sm font-semibold transition-all"
              :class="[
                saving
                  ? 'bg-slate-400 cursor-not-allowed'
                  : 'btn-primary'
              ]"
            >
              <span v-if="saving" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <Save v-else class="w-5 h-5" />
              {{ saving ? '保存中...' : '保存配置' }}
            </button>
          </div>
        </div>

        <div class="card p-7">
          <h3 class="text-lg font-bold text-slate-900 mb-6 flex items-center gap-3">
            <Globe class="w-5 h-5 text-violet-600" />
            店铺设置
          </h3>

          <div class="space-y-6">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-2.5">店铺名称</label>
              <input
                v-model="storeSettings.name"
                class="input-field w-full px-4 py-3 text-sm"
                placeholder="请输入店铺名称"
              />
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-2.5">店铺地址</label>
              <input
                v-model="storeSettings.address"
                class="input-field w-full px-4 py-3 text-sm"
                placeholder="请输入店铺地址"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2.5">目标市场</label>
                <select v-model="storeSettings.market" class="input-field w-full px-4 py-3 text-sm">
                  <option value="global">全球</option>
                  <option value="us">北美</option>
                  <option value="eu">欧洲</option>
                  <option value="jp">日本</option>
                  <option value="au">澳洲</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2.5">默认语言</label>
                <select v-model="storeSettings.default_language" class="input-field w-full px-4 py-3 text-sm">
                  <option value="en">英语</option>
                  <option value="es">西班牙语</option>
                  <option value="de">德语</option>
                  <option value="fr">法语</option>
                </select>
              </div>
            </div>

            <button
              @click="saveStoreSettings"
              :disabled="saving"
              class="w-full py-3.5 rounded-xl flex items-center justify-center gap-2.5 text-sm font-semibold transition-all"
              :class="[
                saving
                  ? 'bg-slate-400 cursor-not-allowed'
                  : 'btn-primary'
              ]"
            >
              <span v-if="saving" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <Save v-else class="w-5 h-5" />
              {{ saving ? '保存中...' : '保存店铺设置' }}
            </button>
          </div>
        </div>
      </div>

      <div>
        <div class="card p-6 mb-6">
          <h3 class="text-lg font-bold text-slate-900 mb-4">系统状态</h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-sm text-slate-600">API连接</span>
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span class="text-sm text-green-600 font-medium">正常</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-slate-600">服务状态</span>
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span class="text-sm text-green-600 font-medium">运行中</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-slate-600">版本</span>
              <span class="text-sm text-slate-700 font-medium">1.0.0</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-slate-600">上次更新</span>
              <span class="text-sm text-slate-700 font-medium">2024-01-15</span>
            </div>
          </div>
        </div>

        <div class="card p-6">
          <h3 class="text-lg font-bold text-slate-900 mb-4">快捷操作</h3>
          <div class="space-y-3">
            <button class="w-full flex items-center justify-between p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-violet-100 flex items-center justify-center">
                  <RotateCcw class="w-5 h-5 text-violet-600" />
                </div>
                <span class="text-sm font-semibold text-slate-700">重置配置</span>
              </div>
              <ChevronRight class="w-5 h-5 text-slate-400" />
            </button>
            <button class="w-full flex items-center justify-between p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <HelpCircle class="w-5 h-5 text-blue-600" />
                </div>
                <span class="text-sm font-semibold text-slate-700">帮助文档</span>
              </div>
              <ChevronRight class="w-5 h-5 text-slate-400" />
            </button>
            <button class="w-full flex items-center justify-between p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                  <FileQuestion class="w-5 h-5 text-amber-600" />
                </div>
                <span class="text-sm font-semibold text-slate-700">API使用说明</span>
              </div>
              <ChevronRight class="w-5 h-5 text-slate-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Key, Save, Globe, RotateCcw, HelpCircle, FileQuestion, ChevronRight } from 'lucide-vue-next'
import { settingsAPI } from '../api/client'
import { ElMessage } from 'element-plus'

const saving = ref(false)

const settings = reactive({
  api_key: '',
  api_endpoint: 'https://ark.cn-beijing.volces.com/api/v3',
  model: 'ep-20260405222155-5xsbr',
  temperature: 0.7,
  max_tokens: 2000,
  timeout: 120
})

const storeSettings = reactive({
  name: '',
  address: '',
  market: 'global',
  default_language: 'en'
})

// 页面加载时从后端读取已有配置
async function loadSettings() {
  try {
    const response = await settingsAPI.get()
    if (response.data.success) {
      const api = response.data.data.api
      if (api) {
        settings.api_key = api.api_key || ''
        settings.api_endpoint = api.api_endpoint || 'https://ark.cn-beijing.volces.com/api/v3'
        settings.model = api.model || 'ep-20260405222155-5xsbr'
        settings.temperature = api.temperature ?? 0.7
        settings.max_tokens = api.max_tokens ?? 2000
        settings.timeout = api.timeout ?? 120
      }
      const store = response.data.data.store
      if (store) {
        storeSettings.name = store.name || ''
        storeSettings.address = store.address || ''
        storeSettings.market = store.market || 'global'
        storeSettings.default_language = store.default_language || 'en'
      }
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}
loadSettings()

async function saveSettings() {
  saving.value = true

  try {
    const response = await settingsAPI.update({
      type: 'api',
      data: settings
    })

    if (response.data.success) {
      ElMessage.success('API配置保存成功')
    } else {
      ElMessage.error('保存失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('保存过程中发生错误')
  } finally {
    saving.value = false
  }
}

async function saveStoreSettings() {
  saving.value = true

  try {
    const response = await settingsAPI.update({
      type: 'store',
      data: storeSettings
    })

    if (response.data.success) {
      ElMessage.success('店铺设置保存成功')
    } else {
      ElMessage.error('保存失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('保存过程中发生错误')
  } finally {
    saving.value = false
  }
}
</script>
