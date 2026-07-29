<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">商品管理</h2>
        <p class="text-sm text-slate-500 mt-2">已上架商品的状态监控与管理</p>
      </div>
      <div class="flex gap-3">
        <el-select v-model="filterShopId" placeholder="按店铺筛选" clearable style="width: 200px" @change="loadListings">
          <el-option v-for="shop in shops" :key="shop.id" :label="shop.name" :value="shop.id" />
        </el-select>
        <button @click="loadListings" class="btn-secondary px-4 py-2 rounded-lg text-sm">
          刷新
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-slate-900">{{ listings.length }}</p>
        <p class="text-xs text-slate-500 mt-1">全部商品</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-emerald-600">{{ activeCount }}</p>
        <p class="text-xs text-slate-500 mt-1">在售中</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-amber-600">{{ pendingCount }}</p>
        <p class="text-xs text-slate-500 mt-1">待审核</p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-2xl font-bold text-red-500">{{ errorCount }}</p>
        <p class="text-xs text-slate-500 mt-1">异常</p>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="w-10 h-10 border-2 border-violet-200 border-t-violet-600 rounded-full animate-spin mx-auto mb-4"></div>
      <p class="text-slate-500">加载中...</p>
    </div>

    <div v-else-if="!listings.length" class="text-center py-16 card">
      <Package class="w-16 h-16 text-slate-300 mx-auto mb-4" />
      <p class="text-slate-500 font-medium">暂无已上架商品</p>
      <p class="text-xs text-slate-400 mt-2">在"文案生成"中生成文案后可一键上架</p>
    </div>

    <div v-else class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-slate-50 text-left">
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">SKU</th>
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">标题</th>
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">平台</th>
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">价格</th>
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">库存</th>
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">状态</th>
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">时间</th>
              <th class="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in listings" :key="item.id" class="border-t border-slate-100 hover:bg-slate-50 transition-colors">
              <td class="px-5 py-3.5 font-mono text-xs font-semibold text-violet-600">{{ item.sku }}</td>
              <td class="px-5 py-3.5 text-slate-700 max-w-xs truncate" :title="item.title">{{ item.title }}</td>
              <td class="px-5 py-3.5">
                <span class="px-2 py-0.5 rounded-full text-xs font-semibold" :class="platformBadge(item.platform)">
                  {{ item.platform }}
                </span>
              </td>
              <td class="px-5 py-3.5 font-semibold text-slate-800">{{ item.price ? '$'+item.price : '-' }}</td>
              <td class="px-5 py-3.5 text-slate-600">{{ item.stock || '-' }}</td>
              <td class="px-5 py-3.5">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold" :class="statusBadge(item.listing_status)">
                  {{ statusLabel(item.listing_status) }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-xs text-slate-400">{{ item.created_at?.slice(0,10) }}</td>
              <td class="px-5 py-3.5">
                <div class="flex gap-2">
                  <button @click="openDetail(item)" class="btn-outline px-3 py-1.5 rounded-lg text-xs flex items-center gap-1">
                    <Eye class="w-3.5 h-3.5" />详情
                  </button>
                  <button @click="removeListing(item)" class="text-red-500 hover:bg-red-50 px-2 py-1.5 rounded-lg text-xs flex items-center gap-1">
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="商品详情" size="480" destroy-on-close>
      <div v-if="selectedItem" class="space-y-5">
        <div class="flex items-center justify-between">
          <span class="text-xs text-slate-500">{{ selectedItem.platform }} · {{ selectedItem.sku }}</span>
          <span class="px-2.5 py-1 rounded-full text-xs font-semibold" :class="statusBadge(selectedItem.listing_status)">
            {{ statusLabel(selectedItem.listing_status) }}
          </span>
        </div>

        <div>
          <h4 class="text-base font-bold text-slate-900">{{ selectedItem.title }}</h4>
        </div>

        <div class="card p-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <span class="text-slate-400 text-xs">价格</span>
            <p class="font-semibold text-slate-800">${{ selectedItem.price }}</p>
          </div>
          <div>
            <span class="text-slate-400 text-xs">库存</span>
            <p class="font-semibold text-slate-800">{{ selectedItem.stock }}</p>
          </div>
          <div>
            <span class="text-slate-400 text-xs">商品类型</span>
            <p class="text-slate-600 text-sm">{{ selectedItem.product_type || '-' }}</p>
          </div>
          <div>
            <span class="text-slate-400 text-xs">平台 ID</span>
            <p class="font-mono text-xs text-slate-600">{{ selectedItem.platform_listing_id || '待同步' }}</p>
          </div>
        </div>

        <div class="card p-4">
          <h5 class="text-xs font-bold text-slate-900 mb-2">卖点 (Bullet Points)</h5>
          <ul v-if="selectedItem.bullet_points?.length" class="list-disc list-inside space-y-1">
            <li v-for="(bp, i) in selectedItem.bullet_points" :key="i" class="text-sm text-slate-600">{{ bp }}</li>
          </ul>
          <p v-else class="text-sm text-slate-400">暂无</p>
        </div>

        <div class="card p-4">
          <h5 class="text-xs font-bold text-slate-900 mb-2">描述</h5>
          <p class="text-sm text-slate-600 whitespace-pre-wrap">{{ selectedItem.description || '暂无' }}</p>
        </div>

        <div class="card p-4">
          <h5 class="text-xs font-bold text-slate-900 mb-3">快速编辑</h5>
          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block text-xs text-slate-500 mb-1">价格</label>
              <input v-model="editForm.price" type="number" class="input-field w-full px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">库存</label>
              <input v-model="editForm.stock" type="number" class="input-field w-full px-3 py-2 text-sm" />
            </div>
          </div>
          <div class="mb-3">
            <label class="block text-xs text-slate-500 mb-1">状态</label>
            <select v-model="editForm.listing_status" class="input-field w-full px-3 py-2 text-sm">
              <option value="active">在售</option>
              <option value="pending">待审核</option>
              <option value="inactive">已下架</option>
            </select>
          </div>
          <button @click="saveEdit" :disabled="editLoading" class="btn-primary px-4 py-2 rounded-lg text-sm w-full">
            {{ editLoading ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Package, Eye, Trash2 } from 'lucide-vue-next'
import { platformAPI } from '../api/client'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const listings = ref([])
const shops = ref([])
const filterShopId = ref(null)
const drawerVisible = ref(false)
const selectedItem = ref(null)
const editLoading = ref(false)
const editForm = ref({ price: 0, stock: 0, listing_status: 'active' })

const activeCount = computed(() => listings.value.filter(l => l.listing_status === 'active').length)
const pendingCount = computed(() => listings.value.filter(l => l.listing_status === 'pending').length)
const errorCount = computed(() => listings.value.filter(l => l.listing_status === 'error').length)

function statusBadge(s) {
  const map = { active: 'bg-emerald-100 text-emerald-700', pending: 'bg-amber-100 text-amber-700', error: 'bg-red-100 text-red-700', inactive: 'bg-slate-100 text-slate-600' }
  return map[s] || 'bg-slate-100 text-slate-600'
}

function statusLabel(s) {
  const map = { active: '在售', pending: '待审核', error: '异常', inactive: '已下架' }
  return map[s] || s
}

function platformBadge(p) {
  const map = { amazon: 'bg-amber-100 text-amber-700', ebay: 'bg-red-100 text-red-700', temu: 'bg-rose-100 text-rose-700', 'local-shop': 'bg-blue-100 text-blue-700' }
  return map[p] || 'bg-slate-100 text-slate-600'
}

async function loadShops() {
  try {
    const res = await platformAPI.list()
    if (res.data.success) shops.value = res.data.data || []
  } catch (e) { console.error(e) }
}

async function loadListings() {
  loading.value = true
  try {
    const res = await platformAPI.getListings(filterShopId.value)
    if (res.data.success) listings.value = res.data.data || []
  } catch (e) { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openDetail(item) {
  selectedItem.value = item
  editForm.value = { price: item.price, stock: item.stock, listing_status: item.listing_status }
  drawerVisible.value = true
}

async function saveEdit() {
  if (!selectedItem.value) return
  editLoading.value = true
  try {
    const res = await platformAPI.updateListing(selectedItem.value.id, editForm.value)
    if (res.data.success) {
      ElMessage.success('已保存')
      Object.assign(selectedItem.value, editForm.value)
      await loadListings()
    } else {
      ElMessage.error(res.data.message || '保存失败')
    }
  } catch (e) { ElMessage.error('保存失败') }
  finally { editLoading.value = false }
}

async function removeListing(item) {
  try {
    await ElMessageBox.confirm(`确定删除 ${item.sku}？`, '删除确认', { type: 'warning' })
    const res = await platformAPI.deleteListing(item.id)
    if (res.data.success) {
      ElMessage.success('已删除')
      await loadListings()
    }
  } catch (e) { /* cancelled */ }
}

onMounted(() => {
  Promise.all([loadShops(), loadListings()])
})
</script>
