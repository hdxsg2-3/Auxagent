<template>
  <div class="max-w-7xl mx-auto">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-900">多平台店铺管理</h2>
        <p class="text-sm text-slate-500 mt-1">绑定 Amazon / Temu 店铺，实现 Listing 自动上架与客服消息自动回复</p>
      </div>
      <button @click="openCreate" class="btn-primary px-5 py-2.5 rounded-xl flex items-center gap-2">
        <Store class="w-4 h-4" /> 新增店铺
      </button>
    </div>

    <!-- 店铺列表 -->
    <div class="card p-6">
      <el-table :data="shops" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            <el-tag :type="row.platform === 'amazon' ? 'warning' : row.platform === 'ebay' ? 'info' : row.platform === 'temu' ? 'danger' : 'success'">
              {{ row.platform === 'local-shop' ? 'LocalShop' : row.platform.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="店铺名称" />
        <el-table-column prop="region" label="区域" width="100" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <span :class="statusClass(row.status)">{{ statusText(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="凭证" width="140">
          <template #default="{ row }">
            <span class="text-xs text-slate-400">{{ Object.keys(row.credentials_summary || {}).length }} 项已配置</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="420">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-2">
              <el-button size="small" @click="testConnection(row)" :loading="row.testing">测试连接</el-button>
              <el-button size="small" @click="syncProducts(row)" :loading="row.syncingProducts">同步商品</el-button>
              <el-button size="small" @click="syncMessages(row)" :loading="row.syncingMessages">同步消息</el-button>
              <el-button size="small" type="primary" @click="openPublish(row)">上架</el-button>
              <el-button size="small" @click="openSendMessage(row)">发消息</el-button>
              <el-button size="small" @click="viewLogs(row)">日志</el-button>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && shops.length === 0" description="暂无店铺，请先新增店铺" />
    </div>

    <!-- 新增/编辑店铺 -->
    <el-dialog v-model="shopDialogVisible" :title="isEdit ? '编辑店铺' : '新增店铺'" width="640px">
      <el-form :model="shopForm" label-width="120px">
        <el-form-item label="平台">
          <el-select v-model="shopForm.platform" placeholder="选择平台" style="width: 100%">
            <el-option label="LocalShop 测试平台（免费即时开通）" value="local-shop" />
            <el-option label="Amazon" value="amazon" />
            <el-option label="eBay" value="ebay" />
            <el-option label="Temu" value="temu" />
          </el-select>
        </el-form-item>
        <el-form-item label="店铺名称">
          <el-input v-model="shopForm.name" placeholder="如：美国主店" />
        </el-form-item>
        <el-form-item label="区域">
          <el-input v-model="shopForm.region" placeholder="Amazon 填 na/eu/fe；Temu 填 global" />
        </el-form-item>
        <el-form-item v-if="shopForm.platform !== 'local-shop'" label="Mock 模式">
          <el-switch v-model="shopForm.mock" active-text="开启（无真实密钥时模拟调用）" />
        </el-form-item>
        <el-form-item v-if="shopForm.platform === 'local-shop'" label="说明">
          <el-alert type="success" :closable="false" show-icon>
            LocalShop 是内建免费电商平台，无需任何凭证，创建后立即可用。数据持久化到本地，支持真实上架和消息收发。
          </el-alert>
        </el-form-item>

        <!-- eBay 分字段凭证输入 -->
        <template v-if="shopForm.platform === 'ebay'">
          <el-form-item label="App ID (Client ID)">
            <el-input v-model="ebayCreds.client_id" placeholder="如：huangqia-xxx-SBX-xxx" />
          </el-form-item>
          <el-form-item label="Cert ID (Client Secret)">
            <el-input v-model="ebayCreds.client_secret" type="password" show-password placeholder="如：SBX-xxx" />
          </el-form-item>
          <el-form-item label="Dev ID">
            <el-input v-model="ebayCreds.dev_id" placeholder="可选，如：ad09acad-xxx" />
          </el-form-item>
          <el-form-item label="User Access Token">
            <el-input v-model="ebayCreds.user_token" type="password" show-password placeholder="OAuth Token Generator 生成" />
            <div class="text-xs text-amber-600 mt-1">
              <span class="font-medium">提示：</span>在 eBay 开发者后台 → 你的 App → OAuth Token Generator 生成 User Token。Token 有效期约 2 小时，过期后需重新生成。
            </div>
          </el-form-item>
          <el-form-item label="Marketplace">
            <el-select v-model="ebayCreds.marketplace_id" style="width: 100%">
              <el-option label="EBAY_US (美国)" value="EBAY_US" />
              <el-option label="EBAY_GB (英国)" value="EBAY_GB" />
              <el-option label="EBAY_DE (德国)" value="EBAY_DE" />
              <el-option label="EBAY_AU (澳大利亚)" value="EBAY_AU" />
              <el-option label="EBAY_CA (加拿大)" value="EBAY_CA" />
            </el-select>
          </el-form-item>
          <el-form-item label="Sandbox 模式">
            <el-switch v-model="ebayCreds.sandbox" active-text="Sandbox（测试环境）" inactive-text="Production（正式环境）" />
          </el-form-item>
          <el-form-item label="Category ID">
            <el-input v-model="ebayCreds.category_id" placeholder="可选，如 30022（电子产品）" />
          </el-form-item>
        </template>

        <!-- 其他平台 JSON 凭证 -->
        <el-form-item v-else-if="shopForm.platform !== 'local-shop'" label="平台凭证" class="mb-2">
          <div class="text-xs text-slate-500 mb-2">
            {{ platformHint }}
          </div>
          <el-input v-model="credentialsJson" type="textarea" :rows="8" placeholder="按平台要求填写 JSON 凭证" />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态">
          <el-select v-model="shopForm.status" style="width: 100%">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shopDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveShop" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 上架 Listing -->
    <el-dialog v-model="publishDialogVisible" title="上架 Listing 到店铺" width="600px">
      <el-form :model="publishForm" label-width="100px">
        <el-form-item label="SKU">
          <el-input v-model="publishForm.sku" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="publishForm.title" />
        </el-form-item>
        <el-form-item label="卖点">
          <el-input v-model="bulletInput" type="textarea" :rows="4" placeholder="每行一条" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="publishForm.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="publishForm.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="publishForm.stock" :min="0" :precision="0" />
        </el-form-item>
        <el-form-item label="Product Type">
          <el-input v-model="publishForm.product_type" placeholder="如 LAMP / MOUSE" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="publish" :loading="publishing">提交上架</el-button>
      </template>
    </el-dialog>

    <!-- 发送消息 -->
    <el-dialog v-model="messageDialogVisible" title="发送站内消息" width="520px">
      <el-form :model="messageForm" label-width="100px">
        <el-form-item label="订单号">
          <el-input v-model="messageForm.order_id" />
        </el-form-item>
        <el-form-item label="买家ID">
          <el-input v-model="messageForm.buyer_id" />
        </el-form-item>
        <el-form-item label="消息内容">
          <el-input v-model="messageForm.text" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="messageDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="sendMessage" :loading="sendingMessage">发送</el-button>
      </template>
    </el-dialog>

    <!-- 日志 -->
    <el-dialog v-model="logDialogVisible" title="店铺操作日志" width="760px">
      <el-table :data="logs" height="400" stripe>
        <el-table-column prop="created_at" label="时间" width="160" />
        <el-table-column prop="action" label="动作" width="140" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="error" label="错误" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Store } from 'lucide-vue-next'
import { platformAPI } from '../api/client.js'

const shops = ref([])
const loading = ref(false)

const shopDialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const currentShopId = ref(null)

const shopForm = reactive({
  platform: 'local-shop',
  name: '',
  region: 'global',
  mock: false,
  status: 'active'
})
const credentialsJson = ref('')

// eBay 分字段凭证
const ebayCreds = reactive({
  client_id: '',
  client_secret: '',
  dev_id: '',
  user_token: '',
  marketplace_id: 'EBAY_US',
  sandbox: true,
  category_id: '30022',
})

const publishDialogVisible = ref(false)
const publishing = ref(false)
const currentPublishShop = ref(null)
const publishForm = reactive({
  sku: '',
  title: '',
  bullet_points: [],
  description: '',
  price: 0,
  stock: 0,
  product_type: ''
})
const bulletInput = ref('')

const messageDialogVisible = ref(false)
const sendingMessage = ref(false)
const currentMessageShop = ref(null)
const messageForm = reactive({
  order_id: '',
  buyer_id: '',
  text: ''
})

const logDialogVisible = ref(false)
const logs = ref([])

const platformHint = computed(() => {
  if (shopForm.platform === 'local-shop') {
    return 'LocalShop 是内建免费测试平台，零配置即时开通，无需任何凭证。数据持久化到本地 SQLite，返回真实商品 ID 和消息 ID。'
  }
  if (shopForm.platform === 'amazon') {
    return 'Amazon SP-API 需填写：seller_id, refresh_token, client_id, client_secret, aws_access_key, aws_secret_key, role_arn, marketplace_id, region(na/eu/fe)'
  }
  if (shopForm.platform === 'ebay') {
    return 'eBay（免费 Sandbox）需填写：client_id, client_secret（开发者后台 Application Keys），user_token（OAuth Token Generator 生成），marketplace_id 默认 EBAY_US，sandbox 默认 true，category_id 可选'
  }
  return 'Temu 开放平台需填写：app_key, app_secret, access_token, region'
})

const defaultCredentials = computed(() => {
  if (shopForm.platform === 'local-shop') {
    return { mock: false, platform: 'local-shop' }
  }
  if (shopForm.platform === 'amazon') {
    return {
      seller_id: '', refresh_token: '', client_id: '', client_secret: '',
      aws_access_key: '', aws_secret_key: '', role_arn: '',
      marketplace_id: 'ATVPDKIKX0DER', region: 'na', mock: true
    }
  }
  if (shopForm.platform === 'ebay') {
    return {
      client_id: '', client_secret: '', user_token: '',
      marketplace_id: 'EBAY_US', sandbox: true, category_id: '30022', mock: true
    }
  }
  return { app_key: '', app_secret: '', access_token: '', region: 'global', mock: true }
})

function statusText(status) {
  const map = { active: '正常', inactive: '禁用', error: '错误', pending: '待测' }
  return map[status] || status
}
function statusClass(status) {
  if (status === 'active') return 'text-emerald-600 font-semibold'
  if (status === 'error') return 'text-red-600 font-semibold'
  return 'text-slate-500'
}

async function loadShops() {
  loading.value = true
  try {
    const res = await platformAPI.list()
    shops.value = (res.data.data || []).map(s => ({ ...s, testing: false, syncingProducts: false, syncingMessages: false }))
  } catch (e) {
    ElMessage.error('加载店铺失败')
  } finally {
    loading.value = false
  }
}

function resetEbayCreds(creds = {}) {
  ebayCreds.client_id = creds.client_id || ''
  ebayCreds.client_secret = creds.client_secret || ''
  ebayCreds.dev_id = creds.dev_id || ''
  ebayCreds.user_token = creds.user_token || ''
  ebayCreds.marketplace_id = creds.marketplace_id || 'EBAY_US'
  ebayCreds.sandbox = creds.sandbox !== false
  ebayCreds.category_id = creds.category_id || '30022'
}

function openCreate() {
  isEdit.value = false
  currentShopId.value = null
  shopForm.platform = 'local-shop'
  shopForm.name = ''
  shopForm.region = 'global'
  shopForm.mock = false
  shopForm.status = 'active'
  credentialsJson.value = JSON.stringify(defaultCredentials.value, null, 2)
  resetEbayCreds()
  shopDialogVisible.value = true
}

async function openEdit(row) {
  isEdit.value = true
  currentShopId.value = row.id
  shopForm.platform = row.platform
  shopForm.name = row.name
  shopForm.region = row.region || ''
  shopForm.status = row.status || 'active'
  // 获取完整凭证（列表接口只返回脱敏摘要 ***）
  try {
    const res = await platformAPI.get(row.id)
    const fullShop = res.data.data
    const creds = fullShop.credentials || defaultCredentials.value
    credentialsJson.value = JSON.stringify(creds, null, 2)
    if (row.platform === 'ebay') {
      resetEbayCreds(creds)
    }
  } catch (e) {
    ElMessage.warning('获取完整凭证失败，使用默认模板')
    credentialsJson.value = JSON.stringify(defaultCredentials.value, null, 2)
    resetEbayCreds()
  }
  shopDialogVisible.value = true
}

async function saveShop() {
  saving.value = true
  try {
    let credentials = {}
    if (shopForm.platform === 'ebay') {
      // eBay 从分字段构建 JSON
      credentials = {
        client_id: ebayCreds.client_id,
        client_secret: ebayCreds.client_secret,
        dev_id: ebayCreds.dev_id,
        user_token: ebayCreds.user_token,
        marketplace_id: ebayCreds.marketplace_id,
        sandbox: ebayCreds.sandbox,
        category_id: ebayCreds.category_id,
        mock: !!shopForm.mock,
      }
    } else {
      try {
        credentials = JSON.parse(credentialsJson.value || '{}')
      } catch (e) {
        ElMessage.error('凭证 JSON 格式错误')
        saving.value = false
        return
      }
    }
    const payload = {
      platform: shopForm.platform,
      name: shopForm.name,
      region: shopForm.region,
      credentials,
      mock: !!shopForm.mock,
      status: shopForm.status
    }
    if (isEdit.value) {
      await platformAPI.update(currentShopId.value, payload)
    } else {
      await platformAPI.create(payload)
    }
    ElMessage.success('保存成功')
    shopDialogVisible.value = false
    await loadShops()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.message || e.message))
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm('确认删除该店铺？', '提示', { type: 'warning' })
    await platformAPI.remove(row.id)
    ElMessage.success('删除成功')
    await loadShops()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function testConnection(row) {
  row.testing = true
  try {
    const res = await platformAPI.test(row.id)
    ElMessage.success(res.data.data?.message || '连接成功')
    await loadShops()
  } catch (e) {
    ElMessage.error('连接失败：' + (e.response?.data?.message || e.message))
  } finally {
    row.testing = false
  }
}

async function syncProducts(row) {
  row.syncingProducts = true
  try {
    const res = await platformAPI.syncProducts(row.id)
    ElMessage.success(`同步成功：${(res.data.data || []).length} 个商品`)
  } catch (e) {
    ElMessage.error('同步失败：' + (e.response?.data?.message || e.message))
  } finally {
    row.syncingProducts = false
  }
}

async function syncMessages(row) {
  row.syncingMessages = true
  try {
    const res = await platformAPI.syncMessages(row.id)
    ElMessage.success(`同步成功：${(res.data.data?.messages || []).length} 条消息`)
  } catch (e) {
    ElMessage.error('同步失败：' + (e.response?.data?.message || e.message))
  } finally {
    row.syncingMessages = false
  }
}

function openPublish(row) {
  currentPublishShop.value = row
  publishForm.sku = ''
  publishForm.title = ''
  publishForm.bullet_points = []
  publishForm.description = ''
  publishForm.price = 0
  publishForm.stock = 0
  publishForm.product_type = ''
  bulletInput.value = ''
  publishDialogVisible.value = true
}

async function publish() {
  publishing.value = true
  try {
    publishForm.bullet_points = bulletInput.value.split('\n').filter(s => s.trim())
    const res = await platformAPI.publishListing(currentPublishShop.value.id, publishForm)
    ElMessage.success(res.data.data?.message || '上架提交成功')
    publishDialogVisible.value = false
  } catch (e) {
    ElMessage.error('上架失败：' + (e.response?.data?.message || e.message))
  } finally {
    publishing.value = false
  }
}

function openSendMessage(row) {
  currentMessageShop.value = row
  messageForm.order_id = ''
  messageForm.buyer_id = ''
  messageForm.text = ''
  messageDialogVisible.value = true
}

async function sendMessage() {
  sendingMessage.value = true
  try {
    const res = await platformAPI.sendMessage(currentMessageShop.value.id, messageForm)
    ElMessage.success(res.data.data?.message_id ? '发送成功' : '发送提交成功')
    messageDialogVisible.value = false
  } catch (e) {
    ElMessage.error('发送失败：' + (e.response?.data?.message || e.message))
  } finally {
    sendingMessage.value = false
  }
}

async function viewLogs(row) {
  try {
    const res = await platformAPI.logs(row.id)
    logs.value = res.data.data || []
    logDialogVisible.value = true
  } catch (e) {
    ElMessage.error('加载日志失败')
  }
}

// 监听平台切换，自动填充默认凭证
watch(() => shopForm.platform, (newPlat, oldPlat) => {
  if (newPlat === 'ebay') {
    const defs = defaultCredentials.value
    ebayCreds.client_id = defs.client_id || ''
    ebayCreds.client_secret = defs.client_secret || ''
    ebayCreds.user_token = defs.user_token || ''
    ebayCreds.marketplace_id = defs.marketplace_id || 'EBAY_US'
    ebayCreds.sandbox = defs.sandbox !== false
    ebayCreds.category_id = defs.category_id || '30022'
  }
})

onMounted(loadShops)
</script>
