import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const copywriterAPI = {
  generate(data) {
    // 文案生成含 LLM 调用 + 合规扫描，给足超时时间
    return api.post('/copywriter/generate', data, { timeout: 600000 })
  },
  translate(data) {
    return api.post('/copywriter/translate', data)
  }
}

export const autoListingAPI = {
  generate(data) {
    // 全自动链路含多次模型调用，给足超时时间
    return api.post('/auto-listing/generate', data, { timeout: 600000 })
  }
}

export const complianceAPI = {
  scan(data) {
    return api.post('/compliance/scan', data)
  },
  analyzeImage(data) {
    return api.post('/compliance/analyze-image', data)
  }
}

export const customerServiceAPI = {
  process(data) {
    return api.post('/customer-service/process', data)
  }
}

export const legalAPI = {
  search(data) {
    return api.post('/legal/search', data)
  }
}

export const logisticsAPI = {
  generate(data) {
    return api.post('/logistics/generate', data)
  },
  listDocuments() {
    return api.get('/logistics/documents')
  },
  getDocument(id) {
    return api.get(`/logistics/documents/${id}`)
  },
  updateStatus(id, data) {
    return api.post(`/logistics/documents/${id}/status`, data)
  },
  listTracking(id) {
    return api.get(`/logistics/documents/${id}/tracking`)
  },
  addTracking(id, data) {
    return api.post(`/logistics/documents/${id}/tracking`, data)
  }
}

export const dashboardAPI = {
  getStats() {
    return api.get('/dashboard/stats')
  },
  getActivity() {
    return api.get('/dashboard/activity')
  }
}

export const batchAPI = {
  generate(data) {
    return api.post('/batch/generate', data)
  },
  complianceScan(data) {
    return api.post('/batch/compliance-scan', data)
  }
}

export const keywordAPI = {
  suggest(data) {
    return api.post('/keyword-research/suggest', data)
  },
  optimize(data) {
    return api.post('/keyword-research/optimize-title', data)
  }
}

export const settingsAPI = {
  get() {
    return api.get('/settings')
  },
  update(data) {
    return api.post('/settings/update', data)
  }
}

// ---------------- 使用记录（后端持久化） ----------------
export const copywriterHistoryAPI = {
  list() {
    return api.get('/copywriter/history')
  },
  add(data) {
    return api.post('/copywriter/history', data)
  },
  remove(id) {
    return api.delete(`/copywriter/history/${id}`)
  },
  clear() {
    return api.delete('/copywriter/history')
  }
}

export const complianceHistoryAPI = {
  list() {
    return api.get('/compliance/history')
  },
  add(data) {
    return api.post('/compliance/history', data)
  },
  remove(id) {
    return api.delete(`/compliance/history/${id}`)
  },
  clear() {
    return api.delete('/compliance/history')
  }
}

export const customerServiceMessagesAPI = {
  list() {
    return api.get('/customer-service/messages')
  },
  add(data) {
    return api.post('/customer-service/messages', data)
  },
  update(id, data) {
    return api.put(`/customer-service/messages/${id}`, data)
  },
  remove(id) {
    return api.delete(`/customer-service/messages/${id}`)
  },
  clear() {
    return api.delete('/customer-service/messages')
  }
}

// ---------------- RAG 知识库管理 ----------------
export const customerServiceKnowledgeAPI = {
  list() {
    return api.get('/customer-service/knowledge')
  },
  add(data) {
    return api.post('/customer-service/knowledge', data)
  },
  get(id) {
    return api.get(`/customer-service/knowledge/${id}`)
  },
  update(id, data) {
    return api.put(`/customer-service/knowledge/${id}`, data)
  },
  remove(id) {
    return api.delete(`/customer-service/knowledge/${id}`)
  },
  embed(id) {
    return api.post(`/customer-service/knowledge/${id}/embed`)
  }
}

// ---------------- 对话记忆管理 ----------------
export const customerServiceMemoryAPI = {
  list() {
    return api.get('/customer-service/memory')
  },
  clear() {
    return api.delete('/customer-service/memory')
  }
}

// ---------------- 客服调用历史记录 ----------------
export const customerServiceHistoryAPI = {
  list() {
    return api.get('/customer-service/history')
  },
  clear() {
    return api.delete('/customer-service/history')
  }
}

// ---------------- 多平台店铺 API 对接 ----------------
export const platformAPI = {
  list() {
    return api.get('/platforms/shops')
  },
  get(id) {
    return api.get(`/platforms/shops/${id}`)
  },
  create(data) {
    return api.post('/platforms/shops', data)
  },
  update(id, data) {
    return api.put(`/platforms/shops/${id}`, data)
  },
  remove(id) {
    return api.delete(`/platforms/shops/${id}`)
  },
  test(id) {
    return api.post(`/platforms/shops/${id}/test`)
  },
  syncProducts(id) {
    return api.post(`/platforms/shops/${id}/sync-products`)
  },
  syncMessages(id) {
    return api.post(`/platforms/shops/${id}/sync-messages`)
  },
  publishListing(id, data) {
    return api.post(`/platforms/shops/${id}/publish-listing`, data)
  },
  sendMessage(id, data) {
    return api.post(`/platforms/shops/${id}/send-message`, data)
  },
  logs(id) {
    return api.get(`/platforms/shops/${id}/logs`)
  },
  // Listing 管理中心
  getListings(shopId) {
    return api.get('/platforms/listings', { params: { shop_id: shopId } })
  },
  getListing(id) {
    return api.get(`/platforms/listings/${id}`)
  },
  updateListing(id, data) {
    return api.put(`/platforms/listings/${id}`, data)
  },
  deleteListing(id) {
    return api.delete(`/platforms/listings/${id}`)
  }
}

// ---------------- 通用店铺自动对接模块 ----------------
export const universalAPI = {
  // 获取全局状态（支持的平台、浏览器自动化状态等）
  status() {
    return api.get('/universal-integration/status')
  },
  // 一键创建 LocalShop 演示店铺（零配置即时开通）
  createDemoShop(data = {}) {
    return api.post('/universal-integration/create-demo-shop', data)
  },
  // 浏览器自动化兜底状态查询
  browserFallbackStatus(platform = 'amazon') {
    return api.get(`/universal-integration/browser-fallback/status?platform=${platform}`)
  },
  // 浏览器自动化执行操作
  browserFallbackExecute(data) {
    return api.post('/universal-integration/browser-fallback/execute', data)
  },
  // 全自动演示：一键完成上架 + 消息收发全链路
  autoDemo(data = {}) {
    return api.post('/universal-integration/auto-demo', data, { timeout: 300000 })
  },
  // 查看 LocalShop 店铺商品
  localShopProducts(shopId) {
    return api.get(`/universal-integration/local-shop/products/${shopId}`)
  },
  // 查看 LocalShop 店铺统计
  localShopStats(shopId) {
    return api.get(`/universal-integration/local-shop/stats/${shopId}`)
  }
}
