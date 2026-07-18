<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">物流单据</h2>
        <p class="text-sm text-slate-500 mt-2">一键生成货运单据，支持多种格式导出</p>
      </div>
      <button class="btn-primary flex items-center gap-2 px-6 py-3 rounded-xl font-semibold">
        <PlusCircle class="w-5 h-5" />
        新建单据
      </button>
    </div>

    <div class="grid grid-cols-2 gap-7">
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
            <button class="btn-secondary px-4 py-2 rounded-lg text-sm flex items-center gap-2">
              <Download class="w-4 h-4" />
              PDF
            </button>
            <button class="btn-outline px-4 py-2 rounded-lg text-sm flex items-center gap-2">
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

        <div v-else class="bg-white rounded-xl p-6 border border-violet-100 shadow-lg">
          <div class="text-center mb-6 pb-4 border-b border-violet-100">
            <h4 class="text-xl font-bold text-slate-900">商业发票</h4>
            <p class="text-sm text-slate-500 mt-1">COMMERCIAL INVOICE</p>
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
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { PlusCircle, FileText, Trash2, Plus, Download } from 'lucide-vue-next'
import { logisticsAPI } from '../api/client'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const documentGenerated = ref(false)

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

function getShippingMethodLabel(method) {
  return shippingMethodLabels[method] || method
}

const totalAmount = computed(() => {
  return form.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0).toFixed(2)
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
    const response = await logisticsAPI.generate(form)

    if (response.data.success) {
      documentGenerated.value = true
      ElMessage.success('单据生成成功')
    } else {
      ElMessage.error('单据生成失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('生成过程中发生错误')
  } finally {
    loading.value = false
  }
}
</script>
