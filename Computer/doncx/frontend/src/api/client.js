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
    return api.post('/copywriter/generate', data)
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
  }
}
