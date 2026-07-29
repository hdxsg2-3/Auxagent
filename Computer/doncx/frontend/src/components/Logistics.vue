<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">物流单据</h2>
        <p class="text-sm text-slate-500 mt-2">一键生成货运单据，支持保存记录、查看物流与导出</p>
      </div>
      <button
        v-if="activeTab === 'records'"
        @click="activeTab = 'form'"
        class="btn-primary flex items-center gap-2 px-6 py-3 rounded-xl font-semibold"
      >
        <PlusCircle class="w-5 h-5" />
        新建单据
      </button>
    </div>

    <el-tabs v-model="activeTab" class="logistics-tabs" type="border-card">
      <el-tab-pane label="生成单据" name="form">
        <div class="grid grid-cols-2 gap-7 mt-6">
          <div class="card p-7">
            <h3 class="text-lg font-bold text-slate-900 mb-6">单据信息</h3>

            <div class="space-y-6">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-2.5">单据类型</label>
                  <select v-model="form.type" class="input-field w-full px-4 py-3 text-sm">
                    <option value="commercial_invoice">商业发票</option>
                    <option value="packing_list">装箱单</option>
                    <option value="bill_of_lading">提单</option>
                    <option value="certificate_of_origin">原产地证</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-2.5">运输方式</label>
                  <select v-model="form.shipping_method" class="input-field w-full px-4 py-3 text-sm">
                    <option value="sea">海运</option>
                    <option value="air">空运</option>
                    <option value="express">快递</option>
                    <option value="rail">铁路</option>
                  </select>
                </div>
              </div>

              <div>
                <h4 class="text-sm font-semibold text-slate-700 mb-3">发货方信息</h4>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <input v-model="form.sender.name" class="input-field w-full px-4 py-3 text-sm" placeholder="公司名称" />
                  <input v-model="form.sender.contact" class="input-field w-full px-4 py-3 text-sm" placeholder="联系人" />
                  <input v-model="form.sender.address" class="input-field w-full px-4 py-3 text-sm" placeholder="地址" />
                  <input v-model="form.sender.phone" class="input-field w-full px-4 py-3 text-sm" placeholder="电话" />
                </div>
              </div>

              <div>
                <h4 class="text-sm font-semibold text-slate-700 mb-3">收货方信息</h4>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <input v-model="form.receiver.name" class="input-field w-full px-4 py-3 text-sm" placeholder="公司名称" />
                  <input v-model="form.receiver.contact" class="input-field w-full px-4 py-3 text-sm" placeholder="联系人" />
                  <input v-model="form.receiver.address" class="input-field w-full px-4 py-3 text-sm" placeholder="地址" />
                  <input v-model="form.receiver.phone" class="input-field w-full px-4 py-3 text-sm" placeholder="电话" />
                </div>
              </div>

              <div>
                <h4 class="text-sm font-semibold text-slate-700 mb-3">商品明细</h4>
                <div class="space-y-3">
                  <div
                    v-for="(item, index) in form.items"
                    :key="index"
                    class="grid grid-cols-1 sm:grid-cols-5 gap-3 items-center"
                  >
                    <input v-model="item.name" class="input-field px-4 py-2.5 text-sm" placeholder="商品名称" />
                    <input v-model="item.quantity" type="number" class="input-field px-4 py-2.5 text-sm" placeholder="数量" />
                    <input v-model="item.unit" class="input-field px-4 py-2.5 text-sm" placeholder="单位" />
                    <input v-model="item.unit_price" type="number" class="input-field px-4 py-2.5 text-sm" placeholder="单价" />
                    <div class="flex items-center justify-between">
                      <span class="text-sm font-semibold text-slate-700">{{ (item.quantity * item.unit_price).toFixed(2) }}</span>
                      <button @click="removeItem(index)" class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
                <button @click="addItem" class="mt-3 btn-outline px-4 py-2.5 rounded-lg text-sm flex items-center gap-2">
                  <Plus class="w-4 h-4" />
                  添加商品
                </button>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-2.5">总件数</label>
                  <input v-model="form.total_packages" type="number" class="input-field w-full px-4 py-3 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-2.5">总重量(kg)</label>
                  <input v-model="form.total_weight" type="number" class="input-field w-full px-4 py-3 text-sm" />
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-2.5">总金额(USD)</label>
                  <input :value="totalAmount" readonly class="input-field w-full px-4 py-3 text-sm bg-slate-50" />
                </div>
              </div>

              <button
                @click="generateDocument"
                :disabled="loading"
                class="w-full py-3.5 rounded-xl flex items-center justify-center gap-2.5 text-sm font-semibold transition-all"
                :class="[
                  loading
                    ? 'bg-slate-400 cursor-not-allowed'
                    : 'btn-primary'
                ]"
              >
                <span v-if="loading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <FileText v-else class="w-5 h-5" />
                {{ loading ? '生成中...' : '生成单据' }}
              </button>
            </div>
          </div>

          <div class="card p-7">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-bold text-slate-900">单据预览</h3>
              <div v-if="documentGenerated" class="flex gap-2">
                <button @click="printDocument" class="btn-secondary px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                  <Printer class="w-4 h-4" />
                  打印/PDF
                </button>
                <button @click="downloadExcel" class="btn-outline px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                  <Download class="w-4 h-4" />
                  Excel
                </button>
              </div>
            </div>

            <div v-if="!documentGenerated" class="text-center py-16">
              <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-5">
                <FileText class="w-10 h-10 text-slate-400" />
              </div>
              <p class="text-slate-500 font-medium">填写信息后点击"生成单据"</p>
            </div>

            <div v-else id="logistics-preview" class="bg-white rounded-xl p-6 border border-violet-100 shadow-lg">
              <div class="text-center mb-6 pb-4 border-b border-violet-100">
                <h4 class="text-xl font-bold text-slate-900">{{ getDocTypeLabel(form.type) }}</h4>
                <p class="text-sm text-slate-500 mt-1">{{ generatedDoc.document_id || '' }}</p>
              </div>

              <div class="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <p class="text-xs text-slate-500 mb-1">发货方</p>
                  <p class="text-sm font-semibold text-slate-800">{{ form.sender.name }}</p>
                  <p class="text-xs text-slate-500">{{ form.sender.contact }}</p>
                  <p class="text-xs text-slate-500">{{ form.sender.address }}</p>
                </div>
                <div>
                  <p class="text-xs text-slate-500 mb-1">收货方</p>
                  <p class="text-sm font-semibold text-slate-800">{{ form.receiver.name }}</p>
                  <p class="text-xs text-slate-500">{{ form.receiver.contact }}</p>
                  <p class="text-xs text-slate-500">{{ form.receiver.address }}</p>
                </div>
              </div>

              <table class="w-full text-sm mb-6">
                <thead>
                  <tr class="border-b border-violet-100">
                    <th class="text-left py-2 text-xs font-semibold text-slate-500">商品名称</th>
                    <th class="text-center py-2 text-xs font-semibold text-slate-500">数量</th>
                    <th class="text-center py-2 text-xs font-semibold text-slate-500">单位</th>
                    <th class="text-right py-2 text-xs font-semibold text-slate-500">单价(USD)</th>
                    <th class="text-right py-2 text-xs font-semibold text-slate-500">金额(USD)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in form.items" :key="index" class="border-b border-violet-50">
                    <td class="py-3 text-slate-700">{{ item.name }}</td>
                    <td class="py-3 text-center text-slate-700">{{ item.quantity }}</td>
                    <td class="py-3 text-center text-slate-700">{{ item.unit }}</td>
                    <td class="py-3 text-right text-slate-700">{{ item.unit_price }}</td>
                    <td class="py-3 text-right font-semibold text-slate-800">{{ (item.quantity * item.unit_price).toFixed(2) }}</td>
                  </tr>
                  <tr class="bg-violet-50">
                    <td colspan="4" class="py-3 text-right font-semibold text-slate-700">合计</td>
                    <td class="py-3 text-right font-bold text-violet-600">{{ totalAmount }}</td>
                  </tr>
                </tbody>
              </table>

              <div class="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <p class="text-slate-500">运输方式: {{ getShippingMethodLabel(form.shipping_method) }}</p>
                  <p class="text-slate-500">总件数: {{ form.total_packages }}</p>
                </div>
                <div>
                  <p class="text-slate-500">总重量: {{ form.total_weight }} kg</p>
                  <p class="text-slate-500">日期: {{ new Date().toLocaleDateString() }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="历史记录" name="records">
        <div class="mt-6">
          <div v-if="recordsLoading" class="text-center py-12">
            <div class="w-10 h-10 border-2 border-violet-200 border-t-violet-600 rounded-full animate-spin mx-auto mb-4"></div>
            <p class="text-slate-500">加载中...</p>
          </div>

          <div v-else-if="!records.length" class="text-center py-16">
            <div class="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-5">
              <ClipboardList class="w-10 h-10 text-slate-400" />
            </div>
            <p class="text-slate-500 font-medium">暂无物流单据记录</p>
            <button @click="activeTab = 'form'" class="mt-4 btn-primary px-5 py-2 rounded-lg text-sm">去生成</button>
          </div>

          <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div
              v-for="doc in records"
              :key="doc.id"
              class="card p-5 hover:shadow-md transition-shadow cursor-pointer"
              @click="openDetail(doc)"
            >
              <div class="flex items-start justify-between mb-3">
                <div>
                  <h4 class="font-bold text-slate-900">{{ getDocTypeLabel(doc.doc_type) }}</h4>
                  <p class="text-xs text-slate-500 mt-1">{{ doc.created_at }}</p>
                </div>
                <span
                  class="px-2.5 py-1 rounded-full text-xs font-semibold"
                  :class="statusClass(doc.status)"
                >
                  {{ statusLabel(doc.status) }}
                </span>
              </div>

              <div class="text-sm text-slate-600 space-y-1 mb-4">
                <p>运输方式：{{ getShippingMethodLabel(doc.transport_mode) }}</p>
                <p>收货方：{{ doc.consignee_info?.name || '' }}</p>
                <p>总金额：{{ doc.totals?.total_amount?.toFixed(2) || '0.00' }} USD</p>
                <p v-if="doc.tracking_number">运单号：{{ doc.tracking_number }}</p>
              </div>

              <div class="flex gap-2">
                <button @click.stop="openDetail(doc)" class="btn-secondary px-3 py-1.5 rounded-lg text-xs flex items-center gap-1">
                  <Eye class="w-3.5 h-3.5" />
                  查看详情
                </button>
                <button @click.stop="openTracking(doc)" class="btn-outline px-3 py-1.5 rounded-lg text-xs flex items-center gap-1">
                  <Truck class="w-3.5 h-3.5" />
                  物流跟踪
                </button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 详情/物流抽屉 -->
    <el-drawer
      v-model="detailVisible"
      :title="selectedDoc ? getDocTypeLabel(selectedDoc.doc_type) : '单据详情'"
      size="520"
      destroy-on-close
    >
      <div v-if="selectedDoc" class="space-y-6">
        <div class="flex items-center justify-between">
          <span class="text-sm text-slate-500">当前状态</span>
          <span class="px-2.5 py-1 rounded-full text-xs font-semibold" :class="statusClass(selectedDoc.status)">
            {{ statusLabel(selectedDoc.status) }}
          </span>
        </div>

        <div class="card p-4">
          <h4 class="text-sm font-bold text-slate-900 mb-3">更新物流状态</h4>
          <div class="grid grid-cols-1 gap-3">
            <select v-model="statusForm.status" class="input-field w-full px-3 py-2 text-sm">
              <option value="generated">已生成</option>
              <option value="shipped">已发货</option>
              <option value="in_transit">运输中</option>
              <option value="customs_clearance">清关中</option>
              <option value="out_for_delivery">派送中</option>
              <option value="delivered">已签收</option>
            </select>
            <input v-model="statusForm.tracking_number" class="input-field w-full px-3 py-2 text-sm" placeholder="运单号" />
            <input v-model="statusForm.carrier" class="input-field w-full px-3 py-2 text-sm" placeholder="承运商" />
            <button
              @click="updateStatus"
              :disabled="statusLoading"
              class="btn-primary px-4 py-2 rounded-lg text-sm"
            >
              {{ statusLoading ? '更新中...' : '更新状态' }}
            </button>
          </div>
        </div>

        <div>
          <h4 class="text-sm font-bold text-slate-900 mb-3">物流轨迹</h4>
          <el-timeline>
            <el-timeline-item
              v-for="(track, idx) in trackingList"
              :key="idx"
              :type="track.type || 'primary'"
              :timestamp="track.created_at"
              placement="top"
            >
              <p class="text-sm font-semibold text-slate-800">{{ statusLabel(track.status) }}</p>
              <p v-if="track.location" class="text-xs text-slate-500">{{ track.location }}</p>
              <p v-if="track.description" class="text-xs text-slate-500 mt-1">{{ track.description }}</p>
            </el-timeline-item>
            <el-timeline-item v-if="!trackingList.length" timestamp="-">
              <p class="text-sm text-slate-500">暂无物流轨迹</p>
            </el-timeline-item>
          </el-timeline>

          <div class="card p-4 mt-4">
            <h5 class="text-xs font-bold text-slate-900 mb-2">新增轨迹</h5>
            <div class="grid grid-cols-1 gap-2">
              <input v-model="trackingForm.status" class="input-field w-full px-3 py-2 text-sm" placeholder="状态，如 in_transit" />
              <input v-model="trackingForm.location" class="input-field w-full px-3 py-2 text-sm" placeholder="地点" />
              <input v-model="trackingForm.description" class="input-field w-full px-3 py-2 text-sm" placeholder="描述" />
              <button
                @click="addTracking"
                :disabled="trackingLoading"
                class="btn-outline px-4 py-2 rounded-lg text-sm"
              >
                {{ trackingLoading ? '提交中...' : '添加轨迹' }}
              </button>
            </div>
          </div>
        </div>

        <div class="card p-4">
          <h4 class="text-sm font-bold text-slate-900 mb-3">单据信息</h4>
          <div class="text-sm text-slate-600 space-y-2">
            <p>发货方：{{ selectedDoc.shipper_info?.name }}</p>
            <p>收货方：{{ selectedDoc.consignee_info?.name }}</p>
            <p>运输方式：{{ getShippingMethodLabel(selectedDoc.transport_mode) }}</p>
            <p>总件数：{{ selectedDoc.totals?.total_packages }}</p>
            <p>总重量：{{ selectedDoc.totals?.total_weight }} kg</p>
            <p>总金额：{{ selectedDoc.totals?.total_amount?.toFixed(2) }} USD</p>
            <p v-if="selectedDoc.tracking_number">运单号：{{ selectedDoc.tracking_number }}</p>
            <p v-if="selectedDoc.carrier">承运商：{{ selectedDoc.carrier }}</p>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { PlusCircle, FileText, Trash2, Plus, Download, Printer, ClipboardList, Eye, Truck } from 'lucide-vue-next'
import { logisticsAPI } from '../api/client'
import { ElMessage } from 'element-plus'

const activeTab = ref('form')
const loading = ref(false)
const recordsLoading = ref(false)
const documentGenerated = ref(false)
const generatedDoc = ref({})
const records = ref([])

const detailVisible = ref(false)
const selectedDoc = ref(null)
const trackingList = ref([])
const statusLoading = ref(false)
const trackingLoading = ref(false)

const statusForm = reactive({
  status: '',
  tracking_number: '',
  carrier: ''
})

const trackingForm = reactive({
  status: '',
  location: '',
  description: ''
})

const form = reactive({
  type: 'commercial_invoice',
  shipping_method: 'sea',
  sender: {
    name: 'Shenzhen Global Trading Co., Ltd.',
    contact: 'Zhang Wei',
    address: 'Room 1001, Building A, Futian District, Shenzhen, China',
    phone: '+86 755 8888 8888'
  },
  receiver: {
    name: 'ABC Trading Inc.',
    contact: 'John Smith',
    address: '123 Main Street, New York, NY 10001, USA',
    phone: '+1 212 555 5555'
  },
  items: [
    { name: 'Power Bank 20000mAh', quantity: 100, unit: 'pcs', unit_price: 18.50 },
    { name: 'USB Cable Type-C', quantity: 200, unit: 'pcs', unit_price: 3.20 }
  ],
  total_packages: 5,
  total_weight: 15
})

const shippingMethodLabels = {
  sea: '海运',
  air: '空运',
  express: '快递',
  rail: '铁路'
}

const docTypeLabels = {
  commercial_invoice: '商业发票',
  packing_list: '装箱单',
  bill_of_lading: '提单',
  certificate_of_origin: '原产地证'
}

const statusLabels = {
  generated: '已生成',
  shipped: '已发货',
  in_transit: '运输中',
  customs_clearance: '清关中',
  out_for_delivery: '派送中',
  delivered: '已签收'
}

function getShippingMethodLabel(method) {
  return shippingMethodLabels[method] || method
}

function getDocTypeLabel(type) {
  return docTypeLabels[type] || type
}

function statusLabel(status) {
  return statusLabels[status] || status
}

function statusClass(status) {
  const map = {
    generated: 'bg-slate-100 text-slate-700',
    shipped: 'bg-blue-100 text-blue-700',
    in_transit: 'bg-violet-100 text-violet-700',
    customs_clearance: 'bg-orange-100 text-orange-700',
    out_for_delivery: 'bg-yellow-100 text-yellow-700',
    delivered: 'bg-green-100 text-green-700'
  }
  return map[status] || 'bg-slate-100 text-slate-700'
}

const totalAmount = computed(() => {
  return form.items.reduce((sum, item) => sum + (Number(item.quantity) * Number(item.unit_price)), 0).toFixed(2)
})

function addItem() {
  form.items.push({ name: '', quantity: 1, unit: 'pcs', unit_price: 0 })
}

function removeItem(index) {
  if (form.items.length > 1) {
    form.items.splice(index, 1)
  }
}

async function generateDocument() {
  loading.value = true

  try {
    const payload = {
      type: form.type,
      shipping_method: form.shipping_method,
      sender: form.sender,
      receiver: form.receiver,
      items: form.items.map(item => ({
        name: item.name,
        quantity: Number(item.quantity),
        unit: item.unit,
        unit_price: Number(item.unit_price)
      })),
      total_packages: Number(form.total_packages),
      total_weight: Number(form.total_weight)
    }
    const response = await logisticsAPI.generate(payload)

    if (response.data.success) {
      generatedDoc.value = response.data.data
      documentGenerated.value = true
      ElMessage.success('单据生成并保存成功')
      loadRecords()
    } else {
      ElMessage.error(response.data.message || '单据生成失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('生成过程中发生错误')
  } finally {
    loading.value = false
  }
}

function printDocument() {
  const printWindow = window.open('', '_blank')
  const content = document.getElementById('logistics-preview')?.innerHTML
  if (!printWindow || !content) return
  printWindow.document.write(`
    <html>
      <head>
        <title>物流单据打印</title>
        <style>
          body { font-family: system-ui, -apple-system, sans-serif; padding: 40px; color: #1e293b; }
          table { width: 100%; border-collapse: collapse; margin-top: 16px; }
          th, td { border-bottom: 1px solid #e2e8f0; padding: 8px; text-align: left; }
          th { font-size: 12px; color: #64748b; }
          td { font-size: 13px; }
          .text-right { text-align: right; }
          .text-center { text-align: center; }
        </style>
      </head>
      <body>${content}</body>
    </html>
  `)
  printWindow.document.close()
  printWindow.focus()
  setTimeout(() => {
    printWindow.print()
    printWindow.close()
  }, 250)
}

function downloadExcel() {
  const headers = ['商品名称', '数量', '单位', '单价(USD)', '金额(USD)']
  const rows = form.items.map(item => [
    item.name,
    item.quantity,
    item.unit,
    item.unit_price,
    (item.quantity * item.unit_price).toFixed(2)
  ])
  rows.push(['合计', '', '', '', totalAmount.value])

  const csvContent = [
    [getDocTypeLabel(form.type)],
    ['发货方', form.sender.name, form.sender.contact, form.sender.address, form.sender.phone],
    ['收货方', form.receiver.name, form.receiver.contact, form.receiver.address, form.receiver.phone],
    [],
    headers,
    ...rows
  ].map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n')

  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `物流单据_${form.type}_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

async function loadRecords() {
  recordsLoading.value = true
  try {
    const res = await logisticsAPI.listDocuments()
    if (res.data.success) {
      records.value = res.data.data || []
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('加载历史记录失败')
  } finally {
    recordsLoading.value = false
  }
}

function openDetail(doc) {
  selectedDoc.value = doc
  statusForm.status = doc.status
  statusForm.tracking_number = doc.tracking_number || ''
  statusForm.carrier = doc.carrier || ''
  loadTracking(doc.id)
  detailVisible.value = true
}

function openTracking(doc) {
  openDetail(doc)
}

async function loadTracking(docId) {
  try {
    const res = await logisticsAPI.listTracking(docId)
    if (res.data.success) {
      trackingList.value = res.data.data || []
    }
  } catch (e) {
    console.error(e)
  }
}

async function updateStatus() {
  if (!selectedDoc.value) return
  statusLoading.value = true
  try {
    const res = await logisticsAPI.updateStatus(selectedDoc.value.id, {
      status: statusForm.status,
      tracking_number: statusForm.tracking_number,
      carrier: statusForm.carrier
    })
    if (res.data.success) {
      ElMessage.success('状态已更新')
      selectedDoc.value.status = statusForm.status
      selectedDoc.value.tracking_number = statusForm.tracking_number
      selectedDoc.value.carrier = statusForm.carrier
      loadTracking(selectedDoc.value.id)
      loadRecords()
    } else {
      ElMessage.error(res.data.message || '更新失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('更新状态失败')
  } finally {
    statusLoading.value = false
  }
}

async function addTracking() {
  if (!selectedDoc.value) return
  trackingLoading.value = true
  try {
    const res = await logisticsAPI.addTracking(selectedDoc.value.id, {
      status: trackingForm.status,
      location: trackingForm.location,
      description: trackingForm.description
    })
    if (res.data.success) {
      ElMessage.success('轨迹已添加')
      trackingForm.status = ''
      trackingForm.location = ''
      trackingForm.description = ''
      loadTracking(selectedDoc.value.id)
      loadRecords()
    } else {
      ElMessage.error(res.data.message || '添加失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('添加轨迹失败')
  } finally {
    trackingLoading.value = false
  }
}

watch(activeTab, (val) => {
  if (val === 'records') {
    loadRecords()
  }
})
</script>

<style scoped>
.logistics-tabs :deep(.el-tabs__header) {
  background: transparent;
  border-bottom: none;
}
.logistics-tabs :deep(.el-tabs__item) {
  border-radius: 8px 8px 0 0;
  margin-right: 4px;
  font-weight: 500;
}
.logistics-tabs :deep(.el-tabs__item.is-active) {
  background: white;
  color: #7c3aed;
}
</style>
