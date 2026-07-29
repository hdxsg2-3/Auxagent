import { reactive, readonly } from 'vue'
import { universalAPI, platformAPI } from '../api/client.js'

// 全局演示状态——切换页面时不会丢失
const state = reactive({
  // 演示状态
  demoRunning: false,
  demoReport: null,
  demoError: null,
  demoConfig: {
    platform: 'local-shop',
    method: 'adapter',
    productSource: 'ai',
  },

  // 浏览器自动化状态
  browserPlatform: 'amazon',
  browserDetail: null,
  browserExecuting: null,
  browserResult: null,

  // 通用状态
  loading: false,
  statusData: null,
  shops: [],
})

export const demoStore = {
  // 只读状态（用于模板展示）
  get state() {
    return readonly(state)
  },
  // 可写配置（用于 v-model 双向绑定）
  get config() {
    return state.demoConfig
  },

  // 初始化加载
  async loadStatus() {
    state.loading = true
    try {
      const [statusRes, shopsRes] = await Promise.all([
        universalAPI.status(),
        platformAPI.list()
      ])
      state.statusData = statusRes.data.data
      state.shops = shopsRes.data.data || []
    } catch (e) {
      console.error('加载状态失败:', e)
      throw e
    } finally {
      state.loading = false
    }
  },

  // 加载浏览器自动化状态
  async loadBrowserStatus() {
    try {
      const res = await universalAPI.browserFallbackStatus(state.browserPlatform)
      state.browserDetail = res.data.data
    } catch (e) {
      console.error('加载浏览器自动化状态失败:', e)
      throw e
    }
  },

  // 创建演示店铺
  async createDemoShop() {
    const res = await universalAPI.createDemoShop({
      name: 'LocalShop 演示店铺',
      region: 'global'
    })
    await this.loadStatus()
    return res.data
  },

  // 运行全自动演示
  async runAutoDemo() {
    if (state.demoRunning) return
    state.demoRunning = true
    state.demoReport = null
    state.demoError = null
    try {
      const payload = {
        platform: state.demoConfig.platform,
        use_browser_fallback: state.demoConfig.method === 'browser',
      }
      if (state.demoConfig.productSource === 'default') {
        payload.product_info = {
          sku: `DEMO-${Date.now()}`,
          title: 'Premium Wireless Bluetooth Earbuds with Active Noise Cancellation',
          bullet_points: [
            'Active noise cancellation up to 35dB',
            'Bluetooth 5.3 for stable connection',
            '36-hour battery life with charging case',
            'IPX5 water resistant for workouts',
            'Touch controls with voice assistant',
          ],
          description: 'Experience premium sound quality with ANC. 36 hours total playtime.',
          price: 39.99,
          stock: 200,
          product_type: 'ELECTRONICS',
        }
      }
      const res = await universalAPI.autoDemo(payload)
      state.demoReport = res.data.data
      return { success: true, data: res.data }
    } catch (e) {
      state.demoError = e.response?.data?.message || e.message
      return { success: false, error: state.demoError }
    } finally {
      state.demoRunning = false
    }
  },

  // 执行浏览器自动化
  async executeBrowserFallback(action, payload) {
    state.browserExecuting = action
    state.browserResult = null
    try {
      const res = await universalAPI.browserFallbackExecute({
        platform: state.browserPlatform,
        action,
        payload,
      })
      state.browserResult = res.data.data
      return { success: true, data: res.data }
    } catch (e) {
      return { success: false, error: e.response?.data?.message || e.message }
    } finally {
      state.browserExecuting = null
    }
  },

  // 更新配置
  updateDemoConfig(config) {
    Object.assign(state.demoConfig, config)
  },
  setBrowserPlatform(platform) {
    state.browserPlatform = platform
  },
}
