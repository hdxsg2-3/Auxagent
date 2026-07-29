/**
 * 品类与文案风格记忆模块
 * - 自动记录每次生成的商品品类和文案风格特征
 * - 本地持久化（localStorage），刷新不丢失
 * - 智能推荐：根据历史品类匹配度推荐过往风格
 */

const STORAGE_KEY = 'cross_border_style_memory'
const MAX_RECORDS = 200

// ---------- 品类关键词库（用于从产品描述中提取品类） ----------
const CATEGORY_KEYWORDS = [
  { name: '电子产品', keywords: ['充电宝', '耳机', '蓝牙', '数据线', '充电器', '音箱', '手机壳', '手机膜', '手表', '手环', '电子', '电池', 'USB', 'Type-C', 'Lightning', '无线充', '移动电源', '智能', '数码'] },
  { name: '家居用品', keywords: ['家居', '收纳', '置物架', '挂钩', '地毯', '窗帘', '抱枕', '靠垫', '桌布', '花瓶', '装饰', '灯具', '蜡烛', '香薰', '相框', '挂画', '摆件'] },
  { name: '厨房用品', keywords: ['厨房', '锅', '碗', '筷子', '勺子', '杯子', '水壶', '保鲜盒', '砧板', '刀具', '围裙', '抹布', '洗碗', '调料', '榨汁', '咖啡'] },
  { name: '服装配饰', keywords: ['衣服', '裤子', '裙子', '外套', '夹克', 'T恤', '衬衫', '帽子', '围巾', '手套', '袜子', '腰带', '包包', '背包', '手提包', '钱包', '首饰', '项链', '手链', '耳环', '戒指'] },
  { name: '美妆个护', keywords: ['化妆', '护肤', '面膜', '精华', '乳液', '面霜', '防晒', '口红', '眼影', '粉底', '洗发', '沐浴', '身体乳', '香水', '美容', '美甲', '梳子', '镜子'] },
  { name: '运动户外', keywords: ['运动', '健身', '瑜伽', '跑步', '骑行', '游泳', '户外', '露营', '帐篷', '登山', '徒步', '钓鱼', '球', '哑铃', '跳绳', '护具'] },
  { name: '母婴用品', keywords: ['婴儿', '宝宝', '奶瓶', '奶粉', '尿不湿', '玩具', '童车', '童床', '孕妇', '哺乳', '辅食', '围兜', '睡袋', '早教'] },
  { name: '宠物用品', keywords: ['宠物', '猫', '狗', '猫粮', '狗粮', '猫砂', '牵引绳', '宠物窝', '宠物玩具', '宠物梳', '喂食器'] },
  { name: '办公文具', keywords: ['办公', '文具', '笔', '笔记本', '文件夹', '书签', '便签', '胶带', '剪刀', '订书机', '计算器', '鼠标垫', '台灯'] },
  { name: '汽车用品', keywords: ['汽车', '车载', '车充', '手机支架', '座垫', '脚垫', '方向盘', '遮阳', '洗车', '车蜡', '行车记录', '车贴'] },
  { name: '食品饮料', keywords: ['食品', '零食', '饮料', '茶', '咖啡', '巧克力', '糖果', '饼干', '坚果', '干货', '调味', '保健品'] },
  { name: '玩具礼品', keywords: ['玩具', '礼品', '礼物', '公仔', '积木', '拼图', '模型', '手办', '桌游', '遥控', '泡泡', '派对'] },
]

// ---------- 风格特征提取 ----------
function extractCategory(productDesc) {
  if (!productDesc) return '其他'
  const text = productDesc.toLowerCase()
  for (const cat of CATEGORY_KEYWORDS) {
    for (const kw of cat.keywords) {
      if (text.includes(kw.toLowerCase())) {
        return cat.name
      }
    }
  }
  return '其他'
}

function extractStyleFeatures(result) {
  const features = {}
  if (!result) return features

  // 标题长度风格
  const titleLen = (result.title || '').length
  if (titleLen < 40) features.title_style = '简洁'
  else if (titleLen < 80) features.title_style = '适中'
  else features.title_style = '详细'

  // 卖点数量风格
  const bpCount = (result.bullet_points || []).length
  features.bullet_count = bpCount

  // 描述长度风格
  const descLen = (result.description || '').length
  if (descLen < 100) features.desc_style = '简短'
  else if (descLen < 300) features.desc_style = '适中'
  else features.desc_style = '详细'

  // 是否包含合规改写
  features.has_compliance = !!(result.compliance && result.compliance.rewritten)

  return features
}

// ---------- 记忆存储 ----------
function loadAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveAll(records) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(records))
  } catch (e) {
    console.error('保存风格记忆失败:', e)
  }
}

// ---------- 对外 API ----------
export const styleMemory = {
  /**
   * 记录一次文案生成
   * @param {object} params
   * @param {string} params.productDesc - 产品描述
   * @param {string} params.platform - 目标平台
   * @param {string} params.language - 目标语言
   * @param {object} params.result - 生成结果对象
   * @param {string} params.mode - 'manual' | 'link'
   */
  record(params) {
    const { productDesc, platform, language, result, mode } = params
    const records = loadAll()

    const category = extractCategory(productDesc || '')
    const styleFeatures = extractStyleFeatures(result)

    const record = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      category,
      platform: platform || 'unknown',
      language: language || 'en',
      mode: mode || 'manual',
      styleFeatures,
      productDesc: (productDesc || '').slice(0, 100),
      title: (result?.title || '').slice(0, 80),
      created_at: new Date().toISOString(),
    }

    records.unshift(record)
    if (records.length > MAX_RECORDS) records.length = MAX_RECORDS
    saveAll(records)
    return record
  },

  /**
   * 获取所有记忆记录
   */
  getAll() {
    return loadAll()
  },

  /**
   * 清空所有记忆
   */
  clear() {
    localStorage.removeItem(STORAGE_KEY)
  },

  /**
   * 删除单条记录
   */
  remove(id) {
    const records = loadAll().filter(r => r.id !== id)
    saveAll(records)
  },

  /**
   * 根据品类推荐历史风格
   * @param {string} productDesc - 当前产品描述
   * @param {number} limit - 返回条数
   * @returns {Array} 按匹配度排序的历史记录
   */
  recommend(productDesc, limit = 5) {
    if (!productDesc) return []
    const records = loadAll()
    if (!records.length) return []

    const currentCategory = extractCategory(productDesc)

    // 按品类匹配度 + 时间排序
    const scored = records.map(r => ({
      ...r,
      score: r.category === currentCategory ? 10 : (r.category === '其他' ? 1 : 3),
    }))

    // 同品类内按时间倒序
    scored.sort((a, b) => {
      if (a.score !== b.score) return b.score - a.score
      return new Date(b.created_at) - new Date(a.created_at)
    })

    return scored.slice(0, limit)
  },

  /**
   * 获取品类统计
   */
  getCategoryStats() {
    const records = loadAll()
    const stats = {}
    for (const r of records) {
      stats[r.category] = (stats[r.category] || 0) + 1
    }
    return Object.entries(stats)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
  },

  /**
   * 获取总记录数
   */
  getCount() {
    return loadAll().length
  },

  /**
   * 从产品描述中提取品类（供外部使用）
   */
  extractCategory,
}