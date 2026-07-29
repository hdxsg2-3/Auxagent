<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">多语种文案生成</h2>
        <p class="text-sm text-slate-500 mt-2">输入中文产品描述，或粘贴 1688 链接一键生成上架文案</p>
      </div>
    </div>

    <!-- 模式切换 -->
    <div class="flex gap-3 mb-7">
      <button
        @click="mode = 'manual'"
        class="px-5 py-2.5 rounded-xl text-sm font-semibold border-2 transition-all"
        :class="mode === 'manual' ? 'border-violet-500 bg-violet-50 text-violet-600' : 'border-slate-200 text-slate-600 hover:border-violet-300'"
      >
        手动输入
      </button>
      <button
        @click="mode = 'link'"
        class="px-5 py-2.5 rounded-xl text-sm font-semibold border-2 transition-all flex items-center gap-2"
        :class="mode === 'link' ? 'border-violet-500 bg-violet-50 text-violet-600' : 'border-slate-200 text-slate-600 hover:border-violet-300'"
      >
        <Link class="w-4 h-4" />
        链接一键生成
      </button>
      <button
        @click="mode = 'batch'"
        class="px-5 py-2.5 rounded-xl text-sm font-semibold border-2 transition-all flex items-center gap-2"
        :class="mode === 'batch' ? 'border-violet-500 bg-violet-50 text-violet-600' : 'border-slate-200 text-slate-600 hover:border-violet-300'"
      >
        <Layers class="w-4 h-4" />
        批量操作
      </button>
    </div>

    <!-- 使用记录（本地持久化，刷新不丢） -->
    <div class="mb-7 card p-4">
      <div class="flex items-center justify-between">
        <button @click="showHistory = !showHistory" class="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-violet-600 transition-colors">
          <History class="w-4 h-4" />
          使用记录（{{ history.length }}）
        </button>
        <button v-if="history.length" @click="clearHistory" class="text-xs text-slate-400 hover:text-red-500 transition-colors">清空</button>
      </div>
      <div v-if="showHistory && history.length" class="mt-3 space-y-2 max-h-72 overflow-y-auto scrollbar-thin">
        <div
          v-for="item in history"
          :key="item.id"
          class="flex items-center justify-between gap-3 p-3 rounded-lg border border-slate-200 hover:border-violet-300 hover:bg-violet-50/50 transition-all"
        >
          <button @click="restoreHistory(item)" class="flex-1 text-left min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-xs px-2 py-0.5 rounded-full" :class="item.mode === 'link' ? 'bg-blue-50 text-blue-600' : 'bg-violet-50 text-violet-600'">{{ item.mode === 'link' ? '链接' : '手动' }}</span>
              <span class="text-xs text-slate-400">{{ formatTime(item.created_at) }}</span>
            </div>
            <p class="text-sm text-slate-700 truncate mt-1">{{ historySummary(item) }}</p>
          </button>
          <button @click="removeHistory(item.id)" class="text-slate-300 hover:text-red-500 transition-colors shrink-0">
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>
      <p v-if="showHistory && !history.length" class="mt-3 text-sm text-slate-400">暂无使用记录，生成文案后会自动保存到这里</p>
    </div>

    <!-- 品类与风格记忆看板 -->
    <div class="mb-7 card p-4">
      <div class="flex items-center justify-between">
        <button @click="showStyleMemory = !showStyleMemory" class="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-violet-600 transition-colors">
          <BookOpen class="w-4 h-4" />
          品类记忆（{{ styleMemoryCount }} 条）
        </button>
        <button v-if="styleMemoryCount" @click="clearStyleMemory" class="text-xs text-slate-400 hover:text-red-500 transition-colors">清空记忆</button>
      </div>
      <div v-if="showStyleMemory && styleMemoryCount" class="mt-3">
        <!-- 品类统计 -->
        <div class="flex flex-wrap gap-2 mb-3">
          <div
            v-for="stat in categoryStats"
            :key="stat.name"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
            :class="stat.name === '其他' ? 'bg-slate-100 text-slate-600' : 'bg-violet-50 text-violet-700 border border-violet-200'"
          >
            <span>{{ stat.name }}</span>
            <span class="w-4 h-4 rounded-full bg-violet-200 text-violet-700 text-[10px] flex items-center justify-center">{{ stat.count }}</span>
          </div>
        </div>
        <!-- 最近记忆列表 -->
        <div class="space-y-1.5 max-h-48 overflow-y-auto scrollbar-thin">
          <div
            v-for="item in recentStyleMemory"
            :key="item.id"
            class="flex items-center justify-between gap-2 p-2 rounded-lg border border-slate-100 hover:border-violet-200 hover:bg-violet-50/30 transition-all"
          >
            <div class="flex items-center gap-2 min-w-0 flex-1">
              <span class="text-xs px-1.5 py-0.5 rounded bg-violet-100 text-violet-700 font-medium shrink-0">{{ item.category }}</span>
              <span class="text-xs text-slate-400 shrink-0">{{ item.platform.toUpperCase() }}</span>
              <span class="text-xs text-slate-500 truncate">{{ item.title || item.productDesc }}</span>
              <span class="text-[10px] text-slate-400 shrink-0">{{ formatTime(item.created_at) }}</span>
            </div>
            <button @click="removeStyleMemory(item.id)" class="text-slate-300 hover:text-red-500 transition-colors shrink-0">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
      <p v-if="showStyleMemory && !styleMemoryCount" class="mt-3 text-sm text-slate-400">暂无品类记忆，生成文案后会自动记录品类和风格特征</p>
    </div>

    <!-- ===================== 手动输入模式 ===================== -->
    <div v-if="mode === 'manual'" class="grid grid-cols-2 gap-7">
      <div class="card p-7">
        <h3 class="text-lg font-bold text-slate-900 mb-6">产品信息输入</h3>

        <div class="space-y-6">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2.5">产品描述</label>
            <textarea
              v-model="form.product_desc"
              @input="onProductDescChange"
              class="input-field w-full h-40 p-4 text-sm resize-none"
              placeholder="请输入中文产品描述，例如：白色2万毫安充电宝，带数显，支持双USB输出"
            ></textarea>
            <!-- 风格记忆推荐 -->
            <div v-if="styleRecommendations.length" class="mt-3">
              <div class="flex items-center gap-1.5 mb-2">
                <span class="text-xs font-semibold text-violet-600">📋 历史风格参考</span>
                <span class="text-xs text-slate-400">（基于品类「{{ currentCategory }}」推荐）</span>
              </div>
              <div class="space-y-1.5">
                <div
                  v-for="rec in styleRecommendations"
                  :key="rec.id"
                  class="flex items-center gap-2 p-2 rounded-lg bg-violet-50/70 border border-violet-100 hover:border-violet-300 transition-all cursor-pointer"
                  @click="applyStyleRecommendation(rec)"
                  :title="'点击应用此风格'"
                >
                  <span class="text-xs px-1.5 py-0.5 rounded bg-violet-200 text-violet-700 font-medium shrink-0">{{ rec.category }}</span>
                  <span class="text-xs text-slate-500 shrink-0">{{ rec.platform.toUpperCase() }}</span>
                  <span class="text-xs text-slate-400 shrink-0">{{ rec.language.toUpperCase() }}</span>
                  <span class="text-xs text-slate-500 truncate flex-1">{{ rec.title || rec.productDesc }}</span>
                  <span class="text-[10px] text-slate-400 shrink-0">{{ formatTime(rec.created_at) }}</span>
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-violet-100 text-violet-600 shrink-0">{{ rec.styleFeatures?.title_style || '—' }}</span>
                </div>
              </div>
              <p class="text-[10px] text-slate-400 mt-1">点击可快速填充对应平台和语言，点击「智能生成」即可沿用类似风格</p>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-2.5">目标平台</label>
              <div class="flex flex-wrap gap-2.5">
                <button
                  v-for="p in platforms"
                  :key="p.value"
                  @click="form.platform = p.value"
                  class="px-5 py-2.5 rounded-xl text-sm font-semibold border-2 transition-all"
                  :class="[
                    form.platform === p.value
                      ? 'border-violet-500 bg-violet-50 text-violet-600'
                      : 'border-slate-200 text-slate-600 hover:border-violet-300 hover:bg-violet-50/50'
                  ]"
                >
                  <component :is="p.icon" class="w-4 h-4 inline mr-1.5" />
                  {{ p.label }}
                </button>
              </div>
            </div>

            <div>
              <label class="block text-sm font-semibold text-slate-700 mb-2.5">目标语言</label>
              <div class="flex flex-wrap gap-2.5">
                <button
                  v-for="l in languages"
                  :key="l.value"
                  @click="form.target_language = l.value"
                  class="px-5 py-2.5 rounded-xl text-sm font-semibold border-2 transition-all"
                  :class="[
                    form.target_language === l.value
                      ? 'border-violet-500 bg-violet-50 text-violet-600'
                      : 'border-slate-200 text-slate-600 hover:border-violet-300 hover:bg-violet-50/50'
                  ]"
                >
                  {{ l.label }}
                </button>
              </div>
            </div>
          </div>

          <button
            @click="generateCopy"
            :disabled="loading"
            class="w-full py-3.5 rounded-xl flex items-center justify-center gap-2.5 text-sm font-semibold transition-all"
            :class="[
              loading
                ? 'bg-slate-400 cursor-not-allowed'
                : 'btn-primary'
            ]"
          >
            <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <Sparkles v-else class="w-5 h-5" />
            {{ loading ? 'AI 生成中（约 30~60 秒，请耐心等待）...' : '智能生成文案' }}
          </button>
        </div>
      </div>

      <div class="card p-7">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-slate-900">生成结果</h3>
          <div class="flex gap-2.5">
            <button
              @click="copyAll"
              :disabled="!result"
              class="px-5 py-2.5 rounded-xl text-sm flex items-center gap-2 transition-all"
              :class="[
                result
                  ? 'btn-secondary'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              ]"
            >
              <Copy class="w-4 h-4" />
              复制全部
            </button>
            <button
              @click="translateCopy"
              :disabled="!result"
              class="px-5 py-2.5 rounded-xl text-sm flex items-center gap-2 transition-all"
              :class="[
                result
                  ? 'btn-outline'
                  : 'border-2 border-slate-200 text-slate-400 cursor-not-allowed'
              ]"
            >
              <Languages class="w-4 h-4" />
              切换语言
            </button>
            <button
              @click="scanComplianceNow"
              :disabled="!result || complianceScanning"
              class="px-5 py-2.5 rounded-xl text-sm flex items-center gap-2 transition-all"
              :class="[
                result && !complianceScanning
                  ? 'btn-outline border-amber-300 text-amber-700 hover:bg-amber-50'
                  : 'border-2 border-slate-200 text-slate-400 cursor-not-allowed'
              ]"
            >
              <span v-if="complianceScanning" class="w-4 h-4 border-2 border-amber-300/30 border-t-amber-500 rounded-full animate-spin"></span>
              <ShieldCheck v-else class="w-4 h-4" />
              {{ complianceScanning ? '合规扫描中...' : (result?.compliance_scan ? '重新合规扫描' : '合规扫描') }}
            </button>
          </div>
        </div>

        <div v-if="!result" class="text-center py-16">
          <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-5">
            <PenTool class="w-10 h-10 text-slate-400" />
          </div>
          <p class="text-slate-500 font-medium">输入产品描述后点击"智能生成"</p>
        </div>

        <div v-else class="space-y-6">
          <div class="flex items-center gap-2 flex-wrap">
            <span
              v-if="result.compliance?.rewritten"
              class="px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700 border border-amber-200"
            >
              已自动合规改写（{{ result.compliance.notes?.length || 0 }} 处）
            </span>
            <span
              v-else-if="result.compliance_scan"
              :class="[
                'px-2.5 py-1 rounded-full text-xs font-medium border',
                result.compliance?.risk === 'high' ? 'bg-red-100 text-red-700 border-red-200'
                  : result.compliance?.risk === 'medium' ? 'bg-amber-100 text-amber-700 border-amber-200'
                  : 'bg-emerald-100 text-emerald-700 border-emerald-200'
              ]"
            >
              合规扫描：{{ result.compliance?.risk === 'high' ? '存在高风险' : result.compliance?.risk === 'medium' ? '存在中风险' : '已通过' }}
            </span>
            <span
              v-else
              class="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-500 border border-slate-200"
            >
              ⏱ 未做合规扫描（生成更快，可点击「合规扫描」按钮按需检测）
            </span>
          </div>

          <div
            v-if="result.compliance_scan && !result.compliance_scan.clean && result.compliance?.notes?.length"
            class="text-xs text-amber-700 bg-amber-50 rounded-lg p-3 border border-amber-100"
          >
            <p class="font-medium mb-1">合规扫描建议：</p>
            <ul class="list-disc list-inside space-y-0.5">
              <li v-for="(note, i) in result.compliance.notes" :key="i">{{ note }}</li>
            </ul>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-2">标题 (Title)</label>
            <div class="bg-gradient-to-r from-violet-50 to-purple-50 rounded-xl p-4 border border-violet-100">
              <p class="text-base font-bold text-slate-900">{{ result.title }}</p>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-2">核心卖点 (Bullet Points)</label>
            <ul class="space-y-2.5">
              <li
                v-for="(point, index) in result.bullet_points"
                :key="index"
                class="flex items-start gap-2 p-3 bg-violet-50/50 rounded-lg"
              >
                <span class="w-5 h-5 rounded-full bg-violet-500 text-white text-xs flex items-center justify-center flex-shrink-0 mt-0.5">{{ index + 1 }}</span>
                <span class="text-sm text-slate-700">{{ point }}</span>
              </li>
            </ul>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-500 mb-2">商品详情 (Description)</label>
            <div class="bg-gradient-to-r from-violet-50 to-purple-50 rounded-xl p-4 border border-violet-100">
              <p class="text-sm text-slate-700 leading-relaxed">{{ result.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== 链接一键生成模式 ===================== -->
    <div v-else-if="mode === 'link'">
      <!-- 输入区 -->
      <div class="card p-7 mb-7">
        <h3 class="text-lg font-bold text-slate-900 mb-6">1688 商品链接</h3>
        <div class="flex flex-col sm:flex-row gap-3">
          <input
            v-model="linkUrl"
            @input="validateLink"
            type="text"
            class="input-field flex-1 px-4 py-3 text-sm"
            :class="linkError ? 'border-red-300 focus:ring-red-300' : ''"
            placeholder="粘贴 1688 商品详情页链接，例如 https://detail.1688.com/offer/xxxx.html"
          />
          <button
            @click="generateFromLink"
            :disabled="linkLoading || !isValidLink"
            class="px-6 py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all whitespace-nowrap"
            :class="linkLoading || !isValidLink ? 'bg-slate-400 cursor-not-allowed' : 'btn-primary'"
          >
            <span v-if="linkLoading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <Zap v-else class="w-4 h-4" />
            {{ linkLoading ? 'AI 生成中（约 1~2 分钟，请耐心等待）...' : '一键生成上架文案' }}
          </button>
        </div>
        <p v-if="linkError" class="text-xs text-red-500 mt-2">{{ linkError }}</p>
        <p v-else class="text-xs text-slate-400 mt-2">
          仅支持 1688 商品详情页链接（含 1688.com）。系统将自动完成：抓取 → 提炼 → 生成英/西/德/中四语种 Listing → 风控校验 → 输出可上架文本。
        </p>
      </div>

      <!-- 执行链路进度 -->
      <div v-if="linkLoading" class="card p-7 mb-7">
        <h3 class="text-lg font-bold text-slate-900 mb-5">智能 Agent 执行链路</h3>
        <div class="space-y-3">
          <div v-for="(s, i) in pipelineSteps" :key="i" class="flex items-center gap-3">
            <span class="w-6 h-6 rounded-full bg-violet-100 text-violet-600 text-xs flex items-center justify-center flex-shrink-0">{{ i + 1 }}</span>
            <span class="text-sm text-slate-700">{{ s }}</span>
            <span class="ml-auto text-xs text-violet-500 animate-pulse">执行中...</span>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="linkResultError" class="card p-7 mb-7 border border-red-200 bg-red-50/50">
        <h3 class="text-lg font-bold text-red-600 mb-3 flex items-center gap-2">
          <AlertTriangle class="w-5 h-5" />
          生成失败
        </h3>
        <div class="text-sm text-slate-700 whitespace-pre-line leading-relaxed">
          {{ linkResultError }}
        </div>
      </div>

      <!-- 结果区 -->
      <div v-if="linkResult">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-slate-900">生成结果</h3>
          <button @click="copyAllLink" class="btn-secondary px-5 py-2.5 rounded-xl text-sm flex items-center gap-2">
            <Copy class="w-4 h-4" />
            复制全部结果
          </button>
        </div>

        <!-- 板块 1：原始抓取内容 -->
        <div class="card p-7 mb-7">
          <div class="flex items-center justify-between mb-5">
            <h4 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <span class="w-7 h-7 rounded-lg bg-slate-100 text-slate-500 text-xs flex items-center justify-center">1</span>
              原始抓取内容
            </h4>
            <button @click="copyRaw" class="btn-outline px-4 py-2 rounded-lg text-xs flex items-center gap-1.5">
              <Copy class="w-3.5 h-3.5" />复制
            </button>
          </div>
          <div class="space-y-4 text-sm">
            <div>
              <span class="font-semibold text-slate-600">商品标题：</span>
              <span class="text-slate-800">{{ linkResult.raw_scraped.title || '—' }}</span>
            </div>
            <div>
              <span class="font-semibold text-slate-600">规格参数：</span>
              <div v-if="linkResult.raw_scraped.specs && linkResult.raw_scraped.specs.length" class="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div v-for="(s, i) in linkResult.raw_scraped.specs" :key="i" class="flex gap-2 p-2.5 bg-slate-50 rounded-lg">
                  <span class="text-slate-500 shrink-0">{{ s.key }}：</span>
                  <span class="text-slate-800">{{ s.value }}</span>
                </div>
              </div>
              <span v-else class="text-slate-400">未提取到</span>
            </div>
            <div>
              <span class="font-semibold text-slate-600">详情文字介绍：</span>
              <div class="mt-2 max-h-52 overflow-auto bg-slate-50 rounded-lg p-3 text-slate-700 whitespace-pre-wrap leading-relaxed">
                {{ linkResult.raw_scraped.description_text || '—' }}
              </div>
            </div>
            <div v-if="linkResult.raw_scraped.advantages && linkResult.raw_scraped.advantages.length">
              <span class="font-semibold text-slate-600">产品优势描述：</span>
              <ul class="mt-2 space-y-1 list-disc list-inside text-slate-700">
                <li v-for="(a, i) in linkResult.raw_scraped.advantages" :key="i">{{ a }}</li>
              </ul>
            </div>
            <div v-if="linkResult.raw_scraped.notes && linkResult.raw_scraped.notes.length" class="text-xs text-amber-600 space-y-1">
              <p v-for="(n, i) in linkResult.raw_scraped.notes" :key="i">⚠ {{ n }}</p>
            </div>
          </div>
        </div>

        <!-- 板块 2：AI 提炼信息 -->
        <div class="card p-7 mb-7">
          <div class="flex items-center justify-between mb-5">
            <h4 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <span class="w-7 h-7 rounded-lg bg-violet-100 text-violet-600 text-xs flex items-center justify-center">2</span>
              AI 提炼信息
            </h4>
            <button @click="copyRefined" class="btn-outline px-4 py-2 rounded-lg text-xs flex items-center gap-1.5">
              <Copy class="w-3.5 h-3.5" />复制
            </button>
          </div>
          <div v-if="linkResult.refined_info" class="space-y-4 text-sm">
            <div v-if="linkResult.refined_info.product_name">
              <span class="font-semibold text-slate-600">产品名称：</span>
              <span class="text-slate-800">{{ linkResult.refined_info.product_name }}</span>
            </div>
            <div v-if="linkResult.refined_info.core_selling_points && linkResult.refined_info.core_selling_points.length">
              <span class="font-semibold text-slate-600">核心卖点：</span>
              <ul class="mt-2 space-y-1.5 list-decimal list-inside text-slate-700">
                <li v-for="(p, i) in linkResult.refined_info.core_selling_points" :key="i">{{ p }}</li>
              </ul>
            </div>
            <div v-if="linkResult.refined_info.key_parameters && linkResult.refined_info.key_parameters.length">
              <span class="font-semibold text-slate-600">关键参数：</span>
              <ul class="mt-2 space-y-1.5 list-disc list-inside text-slate-700">
                <li v-for="(p, i) in linkResult.refined_info.key_parameters" :key="i">{{ p }}</li>
              </ul>
            </div>
            <div v-if="linkResult.refined_info.applicable_scenarios && linkResult.refined_info.applicable_scenarios.length">
              <span class="font-semibold text-slate-600">适用场景：</span>
              <div class="mt-2 flex flex-wrap gap-2">
                <span v-for="(s, i) in linkResult.refined_info.applicable_scenarios" :key="i" class="px-3 py-1 bg-violet-50 text-violet-600 text-xs rounded-full">{{ s }}</span>
              </div>
            </div>
            <div v-if="linkResult.refined_info.clean_description">
              <span class="font-semibold text-slate-600">产品简介：</span>
              <p class="mt-2 text-slate-700 leading-relaxed">{{ linkResult.refined_info.clean_description }}</p>
            </div>
            <p v-if="linkResult.raw_scraped.refine_note" class="text-xs text-amber-600">⚠ {{ linkResult.raw_scraped.refine_note }}</p>
          </div>
          <div v-else class="text-sm text-slate-400">提炼未执行（已使用原始抓取文本直接生成文案）。</div>
        </div>

        <!-- 板块 3：多语种成品 Listing -->
        <div class="card p-7 mb-7">
          <div class="flex items-center justify-between mb-5">
            <h4 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <span class="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-600 text-xs flex items-center justify-center">3</span>
              多语种成品 Listing（亚马逊规范）
            </h4>
            <button @click="copyListing(activeListingLang)" class="btn-outline px-4 py-2 rounded-lg text-xs flex items-center gap-1.5">
              <Copy class="w-3.5 h-3.5" />复制当前语种
            </button>
          </div>
          <div class="flex flex-wrap gap-2 mb-5">
            <button
              v-for="l in listingLangs"
              :key="l.value"
              @click="activeListingLang = l.value"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all"
              :class="activeListingLang === l.value ? 'border-indigo-500 bg-indigo-50 text-indigo-600' : 'border-slate-200 text-slate-600 hover:border-indigo-300'"
            >
              {{ l.label }}
            </button>
          </div>

          <div v-if="currentListing && currentListing.error" class="text-sm text-red-500 p-3 bg-red-50 rounded-lg">
            {{ currentListing.error }}
          </div>
          <div v-else-if="currentListing" class="space-y-5">
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-2">标题 (Title)</label>
              <div class="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-xl p-4 border border-indigo-100">
                <p class="text-base font-bold text-slate-900">{{ currentListing.title }}</p>
              </div>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-2">核心卖点 (Bullet Points)</label>
              <ul class="space-y-2.5">
                <li v-for="(point, index) in currentListing.bullet_points" :key="index" class="flex items-start gap-2 p-3 bg-indigo-50/50 rounded-lg">
                  <span class="w-5 h-5 rounded-full bg-indigo-500 text-white text-xs flex items-center justify-center flex-shrink-0 mt-0.5">{{ index + 1 }}</span>
                  <span class="text-sm text-slate-700">{{ point }}</span>
                </li>
              </ul>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-500 mb-2">商品详情 (Description)</label>
              <div class="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-xl p-4 border border-indigo-100">
                <p class="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{{ currentListing.description }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 板块 4：风控检测报告 -->
        <div class="card p-7 mb-7">
          <div class="flex items-center justify-between mb-5">
            <h4 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <span class="w-7 h-7 rounded-lg bg-rose-100 text-rose-600 text-xs flex items-center justify-center">4</span>
              风控检测报告
            </h4>
            <button @click="copyCompliance(activeListingLang)" class="btn-outline px-4 py-2 rounded-lg text-xs flex items-center gap-1.5">
              <Copy class="w-3.5 h-3.5" />复制当前语种
            </button>
          </div>
          <div class="flex flex-wrap gap-2 mb-5">
            <button
              v-for="l in listingLangs"
              :key="l.value"
              @click="activeComplianceLang = l.value"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all"
              :class="activeComplianceLang === l.value ? 'border-rose-500 bg-rose-50 text-rose-600' : 'border-slate-200 text-slate-600 hover:border-rose-300'"
            >
              {{ l.label }}
            </button>
          </div>

          <div v-if="currentCompliance && currentCompliance.skipped" class="text-sm text-slate-400 p-3 bg-slate-50 rounded-lg">
            {{ currentCompliance.reason }}
          </div>
          <div v-else-if="currentCompliance && currentCompliance.error" class="text-sm text-red-500 p-3 bg-red-50 rounded-lg">
            {{ currentCompliance.error }}
          </div>
          <div v-else-if="currentCompliance" class="space-y-5">
            <div class="flex items-center gap-2">
              <span
                :class="[
                  currentCompliance.overall_risk === 'high' ? 'tag-high' : '',
                  currentCompliance.overall_risk === 'medium' ? 'tag-medium' : '',
                  currentCompliance.overall_risk === 'low' ? 'tag-low' : ''
                ]"
                class="px-3 py-1 rounded-full text-xs font-semibold"
              >
                {{ currentCompliance.overall_risk === 'high' ? '高风险' : currentCompliance.overall_risk === 'medium' ? '中风险' : '低风险' }}
              </span>
              <span v-if="currentCompliance.clean" class="text-xs text-green-600 font-medium">✓ 未发现风险项</span>
            </div>

            <div v-if="currentCompliance.extreme_words && currentCompliance.extreme_words.length">
              <h5 class="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <AlertTriangle class="w-4 h-4 text-red-500" />极限词检测
              </h5>
              <ul class="space-y-2">
                <li v-for="(item, i) in currentCompliance.extreme_words" :key="i" class="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                  <span class="text-sm text-red-700">{{ item.word }}</span>
                  <span class="text-xs text-red-500">{{ item.suggestion }}</span>
                </li>
              </ul>
            </div>

            <div v-if="currentCompliance.copyright_issues && currentCompliance.copyright_issues.length">
              <h5 class="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <Copyright class="w-4 h-4 text-amber-500" />版权风险检测
              </h5>
              <ul class="space-y-2">
                <li v-for="(item, i) in currentCompliance.copyright_issues" :key="i" class="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                  <span class="text-sm text-amber-700">{{ item.description }}</span>
                  <span class="text-xs text-amber-500">{{ item.risk_level }}</span>
                </li>
              </ul>
            </div>

            <div v-if="currentCompliance.forbidden_words && currentCompliance.forbidden_words.length">
              <h5 class="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <XCircle class="w-4 h-4 text-orange-500" />违禁词检测
              </h5>
              <ul class="space-y-2">
                <li v-for="(item, i) in currentCompliance.forbidden_words" :key="i" class="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                  <span class="text-sm text-orange-700">{{ item.word }}</span>
                  <span class="text-xs text-orange-500">{{ item.category }}</span>
                </li>
              </ul>
            </div>

            <div v-if="currentCompliance.suggestions && currentCompliance.suggestions.length">
              <h5 class="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <Lightbulb class="w-4 h-4 text-violet-500" />优化建议
              </h5>
              <ul class="space-y-2">
                <li v-for="(s, i) in currentCompliance.suggestions" :key="i" class="p-3 bg-violet-50 rounded-lg text-sm text-violet-700">{{ s }}</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- 板块 5：最终可上架文本 -->
        <div class="card p-7 mb-7">
          <div class="flex items-center justify-between mb-5">
            <h4 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <span class="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-600 text-xs flex items-center justify-center">5</span>
              最终可上架文本（可直接复制发布）
            </h4>
            <button @click="copyAllFinal" class="btn-secondary px-5 py-2.5 rounded-xl text-sm flex items-center gap-2">
              <Copy class="w-4 h-4" />
              复制全部可上架文本
            </button>
          </div>
          <div class="flex flex-wrap gap-2 mb-5">
            <button
              v-for="l in listingLangs"
              :key="l.value"
              @click="activeFinalLang = l.value"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all flex items-center gap-1.5"
              :class="activeFinalLang === l.value ? 'border-emerald-500 bg-emerald-50 text-emerald-600' : 'border-slate-200 text-slate-600 hover:border-emerald-300'"
            >
              {{ l.label }}
              <span
                v-if="currentFinal && currentFinal.ready"
                class="w-2 h-2 rounded-full bg-emerald-500"
                title="可直接上架"
              ></span>
              <span
                v-else-if="currentFinal"
                class="w-2 h-2 rounded-full bg-amber-500"
                title="需人工复核"
              ></span>
            </button>
          </div>

          <div v-if="!currentFinal" class="text-sm text-slate-400 p-3 bg-slate-50 rounded-lg">
            该语种文案生成失败，无可上架文本。
          </div>
          <div v-else class="space-y-4">
            <div class="flex items-center gap-2">
              <span
                v-if="currentFinal.ready"
                class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200"
              >
                ✓ 可直接上架
              </span>
              <span
                v-else
                class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200"
              >
                ⚠ 存在风险项，建议人工复核后上架
              </span>
              <span class="text-xs text-slate-400">风险等级：{{ currentFinal.overall_risk }}</span>
              <button @click="copyFinal(activeFinalLang)" class="ml-auto btn-outline px-4 py-2 rounded-lg text-xs flex items-center gap-1.5">
                <Copy class="w-3.5 h-3.5" />复制本语种
              </button>
            </div>
            <pre class="bg-slate-900 text-slate-100 rounded-xl p-5 text-sm leading-relaxed whitespace-pre-wrap font-mono overflow-auto max-h-96">{{ currentFinal.text }}</pre>

            <!-- 自动上架 -->
            <div class="mt-5 border-t border-slate-200 pt-5">
              <h5 class="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <Store class="w-4 h-4 text-violet-500" />全自动上架到店铺
              </h5>
              <div class="flex flex-col md:flex-row gap-3">
                <el-select v-model="selectedShopId" placeholder="选择店铺" style="min-width: 200px">
                  <el-option v-for="shop in shopList" :key="shop.id" :label="`${shop.name} (${shop.platform.toUpperCase()})`" :value="shop.id" />
                </el-select>
                <el-input v-model="publishSku" placeholder="输入店铺 SKU" style="max-width: 200px" />
                <button @click="publishToShop" :disabled="publishLoading" class="btn-primary px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                  <Zap v-if="!publishLoading" class="w-4 h-4" />
                  <span>{{ publishLoading ? '提交中...' : '上架到选中店铺' }}</span>
                </button>
              </div>
              <p v-if="shopList.length === 0" class="text-xs text-slate-400 mt-2">暂无店铺，请先到「店铺管理」添加 Amazon/Temu 店铺。</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>

  <!-- ===================== 批量操作模式 ===================== -->
  <div v-if="mode === 'batch'">
    <div class="grid grid-cols-2 gap-7">
      <!-- 输入区 -->
      <div class="card p-7">
        <h3 class="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
          <Layers class="w-5 h-5 text-violet-600" />
          批量操作
        </h3>
        <p class="text-sm text-slate-500 mb-5">每行一个产品描述或文案，系统将自动批量处理。</p>

        <div class="flex gap-2 mb-4">
          <button
            @click="batchMode = 'copywriter'"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="batchMode === 'copywriter' ? 'bg-violet-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
          >批量文案生成</button>
          <button
            @click="batchMode = 'compliance'"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="batchMode === 'compliance' ? 'bg-violet-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
          >批量合规扫描</button>
        </div>

        <label class="block text-sm font-semibold text-slate-700 mb-2">
          {{ batchMode === 'copywriter' ? '产品描述列表（每行一个）' : '文案内容列表（每行一个）' }}
        </label>
        <textarea
          v-model="batchInput"
          rows="12"
          class="input-field w-full mb-4"
          :placeholder="batchMode === 'copywriter' ? '例如：\n无线蓝牙耳机 降噪 长续航\nType-C 数据线 快充 1米\n手机支架 桌面 金属' : '例如：\n最好的无线蓝牙耳机，全场最低价\n...'"
        ></textarea>

        <div v-if="batchMode === 'copywriter'" class="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">目标平台</label>
            <select v-model="batchPlatform" class="input-field w-full">
              <option value="amazon">Amazon</option>
              <option value="temu">Temu</option>
              <option value="ebay">eBay</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-2">目标语言</label>
            <select v-model="batchLanguage" class="input-field w-full">
              <option value="en">英文</option>
              <option value="zh">中文</option>
              <option value="ja">日文</option>
              <option value="de">德文</option>
              <option value="fr">法文</option>
            </select>
          </div>
        </div>

        <div v-if="batchMode === 'compliance'" class="space-y-2 mb-4">
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" v-model="batchCheckExtreme" class="rounded border-slate-300" /> 检测极限词
          </label>
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" v-model="batchCheckCopyright" class="rounded border-slate-300" /> 检测版权/商标
          </label>
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" v-model="batchCheckForbidden" class="rounded border-slate-300" /> 检测违禁词
          </label>
        </div>

        <button
          @click="runBatch"
          :disabled="batchLoading || !batchInput.trim()"
          class="btn-primary w-full flex items-center justify-center gap-2"
        >
          <Loader2 v-if="batchLoading" class="w-4 h-4 animate-spin" />
          <Layers v-else class="w-4 h-4" />
          {{ batchLoading ? `处理中 ${batchProgress}/${batchTotal}` : '开始批量处理' }}
        </button>

        <div v-if="batchLoading" class="mt-4">
          <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-violet-600 transition-all duration-300"
              :style="{ width: batchTotal ? (batchProgress / batchTotal * 100) + '%' : '0%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- 结果区 -->
      <div class="card p-7">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-slate-900">处理结果</h3>
          <div class="flex gap-2">
            <button v-if="batchResults.length" @click="exportBatchCSV" class="btn-outline text-sm flex items-center gap-1">
              <Download class="w-4 h-4" /> 导出 CSV
            </button>
            <button v-if="batchResults.length" @click="batchResults = []" class="text-slate-400 hover:text-red-500 text-sm">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div v-if="!batchResults.length" class="text-center py-16 text-slate-400">
          <Layers class="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>批量处理结果将显示在这里</p>
        </div>

        <div v-else class="space-y-4 max-h-[700px] overflow-y-auto pr-2">
          <div
            v-for="(item, idx) in batchResults"
            :key="idx"
            class="border border-slate-200 rounded-xl p-4"
            :class="item.error ? 'bg-red-50 border-red-200' : 'bg-slate-50'"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-mono text-slate-400">#{{ idx + 1 }}</span>
              <span
                v-if="batchMode === 'compliance'"
                class="text-xs px-2 py-0.5 rounded-full"
                :class="item.pass ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'"
              >{{ item.pass ? '通过' : '未通过' }}</span>
            </div>
            <p class="text-sm text-slate-700 mb-2 line-clamp-2">{{ item.input }}</p>
            <div v-if="batchMode === 'copywriter' && item.result" class="text-sm text-slate-800 whitespace-pre-wrap bg-white border border-slate-200 rounded-lg p-3 max-h-48 overflow-y-auto">{{ item.result }}</div>
            <div v-if="batchMode === 'compliance' && item.issues?.length" class="space-y-1">
              <p v-for="(issue, i) in item.issues" :key="i" class="text-sm text-red-600">• {{ issue }}</p>
            </div>
            <p v-if="item.error" class="text-sm text-red-600 mt-2">{{ item.error }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  PenTool, ShoppingCart, Tag, Globe, Sparkles, Copy, Languages,
  Link, Zap, AlertTriangle, Copyright, XCircle, Lightbulb, History, Trash2, Store, ShieldCheck, BookOpen, Layers, Loader2, Download
} from 'lucide-vue-next'
import { copywriterAPI, autoListingAPI, copywriterHistoryAPI, platformAPI, complianceAPI, batchAPI } from '../api/client'
import { ElMessage } from 'element-plus'
import { styleMemory } from '../store/styleMemory'
import { copywriterStore } from '../store/copywriterStore'

// 从全局 store 读取状态（切换页面后生成仍在后台进行，回来时自动恢复）
const loading = computed({
  get: () => copywriterStore.state.manualLoading,
  set: (v) => {}  // 只读，由 store 控制
})
const result = computed(() => copywriterStore.state.manualResult)
const complianceScanning = ref(false)

const form = reactive({
  product_desc: '',
  platform: 'amazon',
  target_language: 'en'
})

const platforms = [
  { value: 'amazon', label: '亚马逊', icon: ShoppingCart },
  { value: 'ebay', label: 'eBay', icon: Tag },
  { value: 'aliexpress', label: '速卖通', icon: Globe }
]

const languages = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: '英语' },
  { value: 'es', label: '西班牙语' },
  { value: 'de', label: '德语' },
  { value: 'fr', label: '法语' }
]

// ============ 链接一键生成相关状态 ============
const mode = ref('manual')
const linkUrl = ref('')
const linkError = ref('')
const isValidLink = ref(false)
// 链接生成状态从全局 Store 读取（切换页面后生成仍在后台继续）
const linkLoading = computed(() => copywriterStore.state.linkLoading)
const linkResult = computed(() => copywriterStore.state.linkResult)
const linkResultError = computed(() => copywriterStore.state.linkError)
const activeListingLang = ref('en')
const activeComplianceLang = ref('en')
const activeFinalLang = ref('en')

// ============ 批量操作相关状态 ============
const batchMode = ref('copywriter')
const batchInput = ref('')
const batchPlatform = ref('amazon')
const batchLanguage = ref('en')
const batchCheckExtreme = ref(true)
const batchCheckCopyright = ref(true)
const batchCheckForbidden = ref(true)
const batchLoading = ref(false)
const batchProgress = ref(0)
const batchTotal = ref(0)
const batchResults = ref([])

// ============ 自动上架到店铺 ============
const selectedShopId = ref(null)
const shopList = ref([])
const publishLoading = ref(false)
const publishSku = ref('')

// ============ 使用记录（后端持久化） ============
const HISTORY_MAX = 50
const showHistory = ref(false)
const history = ref([])

// ============ 品类与风格记忆 ============
const showStyleMemory = ref(false)
const styleMemoryCount = ref(0)
const categoryStats = ref([])
const recentStyleMemory = ref([])
const styleRecommendations = ref([])
const currentCategory = ref('')

function refreshStyleMemory() {
  styleMemoryCount.value = styleMemory.getCount()
  categoryStats.value = styleMemory.getCategoryStats()
  const all = styleMemory.getAll()
  recentStyleMemory.value = all.slice(0, 20)
}

function onProductDescChange() {
  const desc = form.product_desc.trim()
  if (desc.length >= 4) {
    currentCategory.value = styleMemory.extractCategory(desc)
    styleRecommendations.value = styleMemory.recommend(desc, 5)
  } else {
    currentCategory.value = ''
    styleRecommendations.value = []
  }
}

function applyStyleRecommendation(rec) {
  form.platform = rec.platform
  form.target_language = rec.language
  ElMessage.success(`已应用 ${rec.category} 品类风格（${rec.platform.toUpperCase()} / ${rec.language.toUpperCase()}）`)
}

function clearStyleMemory() {
  styleMemory.clear()
  refreshStyleMemory()
  styleRecommendations.value = []
  ElMessage.success('品类记忆已清空')
}

function removeStyleMemory(id) {
  styleMemory.remove(id)
  refreshStyleMemory()
}

async function loadHistory() {
  try {
    const res = await copywriterHistoryAPI.list()
    if (res.data.success) {
      history.value = res.data.data
    }
  } catch (e) {
    console.error('加载文案历史失败', e)
  }
}

async function pushHistory(record) {
  try {
    await copywriterHistoryAPI.add(record)
    await loadHistory()
  } catch (e) {
    console.error('保存文案历史失败', e)
  }
}

function restoreHistory(item) {
  if (item.mode === 'link') {
    copywriterStore.restoreLinkResult(item.result)
    linkUrl.value = item.input_text || ''
    mode.value = 'link'
  } else {
    form.product_desc = item.input_text || ''
    form.platform = item.platform || 'amazon'
    form.target_language = item.language || 'en'
    copywriterStore.restoreManualResult(item.result)
    mode.value = 'manual'
  }
  showHistory.value = false
}

async function removeHistory(id) {
  try {
    await copywriterHistoryAPI.remove(id)
    history.value = history.value.filter(h => h.id !== id)
  } catch (e) {
    console.error('删除历史失败', e)
  }
}

async function clearHistory() {
  try {
    await copywriterHistoryAPI.clear()
    history.value = []
  } catch (e) {
    console.error('清空历史失败', e)
  }
}

function formatTime(value) {
  return value ? String(value) : ''
}

function historySummary(item) {
  if (item.mode === 'link') {
    return item.input_text || '1688 链接生成'
  }
  const desc = (item.input_text || '').trim()
  return desc ? desc.slice(0, 30) + (desc.length > 30 ? '…' : '') : '手动生成'
}

// ============ 批量操作 ============
async function runBatch() {
  const lines = batchInput.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (!lines.length) return
  batchLoading.value = true
  batchTotal.value = lines.length
  batchProgress.value = 0
  batchResults.value = []

  try {
    if (batchMode.value === 'copywriter') {
      const res = await batchAPI.generate({
        items: lines.map(text => ({ product_desc: text })),
        platform: batchPlatform.value,
        target_language: batchLanguage.value
      })
      if (res.data.success) {
        batchResults.value = (res.data.data || []).map((r, i) => {
          let resultText = ''
          if (r.success && r.data) {
            const d = r.data
            resultText = [d.title, (d.bullet_points || []).join('\n'), d.description].filter(Boolean).join('\n\n')
          }
          return {
            input: lines[i],
            result: resultText,
            error: r.error
          }
        })
      } else {
        alert(res.data.message || '批量生成失败')
      }
    } else {
      const res = await batchAPI.complianceScan({
        items: lines.map(text => ({ text })),
        check_extreme_words: batchCheckExtreme.value,
        check_copyright: batchCheckCopyright.value,
        check_forbidden_words: batchCheckForbidden.value
      })
      if (res.data.success) {
        batchResults.value = (res.data.data || []).map((r, i) => {
          const d = r.data || {}
          return {
            input: lines[i],
            pass: d.pass,
            issues: d.issues || [],
            error: r.error
          }
        })
      } else {
        alert(res.data.message || '批量合规扫描失败')
      }
    }
  } catch (e) {
    console.error('批量处理失败', e)
    alert('批量处理失败：' + (e.message || '网络错误'))
  } finally {
    batchLoading.value = false
    batchProgress.value = batchTotal.value
  }
}

function exportBatchCSV() {
  const rows = batchResults.value.map((item, idx) => {
    if (batchMode.value === 'copywriter') {
      return [`#${idx + 1}`, item.input.replace(/"/g, '""'), (item.result || '').replace(/"/g, '""'), item.error || '']
    } else {
      return [`#${idx + 1}`, item.input.replace(/"/g, '""'), item.pass ? '通过' : '未通过', (item.issues || []).join('; ').replace(/"/g, '""')]
    }
  })
  const headers = batchMode.value === 'copywriter'
    ? ['序号', '输入', '生成结果', '错误']
    : ['序号', '输入', '合规结果', '问题']
  const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `batch-${batchMode.value}-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadHistory()
  loadShops()
  refreshStyleMemory()
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

async function publishToShop() {
  if (!selectedShopId.value) {
    ElMessage.warning('请先选择店铺')
    return
  }
  if (!publishSku.value.trim()) {
    ElMessage.warning('请输入 SKU')
    return
  }
  const shop = shopList.value.find(s => s.id === selectedShopId.value)
  if (!shop) {
    ElMessage.warning('店铺不存在')
    return
  }
  const f = currentFinal.value
  if (!f) {
    ElMessage.warning('当前无可上架文本')
    return
  }
  publishLoading.value = true
  try {
    const payload = {
      sku: publishSku.value.trim(),
      title: f.title,
      bullet_points: f.bullet_points,
      description: f.description,
      price: 0,
      stock: 0,
      product_type: 'PRODUCT'
    }
    const res = await platformAPI.publishListing(selectedShopId.value, payload)
    if (res.data.success) {
      ElMessage.success(`已提交到 ${shop.name}: ${res.data.data?.message || '成功'}`)
    } else {
      ElMessage.error('上架失败：' + (res.data.message || '未知错误'))
    }
  } catch (e) {
    ElMessage.error('上架失败：' + (e.response?.data?.message || e.message))
  } finally {
    publishLoading.value = false
  }
}

const listingLangs = [
  { value: 'en', label: '英语 EN' },
  { value: 'es', label: '西班牙语 ES' },
  { value: 'de', label: '德语 DE' },
  { value: 'zh', label: '中文 ZH' }
]

const pipelineSteps = [
  '① 爬虫抓取商品页（标题 / 规格 / 详情 / 优势）',
  '② 大模型提炼核心卖点 / 关键参数 / 适用场景',
  '③ 生成英 / 西 / 德 / 中 四语种亚马逊 Listing',
  '④ 多语种文案自动合规风控校验',
  '⑤ 拼装最终可上架文本',
  '⑥ 汇总输出可一键复制结果'
]

const currentListing = computed(() => {
  const r = linkResult.value
  if (!r || !r.listings) return null
  return r.listings[activeListingLang.value] || null
})

const currentCompliance = computed(() => {
  const r = linkResult.value
  if (!r || !r.compliance) return null
  return r.compliance[activeComplianceLang.value] || null
})

const currentFinal = computed(() => {
  const r = linkResult.value
  if (!r || !r.final_listings) return null
  return r.final_listings[activeFinalLang.value] || null
})

function validateLink() {
  const v = (linkUrl.value || '').trim()
  const ok = /1688\.com/i.test(v) && v.length >= 10
  isValidLink.value = ok
  if (!v) {
    linkError.value = ''
  } else if (!ok) {
    linkError.value = '请输入有效的 1688 商品详情页链接（需包含 1688.com）'
  } else {
    linkError.value = ''
  }
}

async function generateFromLink() {
  validateLink()
  if (!isValidLink.value) {
    ElMessage.warning(linkError.value || '请输入有效的 1688 链接')
    return
  }

  const res = await copywriterStore.generateFromLink(linkUrl.value.trim())
  if (res.success) {
    pushHistory({
      mode: 'link',
      platform: '1688',
      language: '',
      input_text: linkUrl.value.trim(),
      result: res.data.data
    })
    // 记录品类与风格记忆（从抓取标题中提取品类）
    const scrapedTitle = res.data.data?.raw_scraped?.title || linkUrl.value.trim()
    styleMemory.record({
      productDesc: scrapedTitle,
      platform: '1688',
      language: 'en',
      result: res.data.data?.listings?.en || res.data.data,
      mode: 'link',
    })
    refreshStyleMemory()
    ElMessage.success('上架文案已生成')
  } else {
    ElMessage.error(res.error || '生成失败')
  }
}

// ============ 复制功能 ============
async function copyText(text, successMsg = '已复制到剪贴板') {
  if (!text) {
    ElMessage.warning('没有可复制的内容')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(successMsg)
  } catch (e) {
    console.error(e)
    ElMessage.error('复制失败，请手动选择复制')
  }
}

function copyRaw() {
  const r = linkResult.value.raw_scraped
  let text = `商品标题：${r.title || ''}\n\n`
  if (r.specs && r.specs.length) {
    text += '规格参数：\n' + r.specs.map(s => `- ${s.key}：${s.value}`).join('\n') + '\n\n'
  }
  if (r.advantages && r.advantages.length) {
    text += '产品优势：\n' + r.advantages.map(a => `- ${a}`).join('\n') + '\n\n'
  }
  text += `详情介绍：\n${r.description_text || ''}`
  copyText(text, '已复制原始抓取内容')
}

function copyRefined() {
  const r = linkResult.value.refined_info
  if (!r) {
    ElMessage.warning('无提炼信息可复制')
    return
  }
  let text = ''
  if (r.product_name) text += `产品名称：${r.product_name}\n\n`
  if (r.core_selling_points?.length) text += '核心卖点：\n' + r.core_selling_points.map((p, i) => `${i + 1}. ${p}`).join('\n') + '\n\n'
  if (r.key_parameters?.length) text += '关键参数：\n' + r.key_parameters.map(p => `- ${p}`).join('\n') + '\n\n'
  if (r.applicable_scenarios?.length) text += '适用场景：' + r.applicable_scenarios.join('、') + '\n\n'
  if (r.clean_description) text += `产品简介：${r.clean_description}`
  copyText(text, '已复制 AI 提炼信息')
}

function copyListing(lang) {
  const l = linkResult.value.listings[lang]
  if (!l || l.error) {
    ElMessage.warning('该语种文案生成失败，无可复制内容')
    return
  }
  const label = listingLangs.find(x => x.value === lang)?.label || lang
  const text = `【${label} Listing】\n标题：${l.title}\n\n卖点：\n${l.bullet_points.map((p, i) => `${i + 1}. ${p}`).join('\n')}\n\n详情：${l.description}`
  copyText(text, `已复制${label} Listing`)
}

function copyCompliance(lang) {
  const c = linkResult.value.compliance[lang]
  if (!c || c.skipped || c.error) {
    ElMessage.warning('该语种风控报告不可用')
    return
  }
  const label = listingLangs.find(x => x.value === lang)?.label || lang
  let text = `【${label} 风控报告】风险等级：${c.overall_risk}\n`
  if (c.extreme_words?.length) text += '\n极限词：\n' + c.extreme_words.map(w => `- ${w.word}（建议：${w.suggestion}）`).join('\n')
  if (c.copyright_issues?.length) text += '\n版权风险：\n' + c.copyright_issues.map(w => `- ${w.description}（${w.risk_level}）`).join('\n')
  if (c.forbidden_words?.length) text += '\n违禁词：\n' + c.forbidden_words.map(w => `- ${w.word}（${w.category}）`).join('\n')
  if (c.suggestions?.length) text += '\n优化建议：\n' + c.suggestions.map(s => `- ${s}`).join('\n')
  copyText(text, `已复制${label} 风控报告`)
}

function copyFinal(lang) {
  const f = linkResult.value.final_listings[lang]
  if (!f || !f.text) {
    ElMessage.warning('该语种无可用可上架文本')
    return
  }
  const label = listingLangs.find(x => x.value === lang)?.label || lang
  copyText(f.text, `已复制${label}可上架文本`)
}

async function copyAllFinal() {
  const r = linkResult.value
  let text = ''
  for (const lang of ['en', 'es', 'de', 'zh']) {
    const f = r.final_listings[lang]
    const label = listingLangs.find(x => x.value === lang)?.label || lang
    text += `========== ${label} 可上架文本 ==========\n`
    if (f && f.text) {
      text += (f.ready ? '[状态] 可直接上架\n' : '[状态] 需人工复核\n') + f.text + '\n'
    } else {
      text += '（生成失败）\n'
    }
    text += '\n'
  }
  copyText(text, '已复制全部可上架文本')
}

async function copyAllLink() {
  const r = linkResult.value
  let text = '========== 原始抓取内容 ==========\n'
  text += `商品标题：${r.raw_scraped.title || ''}\n`
  if (r.raw_scraped.specs?.length) text += '规格参数：\n' + r.raw_scraped.specs.map(s => `- ${s.key}：${s.value}`).join('\n') + '\n'
  if (r.raw_scraped.advantages?.length) text += '产品优势：\n' + r.raw_scraped.advantages.map(a => `- ${a}`).join('\n') + '\n'
  text += `详情介绍：\n${r.raw_scraped.description_text || ''}\n`

  if (r.refined_info) {
    text += '\n========== AI 提炼信息 ==========\n'
    if (r.refined_info.product_name) text += `产品名称：${r.refined_info.product_name}\n`
    if (r.refined_info.core_selling_points?.length) text += '核心卖点：\n' + r.refined_info.core_selling_points.map((p, i) => `${i + 1}. ${p}`).join('\n') + '\n'
    if (r.refined_info.key_parameters?.length) text += '关键参数：\n' + r.refined_info.key_parameters.map(p => `- ${p}`).join('\n') + '\n'
    if (r.refined_info.applicable_scenarios?.length) text += '适用场景：' + r.refined_info.applicable_scenarios.join('、') + '\n'
    if (r.refined_info.clean_description) text += `产品简介：${r.refined_info.clean_description}\n`
  }

  for (const lang of ['en', 'es', 'de', 'zh']) {
    const l = r.listings[lang]
    const label = listingLangs.find(x => x.value === lang)?.label || lang
    text += `\n========== ${label} Listing ==========\n`
    if (l && !l.error) {
      text += `标题：${l.title}\n卖点：\n${l.bullet_points.map((p, i) => `${i + 1}. ${p}`).join('\n')}\n详情：${l.description}\n`
    } else {
      text += '（生成失败）\n'
    }
    const c = r.compliance[lang]
    text += `\n--- ${label} 风控报告 ---\n`
    if (c && !c.skipped && !c.error) {
      text += `风险等级：${c.overall_risk}\n`
      if (c.extreme_words?.length) text += '极限词：' + c.extreme_words.map(w => `${w.word}(建议:${w.suggestion})`).join('；') + '\n'
      if (c.copyright_issues?.length) text += '版权：' + c.copyright_issues.map(w => w.description).join('；') + '\n'
      if (c.forbidden_words?.length) text += '违禁词：' + c.forbidden_words.map(w => w.word).join('；') + '\n'
      if (c.suggestions?.length) text += '建议：' + c.suggestions.join('；') + '\n'
      } else if (c && c.skipped) {
        text += '（跳过）\n'
      }
  }

  // 最终可上架文本
  for (const lang of ['en', 'es', 'de', 'zh']) {
    const f = r.final_listings?.[lang]
    const label = listingLangs.find(x => x.value === lang)?.label || lang
    text += `\n========== ${label} 最终可上架文本 ==========\n`
    if (f && f.text) {
      text += (f.ready ? '[可直接上架]\n' : '[需人工复核]\n') + f.text + '\n'
    } else {
      text += '（生成失败）\n'
    }
  }

  copyText(text, '已复制全部结果')
}

// ============ 手动输入模式方法（原有） ============
async function generateCopy() {
  if (!form.product_desc.trim()) {
    ElMessage.warning('请输入产品描述')
    return
  }

  const res = await copywriterStore.generateCopy(form)
  if (res.success) {
    pushHistory({
      mode: 'manual',
      platform: form.platform,
      language: form.target_language,
      input_text: form.product_desc,
      result: res.data.data
    })
    // 记录品类与风格记忆
    styleMemory.record({
      productDesc: form.product_desc,
      platform: form.platform,
      language: form.target_language,
      result: res.data.data,
      mode: 'manual',
    })
    refreshStyleMemory()
    ElMessage.success('文案生成成功')
  } else {
    ElMessage.error(res.error || '文案生成失败')
  }
}

async function translateCopy() {
  if (!result.value) return

  const otherLanguages = languages.filter(l => l.value !== form.target_language)
  if (otherLanguages.length === 0) return

  const targetLang = otherLanguages[0].value
  form.target_language = targetLang

  const res = await copywriterStore.translateCopy({
    title: result.value.title,
    bullet_points: result.value.bullet_points,
    description: result.value.description,
    target_language: targetLang
  })
  if (res.success) {
    ElMessage.success('翻译成功')
  } else {
    ElMessage.error(res.error || '翻译失败')
  }
}

async function copyAll() {
  if (!result.value) return

  const text = `标题：${result.value.title}\n\n卖点：\n${result.value.bullet_points.map((p, i) => `${i + 1}. ${p}`).join('\n')}\n\n详情：${result.value.description}`

  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    console.error(error)
    ElMessage.error('复制失败')
  }
}

// 手动触发合规扫描（默认生成时不跑，节省 30-60 秒）
async function scanComplianceNow() {
  if (!result.value || complianceScanning.value) return
  complianceScanning.value = true
  try {
    const text = `标题：${result.value.title}\n卖点：${(result.value.bullet_points || []).join('；')}\n描述：${result.value.description}`
    const res = await complianceAPI.scan({
      content: text,
      check_extreme_words: true,
      check_copyright: true,
      check_forbidden_words: true
    })
    const scan = res.data?.data || res.data || {}
    // 合并到 result，触发模板更新
    copywriterStore.updateManualResult({
      ...result.value,
      compliance_scan: scan,
      compliance: {
        original_clean: scan.clean !== false,
        rewritten: false,
        notes: scan.suggestions || [],
        risk: scan.overall_risk || 'low'
      }
    })
    if (scan.clean) {
      ElMessage.success('合规扫描完成，未发现风险')
    } else {
      ElMessage.warning(`合规扫描完成，风险等级：${scan.overall_risk || 'medium'}，请查看下方详情`)
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('合规扫描失败：' + (e.response?.data?.message || e.message))
  } finally {
    complianceScanning.value = false
  }
}
</script>
