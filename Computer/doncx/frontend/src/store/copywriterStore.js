/**
 * 文案生成全局 Store
 * 目的：切换页面后生成仍在后台继续，回来时能看到进度和结果（不会因组件卸载而取消）
 */
import { reactive, readonly } from 'vue'
import { copywriterAPI, autoListingAPI } from '../api/client'

const state = reactive({
  // 手动输入模式
  manualLoading: false,
  manualForm: { product_desc: '', platform: 'amazon', target_language: 'en' },
  manualResult: null,
  manualError: null,

  // 链接一键生成模式
  linkLoading: false,
  linkUrl: '',
  linkResult: null,
  linkError: null,
})

export const copywriterStore = {
  state: readonly(state),

  // --- 手动输入模式 ---
  async generateCopy(form) {
    if (state.manualLoading) return { success: false, error: '正在生成中，请稍候' }
    state.manualLoading = true
    state.manualForm = { ...form }
    state.manualResult = null
    state.manualError = null
    try {
      const res = await copywriterAPI.generate(form)
      state.manualResult = res.data.data
      return { success: true, data: res.data }
    } catch (e) {
      state.manualError = e.response?.data?.message || e.message || '生成失败'
      return { success: false, error: state.manualError }
    } finally {
      state.manualLoading = false
    }
  },

  clearManualResult() {
    state.manualResult = null
    state.manualError = null
  },

  // 更新手动模式结果（用于合规扫描等组件内追加操作）
  updateManualResult(updated) {
    state.manualResult = updated
  },

  // 切换语言翻译（复用当前 result）
  async translateCopy(data) {
    if (state.manualLoading) return { success: false, error: '正在生成中，请稍候' }
    state.manualLoading = true
    try {
      const res = await copywriterAPI.translate(data)
      state.manualResult = res.data.data
      return { success: true, data: res.data }
    } catch (e) {
      state.manualError = e.response?.data?.message || e.message || '翻译失败'
      return { success: false, error: state.manualError }
    } finally {
      state.manualLoading = false
    }
  },

  // --- 链接一键生成模式 ---
  async generateFromLink(url) {
    if (state.linkLoading) return { success: false, error: '正在生成中，请稍候' }
    state.linkLoading = true
    state.linkUrl = url
    state.linkResult = null
    state.linkError = null
    try {
      const res = await autoListingAPI.generate({ url })
      state.linkResult = res.data.data
      return { success: true, data: res.data }
    } catch (e) {
      state.linkError = e.response?.data?.message || e.message || '生成失败'
      return { success: false, error: state.linkError }
    } finally {
      state.linkLoading = false
    }
  },

  clearLinkResult() {
    state.linkResult = null
    state.linkError = null
  },

  // 从历史记录恢复结果
  restoreManualResult(data) {
    state.manualResult = data
    state.manualError = null
    state.manualLoading = false
  },

  restoreLinkResult(data) {
    state.linkResult = data
    state.linkError = null
    state.linkLoading = false
  },
}
