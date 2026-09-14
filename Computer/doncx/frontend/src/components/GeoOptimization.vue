<template>
  <div class="max-w-7xl mx-auto">
    <!-- 标题区 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <span class="w-11 h-11 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center">
            <Radar class="w-6 h-6 text-white" />
          </span>
          GEO 优化
        </h2>
        <p class="text-sm text-slate-500 mt-2">生成式引擎优化 · 让品牌更容易被 AI 看见、理解并主动推荐</p>
      </div>
    </div>

    <!-- 功能切换 -->
    <div class="flex flex-wrap gap-2 mb-6 bg-slate-100 p-1.5 rounded-xl w-fit">
      <button @click="activeTab = 'visibility'"
        class="px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all"
        :class="activeTab === 'visibility' ? 'bg-white text-violet-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'">
        <Radar class="w-4 h-4" /> AI 可见度检测
      </button>
      <button @click="activeTab = 'content'"
        class="px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all"
        :class="activeTab === 'content' ? 'bg-white text-violet-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'">
        <Sparkles class="w-4 h-4" /> AI 友好内容
      </button>
      <button @click="activeTab = 'prompts'"
        class="px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all"
        :class="activeTab === 'prompts' ? 'bg-white text-violet-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'">
        <Lightbulb class="w-4 h-4" /> AI 提问挖掘
      </button>
    </div>

    <!-- ==================== Tab 1: AI 可见度检测（多品牌对比） ==================== -->
    <div v-show="activeTab === 'visibility'" class="space-y-6">
      <div class="card p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-slate-900">多品牌横向可见度检测</h3>
          <span class="text-xs text-slate-400">主品牌 vs 最多 4 个竞品</span>
        </div>

        <!-- 主品牌 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs text-slate-500 mb-1">主品牌 / 店铺 *</label>
            <input v-model="vis.brand" class="input-field w-full px-4 py-3 text-sm" placeholder="如：Anker" />
          </div>
          <div>
            <label class="block text-xs text-slate-500 mb-1">目标关键词 / 类目 *</label>
            <input v-model="vis.keyword" class="input-field w-full px-4 py-3 text-sm" placeholder="如：无线蓝牙耳机" @keyup.enter="runVisibility" />
          </div>
          <div>
            <label class="block text-xs text-slate-500 mb-1">面向平台 / 市场</label>
            <select v-model="vis.platform" class="input-field w-full px-4 py-3 text-sm">
              <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
        </div>

        <!-- 竞品（动态增删） -->
        <div class="mt-5">
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs text-slate-500">竞品品牌（可选填，最多 4 个，留空即跳过）</label>
            <button v-if="vis.competitors.length < 4" @click="addCompetitor"
              class="text-xs text-violet-600 hover:text-violet-700 flex items-center gap-1">
              <Plus class="w-3.5 h-3.5" /> 添加竞品
            </button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div v-for="(c, i) in vis.competitors" :key="i" class="flex items-center gap-2">
              <input v-model="vis.competitors[i]" class="input-field flex-1 px-3 py-2 text-sm" :placeholder="`竞品 ${i + 1}，如 Soundcore`" />
              <button @click="removeCompetitor(i)" class="text-slate-400 hover:text-red-500 p-1">
                <X class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <button @click="runVisibility" :disabled="visLoading || !vis.brand || !vis.keyword"
          class="mt-5 w-full py-3 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm"
          :class="(visLoading || !vis.brand || !vis.keyword) ? 'bg-slate-400 cursor-not-allowed text-white' : 'btn-primary'">
          <span v-if="visLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          {{ visLoading ? 'AI 正在多维度评估（结构化）...' : '开始多品牌对比检测' }}
        </button>
      </div>

      <!-- 结果区 -->
      <div v-if="visResult" class="space-y-6">
        <!-- 关键洞察 -->
        <div v-if="visResult.key_insight" class="card p-5 bg-gradient-to-r from-violet-50 to-indigo-50 border-violet-100">
          <div class="flex items-start gap-3">
            <span class="w-8 h-8 rounded-lg bg-violet-600 text-white flex items-center justify-center flex-shrink-0">
              <Zap class="w-4 h-4" />
            </span>
            <div>
              <p class="text-xs font-bold text-violet-700 mb-1">关键洞察 · 最该先做的事</p>
              <p class="text-sm text-slate-700 leading-relaxed">{{ visResult.key_insight }}</p>
              <p v-if="visResult.comparative_summary" class="text-xs text-slate-500 mt-2">{{ visResult.comparative_summary }}</p>
            </div>
          </div>
        </div>

        <!-- 多品牌对比表 + 柱状图 -->
        <div class="card p-6">
          <h3 class="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2"><BarChart3 class="w-5 h-5 text-violet-600" />多品牌可见度对比</h3>
          <!-- 柱状图（纯 SVG） -->
          <div class="mb-6">
            <div class="flex items-end gap-3 h-44 px-2">
              <div v-for="b in visResult.brands" :key="b.name" class="flex-1 flex flex-col items-center justify-end group">
                <div class="w-full max-w-[80px] rounded-t-lg transition-all relative"
                  :class="b.name === visResult.main_brand ? 'bg-gradient-to-t from-violet-600 to-indigo-500' : 'bg-gradient-to-t from-slate-400 to-slate-300'"
                  :style="{ height: `${Math.max(8, (b.visibility_score / 100) * 160)}px` }">
                  <span class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-bold text-slate-700">{{ b.visibility_score }}</span>
                </div>
                <p class="text-xs mt-2 font-medium text-slate-700 text-center truncate w-full" :title="b.name">{{ b.name }}</p>
                <span v-if="b.name === visResult.main_brand" class="text-[10px] text-violet-600 font-bold">主品牌</span>
              </div>
            </div>
          </div>
          <!-- 对比表 -->
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-xs text-slate-500 border-b border-slate-200">
                  <th class="text-left py-2 pr-4">品牌</th>
                  <th class="text-center py-2 px-2">综合评分</th>
                  <th class="text-center py-2 px-2">推荐位次</th>
                  <th class="text-center py-2 px-2">是否被推荐</th>
                  <th class="text-center py-2 px-2">情感倾向</th>
                  <th class="text-center py-2 px-2">提及强度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in visResult.brands" :key="b.name"
                  class="border-b border-slate-100 last:border-0"
                  :class="b.name === visResult.main_brand ? 'bg-violet-50/40' : ''">
                  <td class="py-3 pr-4">
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-semibold text-slate-800">{{ b.name }}</span>
                      <span v-if="b.name === visResult.main_brand" class="text-[10px] px-1.5 py-0.5 rounded bg-violet-100 text-violet-700 font-bold">我的</span>
                    </div>
                  </td>
                  <td class="text-center py-3 px-2">
                    <span class="text-base font-bold" :class="b.visibility_score >= 70 ? 'text-emerald-600' : b.visibility_score >= 40 ? 'text-amber-600' : 'text-red-500'">
                      {{ b.visibility_score }}
                    </span>
                  </td>
                  <td class="text-center py-3 px-2 text-slate-600">{{ b.mention_rank > 0 ? `#${b.mention_rank}` : '—' }}</td>
                  <td class="text-center py-3 px-2">
                    <CheckCircle2 v-if="b.recommended" class="w-4 h-4 text-emerald-500 inline" />
                    <XCircle v-else class="w-4 h-4 text-slate-300 inline" />
                  </td>
                  <td class="text-center py-3 px-2">
                    <span class="text-xs px-2 py-0.5 rounded-full" :class="sentimentClass(avgSentiment(b))">
                      {{ sentimentText(avgSentiment(b)) }}
                    </span>
                  </td>
                  <td class="text-center py-3 px-2">
                    <div class="flex items-center gap-0.5 justify-center">
                      <span v-for="n in 4" :key="n" class="w-1.5 h-3 rounded-sm"
                        :class="n <= maxMention(b) ? (b.name === visResult.main_brand ? 'bg-violet-500' : 'bg-slate-400') : 'bg-slate-100'"></span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 各引擎横向对比 -->
        <div class="card p-6">
          <h3 class="text-lg font-bold text-slate-900 mb-4">各 AI 引擎下的对比</h3>
          <div class="space-y-4">
            <div v-for="eng in engineNames" :key="eng" class="rounded-xl border border-slate-200 p-4">
              <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-bold text-slate-800">{{ eng }}</span>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div v-for="b in visResult.brands" :key="b.name + eng" class="rounded-lg p-3 border"
                  :class="engineMentioned(b, eng) ? 'border-emerald-200 bg-emerald-50/40' : 'border-slate-100 bg-slate-50'">
                  <div class="flex items-center justify-between mb-1.5">
                    <span class="text-xs font-semibold" :class="b.name === visResult.main_brand ? 'text-violet-700' : 'text-slate-700'">{{ b.name }}</span>
                    <CheckCircle2 v-if="engineMentioned(b, eng)" class="w-3.5 h-3.5 text-emerald-500" />
                    <XCircle v-else class="w-3.5 h-3.5 text-slate-300" />
                  </div>
                  <div class="flex items-center gap-2 mb-1">
                    <span v-if="engineRank(b, eng) > 0" class="text-[10px] px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-600">位次 #{{ engineRank(b, eng) }}</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="sentimentClass(engineSentiment(b, eng))">
                      {{ sentimentText(engineSentiment(b, eng)) }}
                    </span>
                  </div>
                  <p class="text-[11px] text-slate-500 leading-snug">{{ engineNote(b, eng) }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 主品牌的优势 / 短板 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="card p-6">
            <h4 class="text-sm font-bold text-emerald-700 mb-3 flex items-center gap-2"><TrendingUp class="w-4 h-4" />主品牌已被 AI 认可</h4>
            <ul class="space-y-2">
              <li v-for="(s, i) in mainBrand.strengths_in_ai" :key="i" class="text-xs text-slate-600 flex gap-2"><span class="text-emerald-500 flex-shrink-0">+</span>{{ s }}</li>
              <li v-if="!mainBrand.strengths_in_ai?.length" class="text-xs text-slate-400">尚无明显优势</li>
            </ul>
          </div>
          <div class="card p-6">
            <h4 class="text-sm font-bold text-red-600 mb-3 flex items-center gap-2"><AlertCircle class="w-4 h-4" />主品牌的曝光短板</h4>
            <ul class="space-y-2">
              <li v-for="(g, i) in mainBrand.gaps" :key="i" class="text-xs text-slate-600 flex gap-2"><span class="text-red-500 flex-shrink-0">-</span>{{ g }}</li>
              <li v-if="!mainBrand.gaps?.length" class="text-xs text-slate-400">暂无明显短板</li>
            </ul>
          </div>
        </div>

        <!-- 优化建议（按优先级排序） -->
        <div class="card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2"><Target class="w-5 h-5 text-violet-600" />GEO 优化建议</h3>
            <div class="flex items-center gap-3 text-xs text-slate-500">
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500"></span>高优先</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-500"></span>中优先</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-slate-400"></span>低优先</span>
            </div>
          </div>
          <div class="space-y-3">
            <div v-for="(s, i) in visResult.suggestions" :key="i"
              class="rounded-xl border p-4 transition-all hover:shadow-sm"
              :class="suggestionBorderClass(s.priority)">
              <div class="flex items-start gap-3">
                <span class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold text-white"
                  :class="suggestionBadgeClass(s.priority)">{{ i + 1 }}</span>
                <div class="flex-1 min-w-0">
                  <div class="flex flex-wrap items-center gap-2 mb-1.5">
                    <span class="text-[10px] font-bold px-1.5 py-0.5 rounded uppercase"
                      :class="suggestionTagClass(s.priority)">{{ priorityLabel(s.priority) }}</span>
                    <span v-if="s.expected_lift && s.expected_lift !== '—'" class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-100 flex items-center gap-1">
                      <TrendingUp class="w-3 h-3" /> 预估 {{ s.expected_lift }}
                    </span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-50 text-slate-500 border border-slate-200 flex items-center gap-1">
                      难度 {{ '★'.repeat(s.difficulty) }}{{ '☆'.repeat(3 - s.difficulty) }}
                    </span>
                  </div>
                  <p class="text-sm text-slate-700 leading-relaxed">{{ s.text }}</p>
                </div>
              </div>
            </div>
            <p v-if="!visResult.suggestions.length" class="text-sm text-slate-400 text-center py-4">暂无建议</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Tab 2: AI 友好内容 ==================== -->
    <div v-show="activeTab === 'content'" class="space-y-6">
      <div class="card p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-4">生成易被 AI 引用的内容</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-slate-500 mb-1">品牌（可选）</label>
            <input v-model="cnt.brand" class="input-field w-full px-4 py-3 text-sm" placeholder="如：Anker" />
          </div>
          <div>
            <label class="block text-xs text-slate-500 mb-1">目标关键词 / 类目（可选）</label>
            <input v-model="cnt.keyword" class="input-field w-full px-4 py-3 text-sm" placeholder="如：无线蓝牙耳机" />
          </div>
          <div class="md:col-span-2">
            <label class="block text-xs text-slate-500 mb-1">商品 / 服务描述 *</label>
            <textarea v-model="cnt.product" rows="3" class="input-field w-full px-4 py-3 text-sm" placeholder="简要描述商品、卖点、目标人群、场景等..."></textarea>
          </div>
          <div>
            <label class="block text-xs text-slate-500 mb-1">输出语言</label>
            <select v-model="cnt.language" class="input-field w-full px-4 py-3 text-sm">
              <option v-for="l in languages" :key="l" :value="l">{{ l }}</option>
            </select>
          </div>
        </div>
        <button @click="runContent" :disabled="cntLoading || !cnt.product"
          class="mt-4 w-full py-3 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm"
          :class="(cntLoading || !cnt.product) ? 'bg-slate-400 cursor-not-allowed text-white' : 'btn-primary'">
          <span v-if="cntLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          {{ cntLoading ? 'AI 正在生成...' : '生成 AI 友好内容' }}
        </button>
      </div>

      <div v-if="cntResult" class="space-y-6">
        <div class="card p-6">
          <h3 class="text-lg font-bold text-slate-900 mb-3">AI 友好简介</h3>
          <p class="text-sm text-slate-700 leading-relaxed bg-violet-50 rounded-xl p-4">{{ cntResult.ai_friendly_intro }}</p>
          <p v-if="cntResult.structured_summary" class="text-sm text-slate-600 mt-3">{{ cntResult.structured_summary }}</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="card p-6">
            <h4 class="text-sm font-bold text-slate-900 mb-3">高频问答（FAQ）</h4>
            <div class="space-y-3">
              <div v-for="(f, i) in cntResult.faq" :key="i" class="border-b border-slate-100 last:border-0 pb-3 last:pb-0">
                <p class="text-xs font-semibold text-slate-800 mb-1">Q：{{ f.q }}</p>
                <p class="text-xs text-slate-500">A：{{ f.a }}</p>
              </div>
            </div>
          </div>
          <div class="card p-6">
            <h4 class="text-sm font-bold text-slate-900 mb-3">权威引用要点</h4>
            <ul class="space-y-2 mb-4">
              <li v-for="(a, i) in cntResult.authority_points" :key="i" class="text-xs text-slate-600 flex gap-2"><span class="text-emerald-500">✓</span>{{ a }}</li>
            </ul>
            <h4 class="text-sm font-bold text-slate-900 mb-3">差异化卖点</h4>
            <ul class="space-y-2">
              <li v-for="(d, i) in cntResult.differentiators" :key="i" class="text-xs text-slate-600 flex gap-2"><span class="text-violet-500">★</span>{{ d }}</li>
            </ul>
          </div>
        </div>

        <div class="card p-6">
          <div class="flex flex-wrap items-center gap-2 mb-3">
            <span class="text-sm font-bold text-slate-900">建议覆盖关键词</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <span v-for="(k, i) in cntResult.target_keywords" :key="i" class="text-xs px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">{{ k }}</span>
          </div>
          <p v-if="cntResult.schema_hint" class="text-xs text-slate-500 mt-4 bg-slate-50 rounded-lg p-3">
            结构化数据建议：{{ cntResult.schema_hint }}
          </p>
        </div>
      </div>
    </div>

    <!-- ==================== Tab 3: AI 提问挖掘 ==================== -->
    <div v-show="activeTab === 'prompts'" class="space-y-6">
      <div class="card p-6">
        <h3 class="text-lg font-bold text-slate-900 mb-4">挖掘买家的 AI 提问</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs text-slate-500 mb-1">商品类目 / 关键词 *</label>
            <input v-model="prm.keyword" class="input-field w-full px-4 py-3 text-sm" placeholder="如：无线蓝牙耳机" @keyup.enter="runPrompts" />
          </div>
          <div>
            <label class="block text-xs text-slate-500 mb-1">面向平台</label>
            <select v-model="prm.platform" class="input-field w-full px-4 py-3 text-sm">
              <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-slate-500 mb-1">目标市场</label>
            <select v-model="prm.market" class="input-field w-full px-4 py-3 text-sm">
              <option v-for="m in markets" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
        </div>
        <button @click="runPrompts" :disabled="prmLoading || !prm.keyword"
          class="mt-4 w-full py-3 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm"
          :class="(prmLoading || !prm.keyword) ? 'bg-slate-400 cursor-not-allowed text-white' : 'btn-primary'">
          <span v-if="prmLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          {{ prmLoading ? 'AI 正在挖掘...' : '开始挖掘' }}
        </button>
      </div>

      <div v-if="prmResult" class="space-y-6">
        <div class="card p-6">
          <h3 class="text-lg font-bold text-slate-900 mb-4">买家可能向 AI 提的问题</h3>
          <div class="space-y-3">
            <div v-for="(q, i) in prmResult.questions" :key="i" class="rounded-xl border border-slate-200 p-4 hover:border-violet-300 transition-colors">
              <div class="flex items-start justify-between gap-3">
                <p class="text-sm font-medium text-slate-800 flex-1">{{ q.question }}</p>
                <span class="text-xs px-2 py-0.5 rounded-full flex-shrink-0" :class="priorityClass(q.priority)">{{ priorityText(q.priority) }}</span>
              </div>
              <div class="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-500">
                <span>意图：{{ q.intent }}</span>
                <span v-if="q.difficulty">竞争难度：{{ q.difficulty }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="card p-6">
            <h4 class="text-sm font-bold text-slate-900 mb-3">问题主题聚类</h4>
            <div class="space-y-3">
              <div v-for="(c, i) in prmResult.clusters" :key="i">
                <p class="text-xs font-semibold text-slate-700 mb-1">{{ c.theme }}</p>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="(k, j) in c.keywords" :key="j" class="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{{ k }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="card p-6">
            <h4 class="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2"><Target class="w-4 h-4 text-violet-600" />优先抢占方向</h4>
            <ul class="space-y-2 mb-4">
              <li v-for="(t, i) in prmResult.recommended_targets" :key="i" class="text-xs text-slate-600 flex gap-2"><span class="text-violet-500">➤</span>{{ t }}</li>
            </ul>
            <h4 class="text-sm font-bold text-slate-900 mb-3">建议内容角度</h4>
            <ul class="space-y-2">
              <li v-for="(a, i) in prmResult.content_angles" :key="i" class="text-xs text-slate-600 flex gap-2"><span class="text-indigo-500">•</span>{{ a }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <div class="card p-6 mt-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2"><History class="w-5 h-5 text-violet-600" />检测历史</h3>
        <button v-if="history.length" @click="clearHistory" class="text-xs text-slate-400 hover:text-red-500 flex items-center gap-1">
          <Trash2 class="w-3.5 h-3.5" />清空
        </button>
      </div>
      <div v-if="!history.length" class="text-sm text-slate-400 py-4 text-center">暂无检测记录</div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="(h, i) in history" :key="i" @click="restoreItem(h)" class="bg-slate-50 rounded-lg p-4 cursor-pointer hover:bg-violet-50 transition-colors">
          <div class="flex items-center justify-between mb-2">
            <p class="text-sm font-semibold text-slate-800 truncate flex-1" :title="h.summary">{{ h.summary }}</p>
            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-violet-100 text-violet-700">{{ h.score }}</span>
          </div>
          <p class="text-xs text-slate-500 line-clamp-2 mb-2">{{ h.keyword }}</p>
          <p class="text-xs text-slate-400">{{ h.created_at }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Radar, Sparkles, Lightbulb, Target, TrendingUp,
  CheckCircle2, XCircle, AlertCircle, History, Trash2,
  Zap, Plus, X, BarChart3
} from 'lucide-vue-next'

const activeTab = ref('visibility')

const platforms = ['Amazon', 'eBay', 'Temu', 'Shopee', 'TikTok Shop', '独立站']
const languages = ['中文', 'English', '多语言']
const markets = ['北美', '欧洲', '东南亚', '中东', '日本', '拉美']
const engineNames = ['ChatGPT', '豆包', 'DeepSeek', 'Perplexity']

// ---------- Tab1: 可见度检测（多品牌） ----------
const vis = ref({
  brand: '',
  keyword: '',
  platform: 'Amazon',
  competitors: ['', '', '']  // 默认 3 个空位
})
const visLoading = ref(false)
const visResult = ref(null)

const mainBrand = computed(() => {
  if (!visResult.value || !visResult.value.brands) return {}
  return visResult.value.brands.find(b => b.name === visResult.value.main_brand) || visResult.value.brands[0] || {}
})

function addCompetitor() {
  if (vis.value.competitors.length < 4) vis.value.competitors.push('')
}
function removeCompetitor(i) {
  vis.value.competitors.splice(i, 1)
}

function engineMentioned(b, eng) {
  const e = (b.engines || []).find(x => x.engine === eng)
  return !!(e && e.mention_score > 0)
}
function engineRank(b, eng) {
  const e = (b.engines || []).find(x => x.engine === eng)
  return e ? e.rank : 0
}
function engineSentiment(b, eng) {
  const e = (b.engines || []).find(x => x.engine === eng)
  return e ? e.sentiment : 'neutral'
}
function engineNote(b, eng) {
  const e = (b.engines || []).find(x => x.engine === eng)
  return e ? e.note : '—'
}
function maxMention(b) {
  return Math.max(0, ...(b.engines || []).map(e => e.mention_score || 0))
}
function avgSentiment(b) {
  const es = (b.engines || []).map(e => e.sentiment)
  if (es.some(s => s === 'positive')) return 'positive'
  if (es.every(s => s === 'negative')) return 'negative'
  return 'neutral'
}

function sentimentText(s) {
  return { positive: '正面', neutral: '中性', negative: '负面' }[s] || '中性'
}
function sentimentClass(s) {
  return {
    positive: 'bg-emerald-50 text-emerald-600 border border-emerald-100',
    negative: 'bg-red-50 text-red-600 border border-red-100'
  }[s] || 'bg-slate-50 text-slate-500 border border-slate-200'
}

function priorityLabel(p) {
  return { high: '高优先', medium: '中优先', low: '低优先' }[p] || '中优先'
}
function priorityClass(p) {
  return {
    high: 'bg-red-50 text-red-600 border border-red-100',
    low: 'bg-slate-50 text-slate-500 border border-slate-200'
  }[p] || 'bg-amber-50 text-amber-600 border border-amber-100'
}
function suggestionBorderClass(p) {
  return {
    high: 'border-red-200 bg-red-50/30 hover:border-red-300',
    low: 'border-slate-200 bg-slate-50/30 hover:border-slate-300'
  }[p] || 'border-amber-200 bg-amber-50/30 hover:border-amber-300'
}
function suggestionBadgeClass(p) {
  return { high: 'bg-red-500', low: 'bg-slate-400' }[p] || 'bg-amber-500'
}
function suggestionTagClass(p) {
  return {
    high: 'bg-red-100 text-red-700',
    low: 'bg-slate-100 text-slate-600'
  }[p] || 'bg-amber-100 text-amber-700'
}

async function runVisibility() {
  if (!vis.value.brand || !vis.value.keyword) return
  visLoading.value = true
  visResult.value = null
  try {
    // 过滤空竞品
    const competitors = (vis.value.competitors || []).map(c => (c || '').trim()).filter(Boolean)
    const payload = {
      brand: vis.value.brand,
      keyword: vis.value.keyword,
      platform: vis.value.platform,
      competitors
    }
    const r = await axios.post('/api/geo/visibility', payload, { timeout: 300000 })
    if (r.data.success) {
      visResult.value = r.data.data
      // 保存到历史（取最高评分作为摘要）
      const brands = r.data.data.brands || []
      const mainB = brands.find(b => b.name === r.data.data.main_brand) || brands[0]
      const competitorsList = brands.filter(b => b.name !== r.data.data.main_brand).map(b => b.name).join(' / ')
      const summary = competitorsList ? `${r.data.data.main_brand} vs ${competitorsList}` : r.data.data.main_brand
      history.value.unshift({
        summary,
        score: mainB ? mainB.visibility_score : 0,
        keyword: vis.value.keyword,
        result: r.data.data,
        created_at: new Date().toLocaleString()
      })
      saveHistory()
    } else {
      ElMessage.error(r.data.message || '检测失败')
    }
  } catch (e) {
    ElMessage.error('请求失败：' + (e.message || '未知错误'))
  } finally {
    visLoading.value = false
  }
}

// ---------- Tab2: AI 友好内容 ----------
const cnt = ref({ brand: '', product: '', keyword: '', language: '中文' })
const cntLoading = ref(false)
const cntResult = ref(null)

async function runContent() {
  if (!cnt.value.product) return
  cntLoading.value = true
  cntResult.value = null
  try {
    const r = await axios.post('/api/geo/content', cnt.value, { timeout: 300000 })
    if (r.data.success) cntResult.value = r.data.data
    else ElMessage.error(r.data.message || '生成失败')
  } catch (e) {
    ElMessage.error('请求失败：' + (e.message || '未知错误'))
  } finally {
    cntLoading.value = false
  }
}

// ---------- Tab3: 提问挖掘 ----------
const prm = ref({ keyword: '', platform: 'Amazon', market: '北美' })
const prmLoading = ref(false)
const prmResult = ref(null)

function priorityText(p) {
  return { high: '高优先', medium: '中优先', low: '低优先' }[p] || '中优先'
}

async function runPrompts() {
  if (!prm.value.keyword) return
  prmLoading.value = true
  prmResult.value = null
  try {
    const r = await axios.post('/api/geo/prompts', prm.value, { timeout: 300000 })
    if (r.data.success) prmResult.value = r.data.data
    else ElMessage.error(r.data.message || '挖掘失败')
  } catch (e) {
    ElMessage.error('请求失败：' + (e.message || '未知错误'))
  } finally {
    prmLoading.value = false
  }
}

// ---------- 历史记录 ----------
const HISTORY_KEY = 'gs_geo_history'
const history = ref([])

function loadHistory() {
  try {
    const raw = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') || []
    // 兼容旧格式（brand 字段）—— 旧记录无 result 时显示品牌名
    history.value = raw.map(h => ({
      summary: h.summary || h.brand || '—',
      score: h.score || 0,
      keyword: h.keyword || '',
      result: h.result,
      created_at: h.created_at || ''
    }))
  } catch { history.value = [] }
}
function saveHistory() {
  localStorage.setItem(HISTORY_KEY, JSON.stringify((history.value || []).slice(0, 20)))
}
function clearHistory() {
  history.value = []
  saveHistory()
}
function restoreItem(h) {
  if (!h.result) return
  activeTab.value = 'visibility'
  visResult.value = h.result
  // 尝试把竞品回填到表单（如果历史记录里有的话）
  vis.value.brand = h.result.main_brand || ''
  vis.value.keyword = h.result.keyword || ''
  vis.value.platform = h.result.platform || 'Amazon'
  const oldCompetitors = (h.result.brands || [])
    .filter(b => b.name !== h.result.main_brand)
    .map(b => b.name)
  vis.value.competitors = oldCompetitors.slice(0, 4)
  while (vis.value.competitors.length < 3) vis.value.competitors.push('')
}

onMounted(loadHistory)
</script>