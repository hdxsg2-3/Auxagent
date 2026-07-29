<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">客服应答</h2>
        <p class="text-sm text-slate-500 mt-2">AI自动回复客户咨询，7x24小时在线服务</p>
      </div>
      <div class="flex gap-3">
        <el-select v-model="selectedShopId" placeholder="选择店铺" size="default" style="width: 180px">
          <el-option v-for="shop in shopList" :key="shop.id" :label="`${shop.name} (${shop.platform.toUpperCase()})`" :value="shop.id" />
        </el-select>
        <button @click="syncShopMessages" :disabled="syncLoading" class="btn-secondary px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm">
          <Store class="w-4 h-4" />
          {{ syncLoading ? '同步中...' : '同步店铺消息' }}
        </button>
        <button @click="loadMessages" class="btn-secondary px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm">
          <RefreshCw class="w-4 h-4" />
          刷新
        </button>
        <button @click="clearAll" class="px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm bg-red-500 text-white hover:bg-red-600 transition-colors">
          <Trash2 class="w-4 h-4" />
          全部清除
        </button>
        <button @click="showKnowledgeDialog = true" class="px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm bg-amber-500 text-white hover:bg-amber-600 transition-colors">
          <BookOpen class="w-4 h-4" />
          知识库
        </button>
        <button class="btn-primary px-5 py-2.5 rounded-xl flex items-center gap-2 text-sm">
          <Download class="w-4 h-4" />
          导出报告
        </button>
      </div>
    </div>

    <!-- 调用历史记录 -->
    <div class="mb-7 card p-4">
      <div class="flex items-center justify-between">
        <button @click="showHistory = !showHistory" class="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-violet-600 transition-colors">
          <History class="w-4 h-4" />
          调用历史（{{ invocationHistory.length }}）
        </button>
        <button v-if="invocationHistory.length" @click="clearInvocationHistory" class="text-xs text-slate-400 hover:text-red-500 transition-colors">清空</button>
      </div>
      <div v-if="showHistory && invocationHistory.length" class="mt-3 space-y-2 max-h-72 overflow-y-auto">
        <div
          v-for="item in invocationHistory"
          :key="item.id"
          @click="selectHistoryItem(item)"
          :class="[
            'flex items-center justify-between gap-3 p-3 rounded-lg border cursor-pointer transition-all',
            selectedHistoryId === item.id
              ? 'border-violet-400 bg-violet-50 shadow-sm'
              : 'border-slate-200 hover:border-violet-300 hover:bg-violet-50/50'
          ]"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span
                class="text-xs px-2 py-0.5 rounded-full"
                :class="item.status === 'failed' ? 'bg-red-50 text-red-600' : item.status === 'auto_replied' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'"
              >{{ item.status === 'failed' ? '失败' : item.status === 'auto_replied' ? '已回复' : item.status === 'pending' ? '待人工' : item.status }}</span>
              <span class="text-xs text-slate-400">{{ formatTime(item.created_at) }}</span>
              <span class="text-xs text-slate-400">{{ item.platform }}</span>
              <span v-if="item.latency_ms" class="text-xs text-slate-400">{{ Math.round(item.latency_ms / 1000 * 10) / 10 }}s</span>
            </div>
            <p class="text-sm text-slate-700 truncate">客户：{{ truncateText(item.customer_message, 40) }}</p>
            <p v-if="item.ai_response" class="text-xs text-slate-400 truncate mt-0.5">回复：{{ truncateText(item.ai_response, 40) }}</p>
          </div>
        </div>
      </div>
      <p v-if="showHistory && !invocationHistory.length" class="mt-3 text-sm text-slate-400">暂无调用历史，AI 生成回复后将自动保存到这里</p>
    </div>

    <!-- 消息与详情大容器 -->
    <div class="card h-[600px] flex overflow-hidden">
      <!-- 左侧：消息列表 -->
      <div class="w-[40%] flex-shrink-0 flex flex-col overflow-hidden border-r border-slate-100 p-6">
        <div class="flex items-center justify-between mb-6 shrink-0">
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

        <div class="space-y-3 overflow-y-auto scrollbar-thin flex-1 min-h-0">
          <div
            v-for="(msg, index) in filteredMessages"
            :key="msg.id"
            @click="selectMessage(index)"
            class="p-4 rounded-xl border transition-all cursor-pointer min-h-[120px] flex flex-col"
            :class="[
              selectedIndex === index
                ? 'border-violet-500 bg-violet-50'
                : msg.status === 'pending'
                  ? 'border-amber-300 bg-amber-50/30'
                  : 'border-slate-200 hover:border-violet-300 hover:bg-violet-50/50'
            ]"
          >
            <div class="flex items-start gap-3 flex-1">
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
                          {{ msg.status === 'pending' ? 'AI回复中...' : msg.status === 'auto_replied' ? '已自动回复' : '已人工回复' }}
                        </span>
                      </div>
                    </div>
                <p class="text-sm text-slate-500 mt-1 line-clamp-2">{{ msg.message }}</p>
                <!-- 客户咨询中文翻译预览 -->
                <div v-if="msg.message_zh" class="mt-1.5 text-xs text-violet-500 line-clamp-1">
                  {{ msg.message_zh }}
                </div>
                <!-- AI 回复预览 -->
                <div v-if="msg.response" class="mt-2 pl-3 border-l-2 border-green-400">
                  <p class="text-xs text-green-700 line-clamp-2">{{ msg.response }}</p>
                </div>
                <!-- 人工回复预览 -->
                <div v-if="msg.manual_response" class="mt-2 pl-3 border-l-2 border-amber-400">
                  <p class="text-xs text-amber-700 line-clamp-2 flex items-center gap-1">
                    <UserCheck class="w-3 h-3" /> {{ msg.manual_response }}
                  </p>
                  <p v-if="msg.manual_response_translated && msg.manual_response_translated !== msg.manual_response" class="text-[10px] text-amber-500 mt-0.5 flex items-center gap-1">
                    <Languages class="w-3 h-3" /> 已自动翻译为客户语言
                  </p>
                </div>
                <div class="flex items-center gap-2 mt-2">
                  <span :class="platformClass(msg.platform)" class="text-xs px-2 py-0.5 rounded-full">
                  {{ platformLabel(msg.platform) }}
                </span>
                  <span class="text-xs text-slate-400">{{ msg.created_at }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：消息详情 -->
      <div class="flex-1 flex flex-col overflow-hidden p-7">
        <div v-if="!selectedMessage && !selectedHistoryItem" class="flex flex-col items-center justify-center flex-1 text-center">
          <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mb-5">
            <MessageSquare class="w-10 h-10 text-slate-400" />
          </div>
          <p class="text-slate-500 font-medium">选择一条消息或调用记录查看详情</p>
          <p class="text-sm text-slate-400 mt-1">点击查看AI已生成的回复详情</p>
        </div>

        <!-- 调用历史详情 -->
        <div v-else-if="selectedHistoryItem" class="overflow-y-auto flex-1 min-h-0">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-lg font-bold text-slate-900">调用记录详情</h3>
              <p class="text-sm text-slate-500 mt-1">记录ID: {{ selectedHistoryItem.id }}</p>
            </div>
            <button @click="clearHistorySelection" class="text-sm text-slate-400 hover:text-slate-600 flex items-center gap-1">
              <X class="w-4 h-4" /> 关闭
            </button>
          </div>

          <div class="flex items-center gap-2 mb-6">
            <span :class="platformClass(selectedHistoryItem.platform)" class="text-xs px-3 py-1.5 rounded-full font-semibold">
              {{ platformLabel(selectedHistoryItem.platform) }}
            </span>
            <span :class="[
              selectedHistoryItem.status === 'failed' ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600',
              'text-xs px-3 py-1.5 rounded-full font-semibold'
            ]">
              {{ selectedHistoryItem.status === 'failed' ? '失败' : '成功' }}
            </span>
            <span class="text-xs text-slate-400">{{ formatTime(selectedHistoryItem.created_at) }}</span>
            <span v-if="selectedHistoryItem.latency_ms" class="text-xs text-slate-400">{{ Math.round(selectedHistoryItem.latency_ms / 1000 * 10) / 10 }}s</span>
          </div>

          <div class="bg-gradient-to-r from-violet-50 to-purple-50 rounded-xl p-6 mb-6">
            <h4 class="text-sm font-semibold text-slate-600 mb-3">客户咨询</h4>
            <p class="text-slate-800 leading-relaxed whitespace-pre-wrap">{{ selectedHistoryItem.customer_message }}</p>
          </div>

          <div v-if="selectedHistoryItem.ai_response" class="space-y-4">
            <h4 class="text-sm font-semibold text-slate-700">AI 自动回复</h4>
            <div class="bg-green-50 rounded-xl p-6 border border-green-200">
              <p class="text-slate-800 leading-relaxed whitespace-pre-wrap">{{ selectedHistoryItem.ai_response }}</p>
            </div>
          </div>

          <div v-if="selectedHistoryItem.status === 'failed'" class="mt-6 bg-red-50 rounded-xl p-6 border border-red-200">
            <h4 class="text-sm font-semibold text-red-700 mb-2">失败原因</h4>
            <p class="text-sm text-red-600">调用失败，请检查服务配置或网络状态。</p>
          </div>
        </div>

        <div v-else class="overflow-y-auto flex-1 min-h-0">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-lg font-bold text-slate-900">{{ selectedMessage.customer_name }}</h3>
              <p class="text-sm text-slate-500 mt-1">消息ID: {{ selectedMessage.id }}</p>
            </div>
            <div class="flex items-center gap-2">
            <span :class="platformClass(selectedMessage.platform)" class="text-xs px-3 py-1.5 rounded-full font-semibold">
              {{ platformLabel(selectedMessage.platform) }}
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
            <!-- 客户咨询中文翻译 -->
            <div v-if="selectedMessage.message_zh" class="mt-3 pt-3 border-t border-violet-200/60">
              <p class="text-xs text-violet-500 font-medium mb-1 flex items-center gap-1">
                <Languages class="w-3 h-3" /> 中文翻译
              </p>
              <p class="text-sm text-slate-600 leading-relaxed">{{ selectedMessage.message_zh }}</p>
            </div>
          </div>

          <!-- ===== AI 自动回复 ===== -->
          <div class="space-y-4">
            <h4 class="text-sm font-semibold text-slate-700">AI 自动回复</h4>

            <div v-if="selectedMessage.response">
              <div class="bg-green-50 rounded-xl p-6 border border-green-200">
                <p class="text-slate-800 leading-relaxed">{{ selectedMessage.response }}</p>
                <div v-if="selectedMessage.response_zh" class="mt-4 pt-4 border-t border-green-200/60">
                  <p class="text-xs text-green-600 font-medium mb-2 flex items-center gap-1">
                    <Languages class="w-3 h-3" /> 中文翻译
                  </p>
                  <p class="text-sm text-slate-700 leading-relaxed">{{ selectedMessage.response_zh }}</p>
                </div>
              </div>
            </div>

            <div v-else class="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center">
              <div class="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
                <Bot class="w-8 h-8 text-slate-400" />
              </div>
              <p class="text-slate-500 font-medium mb-1.5">AI 回复生成失败</p>
              <p class="text-xs text-slate-400">请检查网络后重试</p>
            </div>
          </div>

          <!-- ===== 人工处理 ===== -->
          <div class="space-y-4 mt-6">
            <h4 class="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <UserCheck class="w-4 h-4 text-amber-600" />
              人工处理
            </h4>

            <!-- 已有人工回复：展示 -->
            <div v-if="selectedMessage.manual_response && !manualEditing" class="bg-amber-50 rounded-xl p-6 border border-amber-200 space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-xs px-2 py-0.5 rounded-full bg-amber-200 text-amber-700 font-medium">人工已回复</span>
                <div class="flex gap-2">
                  <button @click="copyManualReply" class="text-xs text-amber-600 hover:text-amber-800 transition-colors flex items-center gap-1">
                    <Copy class="w-3 h-3" /> 复制中文
                  </button>
                  <button @click="startManualEdit" class="text-xs text-amber-600 hover:text-amber-800 transition-colors flex items-center gap-1">
                    <Pencil class="w-3 h-3" /> 修改
                  </button>
                </div>
              </div>
              <!-- 中文原文 -->
              <div>
                <p class="text-xs text-amber-600 font-medium mb-1">中文原文</p>
                <p class="text-slate-800 leading-relaxed whitespace-pre-wrap">{{ selectedMessage.manual_response }}</p>
              </div>
              <!-- 客户语言版本（自动翻译） -->
              <div v-if="selectedMessage.manual_response_translated && selectedMessage.manual_response_translated !== selectedMessage.manual_response" class="pt-4 border-t border-amber-200/60">
                <p class="text-xs text-amber-600 font-medium mb-2 flex items-center gap-1">
                  <Languages class="w-3 h-3" /> 客户语言版本（自动翻译）
                </p>
                <p class="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{{ selectedMessage.manual_response_translated }}</p>
              </div>
            </div>

            <!-- 编写人工回复（编辑 / 新增） -->
            <div v-if="manualEditing" class="border-2 border-amber-300 rounded-xl p-5 bg-amber-50/30 space-y-3">
              <div class="flex items-center gap-2 text-sm text-amber-700 font-medium">
                <Edit3 class="w-4 h-4" />
                {{ selectedMessage.manual_response ? '修改人工回复' : '编写人工回复' }}
              </div>
              <textarea
                v-model="manualReplyText"
                class="input-field w-full h-32 p-3 text-sm resize-none"
                :placeholder="selectedMessage.response
                  ? '你可以引用 AI 回复，也可以完全自定义人工回复的内容...'
                  : 'AI 尚未生成回复，请直接输入人工回复内容...'"
              ></textarea>
              <div class="flex gap-2">
                <button
                  @click="submitManualReply"
                  :disabled="manualSubmitting || !manualReplyText.trim()"
                  class="btn-primary px-5 py-2 rounded-lg text-sm font-semibold flex items-center gap-1.5"
                >
                  <span v-if="manualSubmitting" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  <Send v-else class="w-4 h-4" />
                  {{ manualSubmitting ? '提交中...' : '提交回复' }}
                </button>
                <button @click="cancelManualEdit" class="btn-secondary px-5 py-2 rounded-lg text-sm font-semibold">取消</button>
              </div>
              <p class="text-xs text-slate-400">人工回复提交后将直接更新为最终回复内容。</p>
            </div>

            <!-- 未有人工回复且未在编辑中：入口按钮 -->
            <div v-if="!selectedMessage.manual_response && !manualEditing">
              <button
                @click="startManualEdit"
                class="w-full border-2 border-dashed border-amber-300 rounded-xl p-6 text-center hover:bg-amber-50/50 transition-colors group"
              >
                <div class="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-3 group-hover:bg-amber-200 transition-colors">
                  <MessageSquare class="w-6 h-6 text-amber-600" />
                </div>
                <p class="text-sm font-semibold text-amber-700 group-hover:text-amber-800">点击编写人工回复</p>
                <p class="text-xs text-amber-500 mt-1">可引用 AI 回复内容进行修改，或完全自定义</p>
              </button>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div v-if="selectedMessage.response || selectedMessage.manual_response" class="flex flex-wrap gap-3 mt-6">
            <button
              v-if="selectedMessage.response"
              @click="copyReply"
              class="flex-1 btn-secondary py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2"
            >
              <Copy class="w-4 h-4" /> 复制 AI 回复
            </button>
            <button
              v-if="selectedMessage.response_zh"
              @click="copyReplyZh"
              class="btn-outline px-5 py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2"
            >
              <Languages class="w-4 h-4" /> 复制翻译
            </button>
            <button
              v-if="selectedMessage.manual_response"
              @click="copyManualReply"
              class="btn-outline px-5 py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2"
            >
              <Copy class="w-4 h-4" /> 复制人工回复
            </button>
            <button
              v-if="selectedMessage.manual_response_translated && selectedMessage.manual_response_translated !== selectedMessage.manual_response"
              @click="copyManualReplyTranslated"
              class="btn-outline px-5 py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2"
            >
              <Languages class="w-4 h-4" /> 复制客户语言版
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 知识库管理弹窗 -->
    <el-dialog
      v-model="showKnowledgeDialog"
      title="知识库管理"
      width="800px"
      align-center
      append-to-body
      destroy-on-close
      class="kb-dialog"
    >
      <div class="flex gap-4 mb-5">
        <button
          v-for="cat in kbCategories"
          :key="cat.value"
          @click="kbFilter = kbFilter === cat.value ? '' : cat.value"
          class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-all"
          :class="kbFilter === cat.value ? 'bg-violet-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >{{ cat.label }}</button>
      </div>

      <!-- 新增表单 -->
      <div class="mb-4 p-4 rounded-xl border border-violet-200 bg-violet-50/50 space-y-3">
        <div class="flex items-center gap-2 text-sm font-semibold text-violet-700">
          <Plus class="w-4 h-4" /> {{ kbEditingId ? '编辑知识条目' : '新增知识条目' }}
        </div>
        <select v-model="kbForm.category" class="input-field px-3 py-2 text-sm w-full">
          <option v-for="cat in kbCategories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
        </select>
        <input v-model="kbForm.title" class="input-field w-full px-3 py-2 text-sm" placeholder="标题（如：30天退货政策）" />
        <textarea v-model="kbForm.content" class="input-field w-full px-3 py-2 text-sm" rows="3" placeholder="详细内容（如：本店支持30天内无理由退货...）"></textarea>
        <div class="flex gap-2">
          <button @click="saveKnowledgeEntry" :disabled="kbSaving" class="btn-primary px-5 py-2 rounded-lg text-sm">
            {{ kbSaving ? '保存中...' : (kbEditingId ? '更新' : '添加') }}
          </button>
          <button v-if="kbEditingId" @click="cancelKbEdit" class="btn-secondary px-5 py-2 rounded-lg text-sm">取消</button>
        </div>
      </div>

      <!-- 知识条目列表 -->
      <div class="max-h-80 overflow-y-auto space-y-2">
        <div v-if="kbLoading" class="text-center py-8 text-slate-400 text-sm">加载中...</div>
        <div v-else-if="filteredKnowledge.length === 0" class="text-center py-8 text-slate-400 text-sm">
          {{ kbFilter ? '该分类下暂无条目' : '知识库为空，请添加第一条知识' }}
        </div>
        <div
          v-for="item in filteredKnowledge"
          :key="item.id"
          class="p-3 rounded-lg border border-slate-200 hover:border-violet-200 transition-colors"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="px-2 py-0.5 text-xs rounded-full" :class="kbCategoryClass(item.category)">
                  {{ kbCategoryLabel(item.category) }}
                </span>
                <span class="text-sm font-semibold text-slate-800 truncate">{{ item.title }}</span>
              </div>
              <p class="text-xs text-slate-500 line-clamp-2">{{ item.content }}</p>
            </div>
            <div class="flex items-center gap-1 shrink-0">
              <button @click="editKnowledgeEntry(item)" class="p-1.5 text-slate-400 hover:text-violet-500 rounded transition-colors" title="编辑">
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button @click="deleteKnowledgeEntry(item.id)" class="p-1.5 text-slate-400 hover:text-red-500 rounded transition-colors" title="删除">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400">共 {{ knowledgeEntries.length }} 条知识</span>
          <button @click="showKnowledgeDialog = false" class="btn-secondary px-5 py-2 rounded-lg text-sm">关闭</button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { RefreshCw, Download, MessageSquare, Bot, Copy, Languages, Trash2, Plus, Store, BookOpen, Pencil, History, UserCheck, Send, Edit3, X } from 'lucide-vue-next'
import { customerServiceAPI, customerServiceMessagesAPI, platformAPI, customerServiceKnowledgeAPI, customerServiceMemoryAPI, customerServiceHistoryAPI } from '../api/client'
import { ElMessage, ElMessageBox } from 'element-plus'

const emit = defineEmits(['pending-count-changed'])

const activeTab = ref('all')
const selectedIndex = ref(-1)
const selectedHistoryId = ref(null)

const shopList = ref([])
const selectedShopId = ref(null)
const syncLoading = ref(false)

const tabs = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待处理' },
  { value: 'replied', label: '已回复' }
]

function platformLabel(platform) {
  const map = { amazon: 'Amazon', ebay: 'eBay', aliexpress: 'AliExpress', temu: 'Temu' }
  return map[platform] || platform
}
function platformClass(platform) {
  const map = {
    amazon: 'bg-orange-50 text-orange-600',
    ebay: 'bg-blue-50 text-blue-600',
    aliexpress: 'bg-red-50 text-red-600',
    temu: 'bg-red-100 text-red-700'
  }
  return map[platform] || ''
}

const messages = ref([])
const showAddForm = ref(false)
const newMsg = reactive({ customer_name: '', platform: 'amazon', message: '' })

async function loadMessages() {
  try {
    const res = await customerServiceMessagesAPI.list()
    if (res.data.success) {
      messages.value = res.data.data
      // 加载后自动处理所有待回复消息
      autoReplyAllPendingSilent()
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
      // 先加入列表显示为"AI回复中..."
      const msg = {
        id,
        customer_name: newMsg.customer_name || '客户',
        message: newMsg.message,
        message_zh: '',
        platform: newMsg.platform,
        category: 'general',
        status: 'pending',
        response: '',
        response_zh: '',
        created_at: ''
      }
      messages.value.unshift(msg)
      newMsg.customer_name = ''
      newMsg.message = ''
      showAddForm.value = false
      ElMessage.success('AI 自动回复中...')
      // 立即自动回复新加的消息
      await autoReplySingle(id)
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

async function clearAll() {
  if (messages.value.length === 0) {
    ElMessage.info('没有消息可清除')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要清除全部 ${messages.value.length} 条消息吗？此操作不可恢复。`,
      '确认清除',
      { confirmButtonText: '确认清除', cancelButtonText: '取消', type: 'warning' }
    )
    await customerServiceMessagesAPI.clear()
    messages.value = []
    selectedIndex.value = -1
    ElMessage.success('已清除全部消息')
  } catch (e) {
    if (e !== 'cancel') {
      console.error('清除消息失败', e)
      ElMessage.error('清除失败')
    }
  }
}

onMounted(() => {
  loadMessages()
  loadShops()
  loadKnowledge()
  loadInvocationHistory()
})

async function loadShops() {
  try {
    const res = await platformAPI.list()
    if (res.data.success) {
      shopList.value = res.data.data || []
      if (shopList.value.length && !selectedShopId.value) {
        selectedShopId.value = shopList.value[0].id
      }
    }
  } catch (e) {
    console.error('加载店铺失败', e)
  }
}

async function syncShopMessages() {
  if (!selectedShopId.value) {
    ElMessage.warning('请先选择店铺')
    return
  }
  syncLoading.value = true
  try {
    const res = await platformAPI.syncMessages(selectedShopId.value)
    ElMessage.success(`同步成功：${(res.data.data?.messages || []).length} 条消息`)
    await loadMessages()
  } catch (e) {
    ElMessage.error('同步失败：' + (e.response?.data?.message || e.message))
  } finally {
    syncLoading.value = false
  }
}

// 单个消息自动回复（先更新本地状态，再持久化到数据库）
async function autoReplySingle(id) {
  const msg = messages.value.find(m => m.id === id)
  if (!msg) return
  try {
    const aiRes = await customerServiceAPI.process({
      message: msg.message,
      message_id: msg.id,
      platform: msg.platform,
      buyer_id: msg.customer_name || ''
    })
    if (!aiRes.data.success) return
    const reply = aiRes.data.data
    // 立即更新响应式数组中的对象，触发 UI 更新
    msg.response = reply.response
    msg.response_zh = reply.response_zh || ''
    msg.message_zh = reply.message_zh || ''
    msg.status = 'auto_replied'
    // 后台持久化到数据库（不阻塞 UI）
    customerServiceMessagesAPI.update(msg.id, {
      response: reply.response,
      response_zh: reply.response_zh || '',
      message_zh: reply.message_zh || '',
      status: 'auto_replied'
    }).catch(e => console.error('保存回复失败', e))
    // 刷新调用历史
    loadInvocationHistory().catch(() => {})
  } catch (e) {
    console.error('自动回复单条失败', e)
  }
}

// 静默处理所有待回复消息（不弹窗，后台自动执行）
async function autoReplyAllPendingSilent() {
  const pending = messages.value.filter(m => m.status === 'pending' && !m.response)
  if (!pending.length) return

  for (const msg of pending) {
    await autoReplySingle(msg.id)
  }
}

// ────────── 知识库管理 ──────────
const showKnowledgeDialog = ref(false)

// 打开知识库弹窗时刷新列表
watch(showKnowledgeDialog, (val) => {
  if (val) loadKnowledge()
})

const knowledgeEntries = ref([])
const kbLoading = ref(false)
const kbSaving = ref(false)
const kbFilter = ref('')
const kbEditingId = ref(null)

const kbCategories = [
  { value: 'policy', label: '售后规则' },
  { value: 'faq', label: '常见FAQ' },
  { value: 'product', label: '商品信息' },
  { value: 'style', label: '文案风格' }
]

const kbForm = reactive({ title: '', content: '', category: 'faq' })

function kbCategoryLabel(cat) {
  const found = kbCategories.find(c => c.value === cat)
  return found ? found.label : cat
}

function kbCategoryClass(cat) {
  const map = {
    policy: 'bg-red-50 text-red-600',
    faq: 'bg-blue-50 text-blue-600',
    product: 'bg-green-50 text-green-600',
    style: 'bg-amber-50 text-amber-600'
  }
  return map[cat] || 'bg-slate-50 text-slate-600'
}

const filteredKnowledge = computed(() => {
  if (!kbFilter.value) return knowledgeEntries.value
  return knowledgeEntries.value.filter(e => e.category === kbFilter.value)
})

async function loadKnowledge() {
  kbLoading.value = true
  try {
    const res = await customerServiceKnowledgeAPI.list()
    if (res.data.success) knowledgeEntries.value = res.data.data || []
  } catch (e) {
    console.error('加载知识库失败', e)
  } finally {
    kbLoading.value = false
  }
}

async function saveKnowledgeEntry() {
  if (!kbForm.title.trim() || !kbForm.content.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  kbSaving.value = true
  try {
    if (kbEditingId.value) {
      await customerServiceKnowledgeAPI.update(kbEditingId.value, {
        title: kbForm.title,
        content: kbForm.content,
        category: kbForm.category
      })
      ElMessage.success('知识条目已更新')
    } else {
      await customerServiceKnowledgeAPI.add({
        title: kbForm.title,
        content: kbForm.content,
        category: kbForm.category
      })
      ElMessage.success('知识条目已添加，正在构建向量索引...')
      // 异步触发 embedding 生成（不阻塞 UI）
      loadKnowledge().then(() => {
        const latest = knowledgeEntries.value[0]
        if (latest) customerServiceKnowledgeAPI.embed(latest.id).catch(() => {})
      })
    }
    resetKbForm()
    await loadKnowledge()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.message || e.message))
  } finally {
    kbSaving.value = false
  }
}

function editKnowledgeEntry(item) {
  kbEditingId.value = item.id
  kbForm.title = item.title
  kbForm.content = item.content
  kbForm.category = item.category
}

function cancelKbEdit() {
  resetKbForm()
}

function resetKbForm() {
  kbEditingId.value = null
  kbForm.title = ''
  kbForm.content = ''
  kbForm.category = 'faq'
}

async function deleteKnowledgeEntry(id) {
  try {
    await ElMessageBox.confirm('确定要删除该知识条目吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await customerServiceKnowledgeAPI.remove(id)
    knowledgeEntries.value = knowledgeEntries.value.filter(e => e.id !== id)
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// ────────── 调用历史记录 ──────────
const showHistory = ref(false)
const invocationHistory = ref([])

async function loadInvocationHistory() {
  try {
    const res = await customerServiceHistoryAPI.list()
    if (res.data.success) invocationHistory.value = res.data.data || []
  } catch (e) {
    console.error('加载调用历史失败', e)
  }
}

async function clearInvocationHistory() {
  try {
    await ElMessageBox.confirm('确定要清空所有调用历史记录吗？', '确认清空', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await customerServiceHistoryAPI.clear()
    invocationHistory.value = []
    ElMessage.success('调用历史已清空')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}

function formatTime(value) {
  return value ? String(value).replace('T', ' ').substring(0, 16) : ''
}

function truncateText(text, maxLen) {
  const s = (text || '').trim()
  return s.length > maxLen ? s.slice(0, maxLen) + '…' : s
}

const selectedMessage = computed(() => {
  return selectedIndex.value >= 0 ? messages.value[selectedIndex.value] : null
})

const filteredMessages = computed(() => {
  if (activeTab.value === 'all') return messages.value
  if (activeTab.value === 'pending') return messages.value.filter(m => m.status === 'pending')
  return messages.value.filter(m => m.status !== 'pending')
})

const pendingCount = computed(() => messages.value.filter(m => m.status === 'pending').length)
watch(pendingCount, (count) => {
  emit('pending-count-changed', count)
}, { immediate: true })

function selectMessage(index) {
  selectedIndex.value = index
  selectedHistoryId.value = null
  // 切换消息时重置人工编辑状态
  manualEditing.value = false
  manualReplyText.value = ''
}

const selectedHistoryItem = computed(() => {
  return invocationHistory.value.find(item => item.id === selectedHistoryId.value) || null
})

function selectHistoryItem(item) {
  selectedHistoryId.value = item.id
  selectedIndex.value = -1
  // 关闭可能的人工编辑状态
  manualEditing.value = false
  manualReplyText.value = ''
}

function clearHistorySelection() {
  selectedHistoryId.value = null
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

// ────────── 人工回复功能 ──────────
const manualEditing = ref(false)
const manualReplyText = ref('')
const manualSubmitting = ref(false)

function startManualEdit() {
  const msg = selectedMessage.value
  if (!msg) return
  // 如果已有人工回复，预填为编辑内容；如果只有 AI 回复，可选引用 AI 回复
  manualReplyText.value = msg.manual_response || msg.response || ''
  manualEditing.value = true
}

function cancelManualEdit() {
  manualEditing.value = false
  manualReplyText.value = ''
}

async function submitManualReply() {
  const msg = selectedMessage.value
  if (!msg || !manualReplyText.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  manualSubmitting.value = true
  try {
    const { data: resp } = await customerServiceMessagesAPI.update(msg.id, {
      manual_response: manualReplyText.value.trim(),
      status: 'manual_replied',
      response: msg.response || '',
      response_zh: msg.response_zh || '',
      message_zh: msg.message_zh || ''
    })
    // 更新本地状态（后端会自动翻译成客户语言）
    msg.manual_response = manualReplyText.value.trim()
    msg.manual_response_translated = resp.data?.manual_response_translated || manualReplyText.value.trim()
    msg.status = 'manual_replied'
    manualEditing.value = false
    manualReplyText.value = ''
    ElMessage.success('人工回复已保存并自动翻译')
  } catch (e) {
    console.error('保存人工回复失败', e)
    ElMessage.error('保存失败：' + (e.response?.data?.message || e.message))
  } finally {
    manualSubmitting.value = false
  }
}

async function copyManualReply() {
  const text = selectedMessage.value?.manual_response
  if (!text) {
    ElMessage.warning('暂无可复制的人工回复')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制人工回复')
  } catch (e) {
    console.error(e)
    ElMessage.error('复制失败，请手动复制')
  }
}

async function copyManualReplyTranslated() {
  const text = selectedMessage.value?.manual_response_translated
  if (!text) {
    ElMessage.warning('暂无可复制的客户语言版本')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制客户语言版本')
  } catch (e) {
    console.error(e)
    ElMessage.error('复制失败，请手动复制')
  }
}
</script>

<style scoped>
.kb-dialog :deep(.el-dialog__header) {
  padding-right: 48px;
}
.kb-dialog :deep(.el-dialog__title) {
  font-weight: 600;
  font-size: 1.125rem;
  line-height: 1.5;
  overflow: visible;
  white-space: nowrap;
}
.kb-dialog :deep(.el-dialog__body) {
  max-height: calc(90vh - 180px);
  overflow-y: auto;
  padding-top: 12px;
}
</style>
