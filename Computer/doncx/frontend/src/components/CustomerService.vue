<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">客服应答</h2>
        <p class="text-sm text-slate-500 mt-2">AI自动回复客户咨询，7x24小时在线服务</p>
      </div>
      <div class="flex gap-3">
        <button @click="loadMessages" class="btn-secondary px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm">
          <RefreshCw class="w-4 h-4" />
          刷新
        </button>
        <button class="btn-primary px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm">
          <Download class="w-4 h-4" />
          导出报告
        </button>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <div class="col-span-1 card p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-slate-900">消息列表</h3>
          <div class="flex items-center gap-2">
            <button
              @click="showAddForm = !showAddForm"
              class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1"
              :class="showAddForm ? 'bg-violet-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            >
              <Plus class="w-3.5 h-3.5" />
              新建
            </button>
            <div class="flex gap-2">
              <button
                v-for="tab in tabs"
                :key="tab.value"
                @click="activeTab = tab.value"
                class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-all"
                :class="[
                  activeTab === tab.value
                    ? 'bg-violet-500 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                ]"
              >
                {{ tab.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- 录入新客户消息 -->
        <div v-if="showAddForm" class="mb-4 p-4 rounded-xl border border-violet-200 bg-violet-50/50 space-y-3">
          <input
            v-model="newMsg.customer_name"
            class="input-field w-full px-3 py-2 text-sm"
            placeholder="客户名称（可选）"
          />
          <select v-model="newMsg.platform" class="input-field px-3 py-2 text-sm">
            <option value="amazon">Amazon</option>
            <option value="ebay">eBay</option>
            <option value="aliexpress">AliExpress</option>
          </select>
          <textarea
            v-model="newMsg.message"
            class="input-field w-full h-24 p-3 text-sm resize-none"
            placeholder="粘贴客户消息内容…"
          ></textarea>
          <div class="flex gap-2">
            <button @click="addMessage" class="flex-1 btn-primary py-2 rounded-lg text-sm font-semibold">录入</button>
            <button @click="showAddForm = false" class="px-4 btn-outline py-2 rounded-lg text-sm font-semibold">取消</button>
          </div>
        </div>

        <p v-if="!filteredMessages.length" class="text-sm text-slate-400 text-center py-10">
          暂无消息，点击右上角「新建」录入客户咨询
        </p>

        <div class="space-y-3 max-h-[500px] overflow-y-auto scrollbar-thin">
          <div
            v-for="(msg, index) in filteredMessages"
            :key="msg.id"
            @click="selectMessage(index)"
            class="p-4 rounded-xl border transition-all cursor-pointer"
            :class="[
              selectedIndex === index
                ? 'border-violet-500 bg-violet-50'
                : 'border-slate-200 hover:border-violet-300 hover:bg-violet-50/50'
            ]"
          >
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white font-semibold flex-shrink-0">
                {{ msg.customer_name.charAt(0) }}
              </div>
              <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                      <span class="font-semibold text-slate-800 text-sm">{{ msg.customer_name }}</span>
                      <div class="flex items-center gap-2">
                        <button @click.stop="deleteMessage(msg.id)" class="text-slate-300 hover:text-red-500 transition-colors shrink-0">
                          <Trash2 class="w-4 h-4" />
                        </button>
                        <span :class="[
                          msg.status === 'pending' ? 'tag-warning' : '',
                          msg.status === 'auto_replied' ? 'tag-success' : '',
                          msg.status === 'manual_replied' ? 'tag-info' : ''
                        ]" class="text-xs px-2 py-0.5 rounded-full">
                          {{ msg.status === 'pending' ? '待处理' : msg.status === 'auto_replied' ? '已自动回复' : '已人工回复' }}
                        </span>
                      </div>
                    </div>
                <p class="text-sm text-slate-500 mt-1 line-clamp-2">{{ msg.message }}</p>
                <div class="flex items-center gap-2 mt-2">
                  <span :class="[
                    msg.platform === 'amazon' ? 'bg-orange-50 text-orange-600' : '',
                    msg.platform === 'ebay' ? 'bg-blue-50 text-blue-600' : '',
                    msg.platform === 'aliexpress' ? 'bg-red-50 text-red-600' : ''
                  ]" class="text-xs px-2 py-0.5 rounded-full">
                    {{ msg.platform === 'amazon' ? 'Amazon' : msg.platform === 'ebay' ? 'eBay' : 'AliExpress' }}
                  </span>
                  <span class="text-xs text-slate-400">{{ msg.created_at }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-span-2 card p-7">
        <div v-if="!selectedMessage" class="flex flex-col items-center justify-center h-[500px] text-center">
          <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mb-5">
            <MessageSquare class="w-10 h-10 text-slate-400" />
          </div>
          <p class="text-slate-500 font-medium">选择一条消息查看详情</p>
          <p class="text-sm text-slate-400 mt-1">AI将自动生成回复建议</p>
        </div>

        <div v-else>
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-lg font-bold text-slate-900">{{ selectedMessage.customer_name }}</h3>
              <p class="text-sm text-slate-500 mt-1">消息ID: {{ selectedMessage.id }}</p>
            </div>
            <div class="flex items-center gap-2">
              <span :class="[
                selectedMessage.platform === 'amazon' ? 'bg-orange-50 text-orange-600' : '',
                selectedMessage.platform === 'ebay' ? 'bg-blue-50 text-blue-600' : '',
                selectedMessage.platform === 'aliexpress' ? 'bg-red-50 text-red-600' : ''
              ]" class="text-xs px-3 py-1.5 rounded-full font-semibold">
                {{ selectedMessage.platform === 'amazon' ? 'Amazon' : selectedMessage.platform === 'ebay' ? 'eBay' : 'AliExpress' }}
              </span>
              <span :class="[
                selectedMessage.status === 'pending' ? 'tag-warning' : '',
                selectedMessage.status === 'auto_replied' ? 'tag-success' : '',
                selectedMessage.status === 'manual_replied' ? 'tag-info' : ''
              ]" class="text-xs px-3 py-1.5 rounded-full font-semibold">
                {{ selectedMessage.status === 'pending' ? '待处理' : selectedMessage.status === 'auto_replied' ? '已自动回复' : '已人工回复' }}
              </span>
            </div>
          </div>

          <div class="bg-gradient-to-r from-violet-50 to-purple-50 rounded-xl p-6 mb-6">
            <h4 class="text-sm font-semibold text-slate-600 mb-3">客户咨询</h4>
            <p class="text-slate-800 leading-relaxed">{{ selectedMessage.message }}</p>
          </div>

          <div class="space-y-4">
            <h4 class="text-sm font-semibold text-slate-700">AI回复建议（客户语言）</h4>
            
            <div v-if="selectedMessage.response">
              <div class="bg-green-50 rounded-xl p-6 border border-green-200">
                <p class="text-slate-800 leading-relaxed">{{ selectedMessage.response }}</p>
              </div>
            </div>

            <div v-else class="border-2 border-dashed border-violet-200 rounded-xl p-8 text-center">
              <div class="w-16 h-16 rounded-full bg-violet-100 flex items-center justify-center mx-auto mb-4">
                <Bot class="w-8 h-8 text-violet-600" />
              </div>
              <p class="text-slate-500 font-medium mb-2">点击下方按钮生成AI回复</p>
              <p class="text-sm text-slate-400">AI将根据店铺规则自动生成回复内容</p>
            </div>

            <div v-if="selectedMessage.response_zh" class="mt-5">
              <h4 class="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-2">
                <Languages class="w-4 h-4 text-violet-500" />
                中文翻译（供商家核对回复是否准确）
              </h4>
              <div class="bg-violet-50 rounded-xl p-6 border border-violet-200">
                <p class="text-slate-800 leading-relaxed">{{ selectedMessage.response_zh }}</p>
              </div>
            </div>
          </div>

          <div class="flex flex-wrap gap-3 mt-6">
            <button
              v-if="!selectedMessage.response"
              @click="autoReply"
              :disabled="replying"
              class="flex-1 py-3.5 rounded-xl flex items-center justify-center gap-2.5 text-sm font-semibold transition-all"
              :class="[
                replying
                  ? 'bg-slate-400 cursor-not-allowed'
                  : 'btn-primary'
              ]"
            >
              <span v-if="replying" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <Bot v-else class="w-5 h-5" />
              {{ replying ? '生成中...' : 'AI自动回复' }}
            </button>
            <button
              v-if="selectedMessage.response"
              @click="copyReply"
              class="flex-1 btn-secondary py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2"
            >
              <Copy class="w-4 h-4" /> 复制回复
            </button>
            <button
              v-if="selectedMessage.response_zh"
              @click="copyReplyZh"
              class="btn-outline px-5 py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2"
            >
              <Languages class="w-4 h-4" /> 复制翻译
            </button>
            <button class="btn-outline px-6 py-3.5 rounded-xl font-semibold">
              人工处理
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { RefreshCw, Download, MessageSquare, Bot, Copy, Languages, Trash2, Plus } from 'lucide-vue-next'
import { customerServiceAPI, customerServiceMessagesAPI } from '../api/client'
import { ElMessage } from 'element-plus'

const activeTab = ref('all')
const selectedIndex = ref(-1)
const replying = ref(false)

const tabs = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待处理' },
  { value: 'replied', label: '已回复' }
]

const messages = ref([])
const showAddForm = ref(false)
const newMsg = reactive({ customer_name: '', platform: 'amazon', message: '' })

async function loadMessages() {
  try {
    const res = await customerServiceMessagesAPI.list()
    if (res.data.success) {
      messages.value = res.data.data
    }
  } catch (e) {
    console.error('加载消息失败', e)
  }
}

async function addMessage() {
  if (!newMsg.message.trim()) {
    ElMessage.warning('请输入客户消息内容')
    return
  }
  try {
    const res = await customerServiceMessagesAPI.add({
      customer_name: newMsg.customer_name || '客户',
      platform: newMsg.platform,
      message: newMsg.message
    })
    if (res.data.success) {
      const id = res.data.data.id
      messages.value.unshift({
        id,
        customer_name: newMsg.customer_name || '客户',
        message: newMsg.message,
        platform: newMsg.platform,
        category: 'general',
        status: 'pending',
        response: '',
        response_zh: '',
        created_at: ''
      })
      newMsg.customer_name = ''
      newMsg.message = ''
      showAddForm.value = false
      ElMessage.success('消息已录入')
    }
  } catch (e) {
    console.error('录入消息失败', e)
    ElMessage.error('录入消息失败')
  }
}

async function deleteMessage(id) {
  try {
    await customerServiceMessagesAPI.remove(id)
    messages.value = messages.value.filter(m => m.id !== id)
    if (selectedIndex.value >= messages.value.length) selectedIndex.value = -1
  } catch (e) {
    console.error('删除消息失败', e)
  }
}

onMounted(() => {
  loadMessages()
})

const selectedMessage = computed(() => {
  return selectedIndex.value >= 0 ? messages.value[selectedIndex.value] : null
})

const filteredMessages = computed(() => {
  if (activeTab.value === 'all') return messages.value
  if (activeTab.value === 'pending') return messages.value.filter(m => m.status === 'pending')
  return messages.value.filter(m => m.status !== 'pending')
})

function selectMessage(index) {
  selectedIndex.value = index
}

async function autoReply() {
  if (!selectedMessage.value) return

  replying.value = true

  try {
    const response = await customerServiceAPI.process({
      message: selectedMessage.value.message,
      message_id: selectedMessage.value.id,
      platform: selectedMessage.value.platform
    })

    if (response.data.success) {
      const reply = response.data.data
      const idx = selectedIndex.value
      messages.value[idx].response = reply.response
      messages.value[idx].response_zh = reply.response_zh || ''
      messages.value[idx].status = reply.status
      try {
        await customerServiceMessagesAPI.update(messages.value[idx].id, {
          response: reply.response,
          response_zh: reply.response_zh || '',
          status: reply.status
        })
      } catch (e) {
        console.error('保存回复失败', e)
      }
      ElMessage.success('回复生成成功')
    } else {
      ElMessage.error(response.data.message || '回复生成失败')
    }
  } catch (error) {
    console.error(error)
    const errorMsg = error.response?.data?.message || error.message || '生成回复过程中发生错误'
    ElMessage.error(errorMsg)
  } finally {
    replying.value = false
  }
}

async function copyReply() {
  const text = selectedMessage.value?.response
  if (!text) {
    ElMessage.warning('暂无可复制的回复')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制回复内容')
  } catch (e) {
    console.error(e)
    ElMessage.error('复制失败，请手动复制')
  }
}

async function copyReplyZh() {
  const text = selectedMessage.value?.response_zh
  if (!text) {
    ElMessage.warning('暂无可复制的翻译')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制中文翻译')
  } catch (e) {
    console.error(e)
    ElMessage.error('复制失败，请手动复制')
  }
}
</script>
