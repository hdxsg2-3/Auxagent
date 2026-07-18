# 多语种跨境电商小卖家运营 Agent - 技术开发指南

## 1. 项目概述

### 1.1 项目背景
面向深圳跨境小商家，提供一站式多语种跨境电商运营解决方案。针对深圳外贸产业环境特点，聚焦产品文案多语种翻译、海外平台合规审查、海外当地法律法规检索、客户纠纷自动回复、货代物流单据生成等核心需求。

### 1.2 目标用户
- 深圳及珠三角地区跨境电商小卖家
- 亚马逊/eBay/速卖通等平台商家
- 年营业额 100 万 - 5000 万人民币的中小型外贸企业

### 1.3 核心价值
- 降低跨境电商运营门槛，减少人力成本
- 提升商品上架效率，缩短新品上市周期
- 降低合规风险，避免店铺被封或罚款
- 提升客户服务响应速度，优化购物体验

---

## 2. 功能需求分析

### 2.1 多语种文案生成智能体

#### 2.1.1 功能描述
用户输入中文产品描述，系统自动生成符合目标电商平台规则的多语种商品文案。

#### 2.1.2 核心功能
| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 中文输入 | 用户输入中文产品描述（如：白色2万毫安充电宝，带数显） | P0 |
| 平台规则适配 | 自动适配亚马逊/eBay/速卖通等平台规则 | P0 |
| 英文标题生成 | 根据产品描述生成符合平台规范的英文标题 | P0 |
| 卖点生成 | 生成 5 条核心卖点（Bullet Points） | P0 |
| 商品详情生成 | 生成详细的商品描述（长详情） | P0 |
| 一键翻译 | 支持翻译成西语、德语、法语等目标语言 | P0 |
| 复制粘贴 | 一键复制生成的文案，直接粘贴上架店铺 | P0 |
| 模板管理 | 支持自定义文案模板 | P2 |

#### 2.1.3 输入输出示例

**输入：**
```
白色2万毫安充电宝，带数显
```

**输出（英文）：**
```
Title: 20000mAh Portable Power Bank with LED Display - White

Bullet Points:
1. 20000mAh large capacity, charges iPhone 14 over 5 times
2. LED digital display shows real-time remaining power
3. Dual USB output ports, charge two devices simultaneously
4. Smart chip protection against overcharge, overdischarge, short circuit
5. Slim and portable design, perfect for travel and daily use

Description:
Our 20000mAh Portable Power Bank is the perfect companion for your on-the-go lifestyle...
```

**输出（西班牙语）：**
```
Título: Banco de energía portátil de 20000mAh con pantalla LED - Blanco

Puntos destacados:
1. Gran capacidad de 20000mAh...
```

### 2.2 合规风控审查智能体

#### 2.2.1 功能描述
对生成或已有的商品文案进行合规审查，提前发现潜在风险。采用**混合架构**：关键词规则匹配为主，LLM语义分析为辅，确保检测结果的准确性和可靠性。

#### 2.2.2 核心功能
| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 极限词检测 | 基于规则库精确匹配"最牛、第一、顶级"等违规词汇 | P0 |
| 品牌侵权检测 | 基于规则库精确匹配品牌名、卡通形象等版权风险词汇 | P0 |
| 违禁词预警 | 基于规则库精确匹配平台违禁类目词 | P0 |
| LLM语义分析 | 对模糊/歧义内容进行LLM语义分析，识别潜在风险 | P1 |
| 图片合规检测 | 检测图片是否侵犯版权或包含违规内容 | P1 |
| 审查报告生成 | 生成详细的合规审查报告 | P0 |
| 风险等级评估 | 对审查结果进行风险等级评估（高/中/低） | P0 |
| 整改建议 | 根据检测结果提供整改建议 | P0 |
| 规则库管理 | 支持自定义添加、编辑、删除合规规则 | P1 |

#### 2.2.3 审查维度
```
审查类型          检测内容                              风险等级    检测方式
──────────────────────────────────────────────────────────────────────────
极限词检测        最牛、第一、顶级、最好、唯一、100%    高          规则匹配
品牌侵权检测      Apple、Nike、Disney等品牌名           高          规则匹配
卡通形象版权      米老鼠、Hello Kitty等卡通形象        高          规则匹配
违禁类目词        武器、毒品、医疗设备等敏感词汇        高          规则匹配
平台特定规则      各平台独有的违禁词规则                中          规则匹配
广告法合规        虚假宣传、误导性描述                  中          LLM语义分析
模糊表述检测      "大概、可能、差不多"等模糊描述        低          LLM语义分析
```

#### 2.2.4 审查流程（混合架构）
```
输入文案
    │
    ▼
┌─────────────────────────────────────┐
│ 第一步：规则库精确匹配              │
│  - 极限词匹配                       │
│  - 品牌名匹配                       │
│  - 违禁词匹配                       │
│  - 平台规则匹配                     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 第二步：LLM语义分析（仅对模糊内容）  │
│  - 检测虚假宣传                     │
│  - 检测误导性描述                   │
│  - 检测模糊表述                     │
│  - 提供整改建议                     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 第三步：结果汇总                    │
│  - 合并规则匹配和LLM分析结果         │
│  - 评估风险等级                     │
│  - 生成审查报告                     │
└─────────────────────────────────────┘
```

### 2.3 海外客服自动应答智能体

#### 2.3.1 功能描述
自动处理海外客户的英文咨询，按店铺预设规则自动回复，复杂问题推送人工处理。支持**Webhook实时接收**和**定时轮询**两种消息接收机制。

#### 2.3.2 核心功能
| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 多语言理解 | 自动识别并理解英文客户咨询 | P0 |
| 自动回复 | 按预设规则自动生成回复内容 | P0 |
| 问题分类 | 自动分类客户问题类型（物流、退货、售后等） | P0 |
| 规则配置 | 支持店铺自定义回复规则和模板 | P0 |
| 人工转接 | 复杂问题自动推送人工处理 | P0 |
| 回复记录 | 记录所有客户咨询和回复历史 | P0 |
| 常见问题库 | 建立常见问题知识库 | P1 |
| Webhook接收 | 通过Webhook实时接收平台消息 | P1 |
| 定时轮询 | 定时调用平台API拉取未处理消息 | P1 |
| 消息推送 | 重要消息推送提醒到微信/邮件 | P2 |

#### 2.3.3 问题类型分类
```
问题类型        示例问题                                  处理方式
─────────────────────────────────────────────────────────────
物流查询        "How long will shipping take?"          自动回复
退货政策        "Can I return this item?"               自动回复
商品问题        "Is this compatible with iPhone 14?"    自动回复
少件投诉        "I received a missing item"             自动回复+预警
质量问题        "The product is defective"              转接人工
价格协商        "Can you give me a discount?"           转接人工
其他问题        无法识别的问题类型                        转接人工
```

#### 2.3.4 消息接收机制

**方式一：Webhook实时接收**（推荐）
```
平台消息 → Webhook通知 → 系统接收 → 自动处理 → 自动回复/转接人工
```

**方式二：定时轮询**（备用）
```
定时任务(每5-10分钟) → 调用平台API → 获取未处理消息 → 自动处理 → 自动回复/转接人工
```

**支持的平台对接方式**：
| 平台 | Webhook支持 | API轮询 | 官方SDK |
|------|-------------|---------|---------|
| 亚马逊 | 部分支持 | ✅ | Selling Partner API |
| eBay | ✅ | ✅ | Trading API |
| 速卖通 | ✅ | ✅ | Aliexpress API |

### 2.4 海外当地法律法规检索智能体

#### 2.4.1 功能描述
帮助卖家查询目标国家/地区的电商相关法律法规，了解当地合规要求，降低法律风险。采用**RAG（检索增强生成）架构**：LLM仅对已验证的法规文本进行总结和翻译，绝不从训练数据中生成法规内容，确保信息的准确性和权威性。

**重要声明**：系统提供的法规摘要仅供参考，不能替代专业法律意见。卖家在进行跨境贸易前应咨询专业律师。

#### 2.4.2 核心功能
| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 地区选择 | 支持选择目标国家/地区进行法规检索 | P0 |
| 法规分类 | 按类别检索（消费者权益、产品安全、数据隐私、税收等） | P0 |
| 关键词搜索 | 基于向量检索的关键词搜索特定法规条款 | P0 |
| 法规摘要 | LLM对已验证法规文本生成中文摘要 | P0 |
| 合规建议 | 根据检索结果提供合规建议和注意事项 | P0 |
| 历史记录 | 保存法规检索历史，方便查阅 | P1 |
| 法规更新提醒 | 重要法规更新时推送提醒 | P2 |
| 向量索引管理 | 法规文本向量化索引的构建和更新 | P1 |

#### 2.4.3 支持的国家/地区
| 地区 | 主要法规 |
|------|----------|
| 美国 | FTC Act、CPG、Prop 65、CCPA |
| 欧盟 | GDPR、消费者权益指令、产品安全法规 |
| 英国 | Consumer Rights Act、GDPR |
| 日本 | 消费者契约法、产品责任法 |
| 德国 | BGB、产品安全法 |
| 西班牙 | 消费者保护法、数据保护法 |

#### 2.4.4 法规分类
```
法规分类          覆盖内容
─────────────────────────────────
消费者权益保护    退货政策、退款规则、消费者权利
产品安全          产品认证、安全标准、警告标识
数据隐私          个人信息保护、数据跨境传输
税收合规          VAT/GST、进口关税、税务申报
广告合规          广告法、宣传规范、虚假广告
知识产权          商标、专利、版权保护
```

#### 2.4.5 RAG检索流程
```
用户查询（关键词/分类/地区）
        │
        ▼
┌─────────────────────────────────────┐
│ 第一步：向量检索                    │
│  - 将查询向量化                      │
│  - 在法规数据库中进行相似度检索       │
│  - 返回最相关的N条法规文本           │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 第二步：LLM总结（仅基于检索结果）    │
│  - 将检索到的法规文本作为上下文      │
│  - LLM生成中文摘要                  │
│  - LLM提供合规建议                  │
│  - 绝不从训练数据生成新法规          │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 第三步：结果输出                    │
│  - 展示法规原文链接                 │
│  - 展示中文摘要和合规建议            │
│  - 添加重要声明                     │
└─────────────────────────────────────┘
```

### 2.5 货代物流单据生成智能体

#### 2.5.1 功能描述
根据订单信息自动生成各类货代物流单据，支持打印和导出，适配深圳外贸产业环境。

#### 2.5.2 核心功能
| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| 商业发票生成 | 自动生成符合报关要求的商业发票 | P0 |
| 装箱单生成 | 自动生成装箱单，包含商品明细 | P0 |
| 报关单生成 | 自动生成报关单，支持常见贸易术语 | P0 |
| 提单信息生成 | 生成提单所需的货物信息 | P1 |
| 原产地证生成 | 生成原产地证书相关信息 | P1 |
| 批量生成 | 支持批量导入订单生成单据（支持Excel/CSV格式） | P0 |
| 模板自定义 | 支持自定义单据模板 | P2 |
| 导出打印 | 支持PDF导出和直接打印 | P0 |

#### 2.5.3 支持的单据类型
```
单据类型          用途                          格式
───────────────────────────────────────────────────
Commercial Invoice 商业发票，用于清关和结算      PDF
Packing List       装箱单，列明货物明细          PDF
Customs Declaration 报关单，申报货物信息        PDF
Bill of Lading Info 提单信息，运输凭证          PDF
Certificate of Origin 原产地证，证明产地        PDF
Proforma Invoice   形式发票，报价参考            PDF
```

#### 2.5.4 输入输出示例

**输入：**
```json
{
  "order_info": {
    "order_id": "ORD-2024-001",
    "buyer_name": "John Smith",
    "buyer_address": "123 Main St, New York, NY 10001",
    "seller_name": "深圳XX科技有限公司",
    "seller_address": "深圳市南山区科技园路88号",
    "goods": [
      {"name": "Power Bank", "quantity": 10, "unit_price": 25.00, "total_price": 250.00},
      {"name": "USB Cable", "quantity": 20, "unit_price": 5.00, "total_price": 100.00}
    ],
    "total_amount": 350.00,
    "currency": "USD",
    "trade_term": "FOB",
    "port_of_loading": "深圳盐田港",
    "port_of_discharge": "洛杉矶港"
  }
}
```

**输出：**
生成完整的商业发票、装箱单、报关单等PDF文件

### 2.6 大模型 API 接入

#### 2.6.1 功能描述
支持接入兼容 OpenAI 格式的大模型 API，实现智能化问答和文案生成。

#### 2.6.2 核心功能
| 功能点 | 描述 | 优先级 |
|--------|------|--------|
| API 配置 | 支持配置 API 密钥、接口地址、模型名称 | P0 |
| OpenAI 兼容 | 兼容 OpenAI API 格式 | P0 |
| 模型切换 | 支持切换不同的大模型 | P1 |
| 调用日志 | 记录 API 调用日志和消耗 | P1 |
| 成本控制 | 支持设置 API 调用限制和预算 | P2 |

---

## 3. UI 设计

### 3.1 设计原则
- **极简风格**：清晰的功能分区，减少操作步骤
- **移动端优先**：适配手机垂直屏幕，方便随时随地使用
- **高效便捷**：一键操作，减少重复输入
- **视觉反馈**：清晰的状态提示和操作反馈

### 3.2 页面结构

#### 3.2.1 首页/工作台
```
┌─────────────────────────────┐
│  跨境电商运营 Agent         │
├─────────────────────────────┤
│                             │
│  ┌─────────────┐ ┌─────────┐│
│  │ 文案生成     │ │ 合规审查 ││
│  │ (文案智能体)  │ │ (风控智能体)││
│  └─────────────┘ └─────────┘│
│                             │
│  ┌─────────────┐ ┌─────────┐│
│  │ 客服应答     │ │ 法规检索 ││
│  │ (客服智能体)  │ │ (法规智能体)││
│  └─────────────┘ └─────────┘│
│                             │
│  ┌─────────────┐ ┌─────────┐│
│  │ 物流单据     │ │ 设置    ││
│  │ (单据智能体)  │ │ (API配置) ││
│  └─────────────┘ └─────────┘│
└─────────────────────────────┘
```

#### 3.2.2 文案生成页面
```
┌─────────────────────────────┐
│  多语种文案生成              │
├─────────────────────────────┤
│                             │
│  输入中文产品描述：          │
│  ┌───────────────────────┐  │
│  │ [        输入框       ] │  │
│  └───────────────────────┘  │
│                             │
│  目标平台：                  │
│  [亚马逊] [eBay] [速卖通]    │
│                             │
│  目标语言：                  │
│  [英语] [西班牙语] [德语]    │
│                             │
│  [生成文案]                  │
│                             │
├─────────────────────────────┤
│  生成结果：                  │
│  ┌───────────────────────┐  │
│  │ 标题：XXX             │  │
│  │ 卖点：XXX             │  │
│  │ 详情：XXX             │  │
│  └───────────────────────┘  │
│                             │
│  [复制全部] [翻译其他语言]    │
└─────────────────────────────┘
```

#### 3.2.3 合规审查页面
```
┌─────────────────────────────┐
│  合规风控审查                │
├─────────────────────────────┤
│                             │
│  输入要审查的文案：          │
│  ┌───────────────────────┐  │
│  │ [        输入框       ] │  │
│  └───────────────────────┘  │
│                             │
│  上传图片（可选）：          │
│  [选择文件]                  │
│                             │
│  [开始审查]                  │
│                             │
├─────────────────────────────┤
│  审查结果：                  │
│                             │
│  🚫 高风险：                │
│  - "最牛" - 极限词违规      │
│                             │
│  ⚠️ 中风险：                │
│  - "Apple" - 品牌侵权风险   │
│                             │
│  ✅ 低风险：                │
│  - 无违禁类目词              │
│                             │
│  整改建议：XXX               │
└─────────────────────────────┘
```

#### 3.2.4 客服应答页面
```
┌─────────────────────────────┐
│  海外客服自动应答            │
├─────────────────────────────┤
│                             │
│  客户消息列表：              │
│  ┌───────────────────────┐  │
│  │ [1] English msg...    │  │
│  │ [2] English msg...    │  │
│  │ [3] English msg...    │  │
│  └───────────────────────┘  │
│                             │
│  选中消息详情：              │
│  ┌───────────────────────┐  │
│  │ Customer: How long... │  │
│  │ AI回复: Shipping...   │  │
│  │ Status: 已自动回复     │  │
│  └───────────────────────┘  │
│                             │
│  [查看历史] [配置规则]        │
└─────────────────────────────┘
```

#### 3.2.5 法规检索页面
```
┌─────────────────────────────┐
│  海外法律法规检索            │
├─────────────────────────────┤
│                             │
│  选择地区：                  │
│  [美国] [欧盟] [英国] [日本] │
│                             │
│  法规分类：                  │
│  [消费者权益] [产品安全]      │
│  [数据隐私] [税收合规]        │
│                             │
│  关键词搜索：                │
│  ┌───────────────────────┐  │
│  │ [        输入框       ] │  │
│  └───────────────────────┘  │
│                             │
│  [搜索法规]                  │
│                             │
├─────────────────────────────┤
│  检索结果：                  │
│  ┌───────────────────────┐  │
│  │ 法规名称：XXX          │  │
│  │ 生效日期：XXX          │  │
│  │ 摘要：XXX              │  │
│  │ 合规建议：XXX          │  │
│  └───────────────────────┘  │
│                             │
│  [查看详情] [保存到历史]      │
└─────────────────────────────┘
```

#### 3.2.6 物流单据页面
```
┌─────────────────────────────┐
│  货代物流单据生成            │
├─────────────────────────────┤
│                             │
│  选择单据类型：              │
│  [商业发票] [装箱单] [报关单] │
│                             │
│  导入订单：                  │
│  [选择文件]                  │
│                             │
│  手动填写：                  │
│  ┌───────────────────────┐  │
│  │ 订单号：[输入框]       │  │
│  │ 买家信息：[输入框]     │  │
│  │ 商品明细：[输入框]     │  │
│  └───────────────────────┘  │
│                             │
│  [生成单据]                  │
│                             │
├─────────────────────────────┤
│  生成结果：                  │
│  ┌───────────────────────┐  │
│  │ 商业发票.pdf          │  │
│  │ 装箱单.pdf            │  │
│  │ 报关单.pdf            │  │
│  └───────────────────────┘  │
│                             │
│  [导出全部] [打印]          │
└─────────────────────────────┘
```

#### 3.2.7 设置页面
```
┌─────────────────────────────┐
│  设置                        │
├─────────────────────────────┤
│                             │
│  API 配置：                  │
│  ┌───────────────────────┐  │
│  │ API密钥：[********]   │  │
│  │ 接口地址：[URL输入框] │  │
│  │ 模型名称：[选择框]     │  │
│  └───────────────────────┘  │
│                             │
│  [保存配置] [测试连接]        │
│                             │
├─────────────────────────────┤
│  店铺信息：                  │
│  ┌───────────────────────┐  │
│  │ 店铺名称：[输入框]     │  │
│  │ 主营类目：[选择框]     │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

### 3.3 交互设计要点

#### 3.3.1 文案生成流程
```
用户输入 → 选择平台 → 选择语言 → 点击生成 → 查看结果 → 复制/翻译
```

#### 3.3.2 合规审查流程
```
输入文案 → 上传图片 → 点击审查 → 查看风险等级 → 获取整改建议
```

#### 3.3.3 客服应答流程
```
接收消息 → 自动分类 → 匹配规则 → 自动回复 / 转接人工
```

#### 3.3.4 法规检索流程
```
选择地区 → 选择分类 → 输入关键词 → 搜索 → 查看摘要 → 获取合规建议
```

#### 3.3.5 物流单据流程
```
选择单据类型 → 导入/填写订单信息 → 生成单据 → 预览 → 导出/打印
```

---

## 4. 系统架构

### 4.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          前端层 (Web)                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│  │ 文案生成页面  │ │ 合规审查页面  │ │ 客服应答页面  │ │ 法规检索页面  ││
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘│
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│  ┌──────────────┐                                                   │
│  │ 物流单据页面  │                                                   │
│  └──────┬───────┘                                                   │
└─────────┼───────────────────────────────────────────────────────────┘
          │                │                │                │
┌─────────▼────────────────▼────────────────▼────────────────▼──────────┐
│                          后端层 (API)                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│  │ 文案生成API   │ │ 合规审查API   │ │ 客服应答API   │ │ 法规检索API   ││
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘│
│         │                │                │                │        │
│  ┌──────▼────────────────▼────────────────▼────────────────▼──────┐  │
│  │                      大模型集成服务                            │  │
│  │  - OpenAI兼容API调用                                        │  │
│  │  - Prompt模板管理                                          │  │
│  │  - 调用日志记录                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────┐                                                   │
│  │ 物流单据API   │                                                   │
│  └──────┬───────┘                                                   │
└─────────┼───────────────────────────────────────────────────────────┘
          │                │                │                │
┌─────────▼────────────────▼────────────────▼────────────────▼──────────┐
│                          数据层                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│  │ 文案模板库    │ │ 合规规则库    │ │ 客服知识库    │ │ 法规数据库    ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘│
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │ 单据模板库    │ │ 调用日志表    │ │ 用户配置表    │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 技术选型

| 层次 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| 前端框架 | Vue.js | 3.x | 轻量、响应式、生态成熟，适合快速开发 |
| UI 组件 | Element Plus | 2.x | Vue 3 兼容，组件丰富，中文文档完善 |
| 后端框架 | Flask | 2.x | 轻量、灵活，适合中小型项目快速开发 |
| 数据库 | PostgreSQL | 15.x | 支持并发写入，适合生产环境，客服消息实时处理 |
| API 集成 | OpenAI API | 兼容 | 用户要求兼容 OpenAI 格式的大模型接口 |
| PDF 生成 | WeasyPrint | 59.x | HTML转PDF，支持复杂布局，中文支持良好 |
| 向量检索 | FAISS | 1.7.x | 轻量高效的向量搜索引擎，支持RAG检索 |

### 4.3 模块划分

```
backend/
├── app.py                    # 应用入口
├── config.py                 # 配置管理
├── controllers/              # 控制器层
│   ├── copywriter.py         # 文案生成控制器
│   ├── compliance.py         # 合规审查控制器
│   ├── customer_service.py   # 客服应答控制器
│   ├── legal.py              # 法规检索控制器
│   ├── logistics.py          # 物流单据控制器
│   └── settings.py           # 设置控制器
├── services/                 # 服务层
│   ├── llm_service.py        # 大模型服务
│   ├── prompt_manager.py     # Prompt模板管理
│   ├── compliance_engine.py  # 合规审查引擎
│   ├── rule_engine.py        # 规则引擎
│   ├── legal_engine.py       # 法规检索引擎
│   └── document_engine.py    # 单据生成引擎
├── models/                   # 数据模型
│   ├── templates.py          # 文案模板模型
│   ├── rules.py              # 合规规则模型
│   ├── knowledge_base.py     # 知识库模型
│   ├── legal_db.py           # 法规数据库模型
│   ├── document_templates.py # 单据模板模型
│   ├── logs.py               # 日志模型
│   └── config.py             # 配置模型
└── utils/                    # 工具类
    ├── api_client.py         # API客户端
    ├── validator.py          # 数据验证
    ├── logger.py             # 日志工具
    ├── pdf_generator.py      # PDF生成工具
    └── vector_search.py      # 向量检索工具（FAISS）

frontend/
├── src/
│   ├── main.js               # 入口文件
│   ├── App.vue               # 根组件
│   ├── components/           # 组件
│   │   ├── Copywriter.vue    # 文案生成组件
│   │   ├── Compliance.vue    # 合规审查组件
│   │   ├── CustomerService.vue # 客服应答组件
│   │   ├── Legal.vue         # 法规检索组件
│   │   ├── Logistics.vue     # 物流单据组件
│   │   └── Settings.vue      # 设置组件
│   ├── api/                  # API调用
│   │   └── client.js         # API客户端
│   ├── store/                # 状态管理
│   │   └── index.js          # 全局状态
│   └── utils/                # 工具函数
│       └── helpers.js        # 通用辅助函数
├── index.html                # HTML模板
├── package.json              # 依赖配置
└── vite.config.js            # Vite配置
```

---

## 5. API 设计

### 5.1 文案生成 API

#### 5.1.1 生成文案
- **路径**: `POST /api/copywriter/generate`
- **描述**: 根据中文产品描述生成多语种商品文案

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| product_desc | string | 是 | 中文产品描述 |
| platform | string | 是 | 目标平台（amazon/ebay/aliexpress） |
| target_language | string | 是 | 目标语言（en/es/de/fr） |

**请求示例**:
```json
{
  "product_desc": "白色2万毫安充电宝，带数显",
  "platform": "amazon",
  "target_language": "en"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "title": "20000mAh Portable Power Bank with LED Display - White",
    "bullet_points": [
      "20000mAh large capacity, charges iPhone 14 over 5 times",
      "LED digital display shows real-time remaining power",
      "Dual USB output ports, charge two devices simultaneously",
      "Smart chip protection against overcharge, overdischarge, short circuit",
      "Slim and portable design, perfect for travel and daily use"
    ],
    "description": "Our 20000mAh Portable Power Bank is the perfect companion...",
    "platform": "amazon",
    "language": "en"
  }
}
```

#### 5.1.2 翻译文案
- **路径**: `POST /api/copywriter/translate`
- **描述**: 将已有文案翻译为目标语言

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| title | string | 是 | 标题 |
| bullet_points | array | 是 | 卖点列表 |
| description | string | 是 | 商品详情 |
| target_language | string | 是 | 目标语言（es/de/fr） |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "title": "Banco de energía portátil de 20000mAh con pantalla LED - Blanco",
    "bullet_points": [...],
    "description": "...",
    "language": "es"
  }
}
```

### 5.2 合规审查 API

#### 5.2.1 审查文案
- **路径**: `POST /api/compliance/scan`
- **描述**: 对文案进行合规审查

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| content | string | 是 | 要审查的文案内容 |
| platform | string | 是 | 目标平台 |
| images | array | 否 | 图片URL列表 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "overall_risk": "high",
    "issues": [
      {
        "type": "extreme_word",
        "level": "high",
        "content": "最牛",
        "suggestion": "建议替换为\"高品质\""
      },
      {
        "type": "trademark",
        "level": "high",
        "content": "Apple",
        "suggestion": "避免使用知名品牌名称"
      }
    ],
    "summary": "检测到2个高风险问题，建议修改后再上架"
  }
}
```

### 5.3 客服应答 API

#### 5.3.1 处理客户消息
- **路径**: `POST /api/customer_service/process`
- **描述**: 处理客户消息，生成自动回复

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| message | string | 是 | 客户消息内容 |
| message_id | string | 是 | 消息ID |
| platform | string | 是 | 消息来源平台 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "message_id": "msg_12345",
    "category": "shipping",
    "response": "Standard shipping takes 7-14 business days. Expedited shipping is available for faster delivery.",
    "status": "auto_replied",
    "confidence": 0.95
  }
}
```

#### 5.3.2 获取消息列表
- **路径**: `GET /api/customer_service/messages`
- **描述**: 获取客户消息列表

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| limit | int | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "messages": [...],
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

### 5.4 法规检索 API

#### 5.4.1 搜索法规
- **路径**: `POST /api/legal/search`
- **描述**: 根据地区、分类和关键词搜索法律法规

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| region | string | 是 | 目标地区（usa/eu/uk/japan/germany/spain） |
| category | string | 否 | 法规分类（consumer/product/privacy/tax/ad/ip） |
| keyword | string | 否 | 搜索关键词 |

**请求示例**:
```json
{
  "region": "usa",
  "category": "consumer",
  "keyword": "return policy"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "law_001",
        "title": "Federal Trade Commission Act",
        "category": "consumer",
        "region": "usa",
        "effective_date": "1914-09-26",
        "summary": "联邦贸易委员会法禁止不公平的商业行为和虚假广告...",
        "compliance_tips": [
          "确保退货政策清晰明确",
          "不得进行虚假或误导性宣传",
          "遵守消费者权益保护规定"
        ],
        "details_url": "https://www.ftc.gov/"
      }
    ],
    "total": 1
  }
}
```

#### 5.4.2 获取法规详情
- **路径**: `GET /api/legal/detail/{law_id}`
- **描述**: 获取法规详细信息

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "law_001",
    "title": "Federal Trade Commission Act",
    "category": "consumer",
    "region": "usa",
    "effective_date": "1914-09-26",
    "full_text": "...完整法规内容...",
    "summary": "...法规摘要...",
    "compliance_tips": [...],
    "related_laws": [...]
  }
}
```

#### 5.4.3 获取检索历史
- **路径**: `GET /api/legal/history`
- **描述**: 获取用户的法规检索历史

**响应示例**:
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "id": "hist_001",
        "region": "usa",
        "category": "consumer",
        "keyword": "return policy",
        "search_time": "2024-01-15 10:30:00"
      }
    ],
    "total": 10
  }
}
```

### 5.5 物流单据 API

#### 5.5.1 生成单据
- **路径**: `POST /api/logistics/generate`
- **描述**: 根据订单信息生成指定类型的单据（合并原5.5.1/5.5.2/5.5.3）

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| order_info | object | 是 | 订单信息对象 |
| document_type | string | 是 | 单据类型（commercial_invoice/packing_list/customs_declaration/bill_of_lading/certificate_of_origin/proforma_invoice） |

**请求示例**:
```json
{
  "document_type": "commercial_invoice",
  "order_info": {
    "order_id": "ORD-2024-001",
    "buyer_name": "John Smith",
    "buyer_address": "123 Main St, New York, NY 10001",
    "seller_name": "深圳XX科技有限公司",
    "seller_address": "深圳市南山区科技园路88号",
    "goods": [
      {"name": "Power Bank", "quantity": 10, "unit_price": 25.00, "total_price": 250.00},
      {"name": "USB Cable", "quantity": 20, "unit_price": 5.00, "total_price": 100.00}
    ],
    "total_amount": 350.00,
    "currency": "USD",
    "trade_term": "FOB",
    "port_of_loading": "深圳盐田港",
    "port_of_discharge": "洛杉矶港"
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "document_type": "commercial_invoice",
    "document_id": "INV-2024-001",
    "pdf_url": "/api/logistics/download/INV-2024-001",
    "generated_at": "2024-01-15 10:30:00"
  }
}
```

#### 5.5.2 批量生成单据（真正批量）
- **路径**: `POST /api/logistics/batch_generate`
- **描述**: 批量为多个订单生成多种单据

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| orders | array | 是 | 订单信息对象数组 |
| document_types | array | 是 | 要生成的单据类型列表 |

**请求示例**:
```json
{
  "orders": [
    {
      "order_id": "ORD-2024-001",
      "buyer_name": "John Smith",
      "buyer_address": "123 Main St, New York, NY 10001",
      "goods": [...],
      "total_amount": 350.00,
      "currency": "USD"
    },
    {
      "order_id": "ORD-2024-002",
      "buyer_name": "Alice Johnson",
      "buyer_address": "456 Oak Ave, Los Angeles, CA 90001",
      "goods": [...],
      "total_amount": 180.00,
      "currency": "USD"
    }
  ],
  "document_types": ["commercial_invoice", "packing_list", "customs_declaration"]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "order_id": "ORD-2024-001",
        "documents": [
          {"type": "commercial_invoice", "id": "INV-2024-001", "url": "/api/logistics/download/INV-2024-001"},
          {"type": "packing_list", "id": "PKL-2024-001", "url": "/api/logistics/download/PKL-2024-001"},
          {"type": "customs_declaration", "id": "CD-2024-001", "url": "/api/logistics/download/CD-2024-001"}
        ]
      },
      {
        "order_id": "ORD-2024-002",
        "documents": [
          {"type": "commercial_invoice", "id": "INV-2024-002", "url": "/api/logistics/download/INV-2024-002"},
          {"type": "packing_list", "id": "PKL-2024-002", "url": "/api/logistics/download/PKL-2024-002"},
          {"type": "customs_declaration", "id": "CD-2024-002", "url": "/api/logistics/download/CD-2024-002"}
        ]
      }
    ],
    "total_orders": 2,
    "total_documents": 6
  }
}
```

#### 5.5.3 下载单据
- **路径**: `GET /api/logistics/download/{document_id}`
- **描述**: 下载生成的单据 PDF 文件

### 5.6 设置 API

#### 5.6.1 保存配置
- **路径**: `POST /api/settings/save`
- **描述**: 保存系统配置

**请求参数**:
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| api_key | string | 是 | 大模型API密钥 |
| api_endpoint | string | 是 | API接口地址 |
| model_name | string | 是 | 模型名称 |
| shop_name | string | 否 | 店铺名称 |
| main_category | string | 否 | 主营类目 |

**响应示例**:
```json
{
  "success": true,
  "message": "配置保存成功"
}
```

#### 5.6.2 获取配置
- **路径**: `GET /api/settings/get`
- **描述**: 获取当前配置

**响应示例**:
```json
{
  "success": true,
  "data": {
    "api_key": "sk-***",
    "api_endpoint": "https://api.example.com/v1",
    "model_name": "gpt-4",
    "shop_name": "My Shop",
    "main_category": "Electronics"
  }
}
```

#### 5.6.3 测试连接
- **路径**: `POST /api/settings/test`
- **描述**: 测试大模型API连接

**响应示例**:
```json
{
  "success": true,
  "message": "API连接成功",
  "latency": 256
}
```

---

## 6. 数据库设计

### 6.1 数据库表结构

#### 6.1.1 文案模板表 (copywriter_templates)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 模板ID |
| platform | TEXT | NOT NULL | 目标平台 |
| language | TEXT | NOT NULL | 目标语言 |
| title_template | TEXT | NOT NULL | 标题模板 |
| bullet_template | TEXT | NOT NULL | 卖点模板 |
| description_template | TEXT | NOT NULL | 详情模板 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

#### 6.1.2 合规规则表 (compliance_rules)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 规则ID |
| rule_type | TEXT | NOT NULL | 规则类型（extreme_word/trademark/forbidden） |
| platform | TEXT | NOT NULL | 适用平台 |
| keyword | TEXT | NOT NULL | 关键词 |
| risk_level | TEXT | NOT NULL | 风险等级（high/medium/low） |
| suggestion | TEXT | | 整改建议 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

#### 6.1.3 客服知识库表 (knowledge_base)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 知识ID |
| category | TEXT | NOT NULL | 问题分类（shipping/return/product/other） |
| question | TEXT | NOT NULL | 常见问题 |
| answer | TEXT | NOT NULL | 标准回答 |
| keywords | TEXT | | 关键词（逗号分隔） |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

#### 6.1.4 调用日志表 (api_logs)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 日志ID |
| module | TEXT | NOT NULL | 调用模块（copywriter/compliance/customer_service/legal/logistics） |
| api_endpoint | TEXT | NOT NULL | API接口地址 |
| request_params | TEXT | | 请求参数 |
| response_data | TEXT | | 响应数据 |
| status | TEXT | NOT NULL | 状态（success/failed） |
| latency | INTEGER | | 响应时间（毫秒） |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |

#### 6.1.5 法规数据库表 (legal_database)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 法规ID |
| title | TEXT | NOT NULL | 法规标题 |
| category | TEXT | NOT NULL | 分类（consumer/product/privacy/tax/ad/ip） |
| region | TEXT | NOT NULL | 地区（usa/eu/uk/japan/germany/spain） |
| effective_date | TEXT | | 生效日期 |
| summary | TEXT | NOT NULL | 法规摘要 |
| compliance_tips | TEXT | | 合规建议（JSON格式） |
| details_url | TEXT | | 详情链接 |
| full_text | TEXT | | 完整内容 |
| related_laws | TEXT | | 关联法规（JSON格式） |
| data_source | TEXT | | 数据来源（manual/llm/api） |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

#### 6.1.5.1 法规数据库数据来源策略
法规数据库的数据来源采用**混合策略**：

| 来源方式 | 描述 | 适用场景 |
|----------|------|----------|
| **人工录入** | 由运营人员手动录入重要法规内容 | 核心法规、最新法规更新 |
| **LLM 生成** | 通过大模型生成法规摘要和合规建议 | 补充法规、生成中文摘要 |
| **公共 API** | 对接政府或法律数据库公开 API | 自动更新、实时数据 |

**初始化策略**：系统上线时预置核心法规数据（约50-100条），涵盖美国、欧盟、英国、日本等主要市场的消费者权益保护、产品安全、数据隐私等重点领域。

**更新策略**：定期（每周/每月）通过 LLM 检索最新法规变化，结合人工审核更新数据库。重要法规更新时推送用户提醒。

#### 6.1.6 法规检索历史表 (legal_history)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 历史ID |
| region | TEXT | NOT NULL | 地区 |
| category | TEXT | | 分类 |
| keyword | TEXT | | 关键词 |
| search_time | TIMESTAMPTZ | DEFAULT NOW() | 搜索时间 |

#### 6.1.7 单据模板表 (document_templates)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 模板ID |
| document_type | TEXT | NOT NULL | 单据类型（invoice/packing_list/customs_declaration） |
| template_name | TEXT | NOT NULL | 模板名称 |
| template_content | TEXT | NOT NULL | 模板内容（HTML/PDF模板） |
| default_template | INTEGER | DEFAULT 0 | 是否默认模板（0/1） |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

#### 6.1.8 生成单据记录表 (document_records)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 记录ID |
| document_id | TEXT | NOT NULL | 单据编号 |
| document_type | TEXT | NOT NULL | 单据类型 |
| order_info | TEXT | NOT NULL | 订单信息（JSON格式） |
| pdf_path | TEXT | NOT NULL | PDF文件路径 |
| generated_at | TIMESTAMPTZ | DEFAULT NOW() | 生成时间 |

#### 6.1.9 用户配置表 (user_settings)
| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | SERIAL | PRIMARY KEY | 配置ID |
| api_key | TEXT | NOT NULL | 大模型API密钥（AES-256加密存储） |
| api_endpoint | TEXT | NOT NULL | API接口地址 |
| model_name | TEXT | NOT NULL | 模型名称 |
| shop_name | TEXT | | 店铺名称 |
| main_category | TEXT | | 主营类目 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**API密钥加密说明**：
- 使用 AES-256-GCM 算法加密存储API密钥
- 加密密钥存储在环境变量中，不在数据库中保存
- 解密仅在需要调用大模型时进行，解密结果不缓存
- 支持配置定期轮换加密密钥

---

## 7. 大模型集成方案

### 7.1 API 调用规范

#### 7.1.1 请求格式（兼容 OpenAI）
```python
import requests

def call_llm(prompt, model="gpt-4", max_tokens=2000):
    url = f"{config.API_ENDPOINT}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个专业的跨境电商运营助手..."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

#### 7.1.2 Prompt 模板设计

**文案生成 Prompt**:
```
你是一个专业的亚马逊产品文案撰写专家。请根据以下中文产品描述，生成符合亚马逊平台规则的英文文案。

产品描述：{product_desc}

要求：
1. 标题：不超过200字符，包含核心关键词，符合亚马逊搜索规则
2. 卖点：5条，每条不超过100字符，突出产品核心优势
3. 详情：300-500字符，详细描述产品功能和使用场景
4. 语言：英语，专业且吸引人

请以JSON格式输出：
{
  "title": "...",
  "bullet_points": [...],
  "description": "..."
}
```

**合规审查 Prompt**:
```
你是一个跨境电商合规审查专家。请审查以下文案，识别潜在的合规风险。

文案内容：{content}
目标平台：{platform}

请检查以下维度：
1. 极限词：如"最牛、第一、顶级、最好、唯一"等
2. 品牌侵权：如Apple、Nike、Disney等知名品牌名称
3. 卡通形象：如米老鼠、Hello Kitty等受版权保护的形象
4. 违禁类目词：如武器、毒品、医疗设备等敏感词汇

请以JSON格式输出审查结果：
{
  "overall_risk": "high/medium/low",
  "issues": [
    {"type": "问题类型", "level": "风险等级", "content": "问题内容", "suggestion": "整改建议"}
  ]
}
```

**客服应答 Prompt**:
```
你是一个专业的跨境电商客服代表。请根据以下客户消息，生成合适的回复。

客户消息：{message}
店铺规则：{shop_rules}

要求：
1. 识别问题类型（物流查询、退货政策、商品问题、其他）
2. 根据店铺规则生成友好、专业的回复
3. 语言：英语
4. 如果问题复杂无法自动处理，请标记为需要人工介入

请以JSON格式输出：
{
  "category": "问题分类",
  "response": "回复内容",
  "needs_human": false,
  "confidence": 0.95
}
```

**法规检索 Prompt**:
```
你是一个跨境电商法律法规专家。请根据以下查询条件，检索相关法律法规并提供中文摘要和合规建议。

地区：{region}
分类：{category}
关键词：{keyword}

要求：
1. 列出相关法律法规名称
2. 生成中文摘要，简明扼要解释法规核心内容
3. 提供针对跨境电商卖家的合规建议
4. 如果没有找到相关法规，请明确说明

请以JSON格式输出：
{
  "results": [
    {
      "title": "法规名称",
      "summary": "中文摘要",
      "compliance_tips": ["建议1", "建议2"]
    }
  ]
}
```

**物流单据提示**:
```
你是一个专业的外贸单证员。请根据以下订单信息，生成标准格式的商业发票内容。

订单信息：{order_info}

要求：
1. 包含所有必要的发票要素（买卖双方信息、商品明细、金额、贸易术语等）
2. 格式规范，符合国际贸易惯例
3. 商品描述专业准确

请直接输出发票内容，不需要JSON格式。
```

### 7.2 安全性考虑

| 安全要点 | 处理方式 |
|----------|----------|
| API密钥存储 | 使用环境变量或加密存储，不在代码中硬编码 |
| 输入验证 | 对用户输入进行严格验证，防止注入攻击 |
| 输出过滤 | 对大模型输出进行过滤，防止敏感内容 |
| 调用频率限制 | 实现API调用频率限制，防止滥用 |
| 日志脱敏 | 日志中对敏感信息进行脱敏处理 |

### 7.3 认证机制

采用**JWT令牌认证**机制，确保API安全访问：

| 认证环节 | 描述 |
|----------|------|
| 用户登录 | 通过用户名密码获取JWT令牌 |
| Token验证 | 每次API请求携带Bearer Token |
| Token刷新 | 支持令牌过期前自动刷新 |
| 权限控制 | 基于角色的访问控制（RBAC） |

**认证API设计**：
- `POST /api/auth/login` - 用户登录获取Token
- `POST /api/auth/refresh` - 刷新Token
- `POST /api/auth/logout` - 退出登录

### 7.4 错误处理策略

#### 7.4.1 LLM调用重试机制
```
首次调用失败 → 等待1s → 第二次调用 → 等待2s → 第三次调用 → 返回降级响应
```

**指数退避重试参数**：
- 最大重试次数：3次
- 初始等待时间：1秒
- 退避系数：2
- 超时时间：30秒

#### 7.4.2 降级策略
| 场景 | 降级方案 |
|------|----------|
| LLM服务不可用 | 返回预设规则匹配结果 |
| 网络超时 | 返回缓存数据或默认响应 |
| API调用超限 | 返回友好提示，建议稍后重试 |

#### 7.4.3 统一错误响应格式
```json
{
  "success": false,
  "error_code": "LLM_TIMEOUT",
  "message": "大模型服务暂时不可用，请稍后重试",
  "retry_after": 60
}
```

### 7.5 CORS配置

| 配置项 | 值 |
|--------|-----|
| 允许来源 | 前端部署域名 |
| 允许方法 | GET, POST, PUT, DELETE, OPTIONS |
| 允许头 | Content-Type, Authorization |
| 凭证支持 | true |
| 预检缓存 | 3600秒 |

---

## 8. 部署方案

### 8.1 开发环境
- **操作系统**: Windows/macOS/Linux
- **Python**: 3.9+
- **Node.js**: 18+
- **数据库**: PostgreSQL 15.x（开发和生产统一使用）

### 8.2 生产环境

#### 8.2.1 单机部署（推荐小卖家）
- **服务器**: 1核2G云服务器即可
- **操作系统**: Ubuntu Server 22.04
- **数据库**: PostgreSQL 15.x（支持并发写入）
- **Web服务器**: Nginx + Gunicorn

#### 8.2.2 Docker 部署
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# frontend/nginx.conf
events {}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        server_name localhost;

        location / {
            root   /usr/share/nginx/html;
            index  index.html;
            try_files $uri $uri/ /index.html;
        }

        location /api/ {
            proxy_pass http://backend:5000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /static/ {
            root   /usr/share/nginx/html;
        }
    }
}
```

#### 8.2.3 Docker Compose 部署（推荐）
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: ecommerce-agent-db
    environment:
      POSTGRES_DB: ecommerce_agent
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: ./backend
    container_name: ecommerce-agent-backend
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD:-password}@db:5432/ecommerce_agent
      API_KEY: ${API_KEY}
      API_ENDPOINT: ${API_ENDPOINT}
      MODEL_NAME: ${MODEL_NAME:-gpt-4}
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: ecommerce-agent-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

**启动方式**：
```bash
# 创建环境变量文件
cp .env.example .env

# 修改 .env 文件配置
# - DB_PASSWORD: 数据库密码
# - API_KEY: 大模型API密钥
# - API_ENDPOINT: 大模型API接口地址

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 8.3 启动步骤

#### 8.3.1 后端启动
```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### 8.3.2 前端启动
```bash
cd frontend
npm install
npm run dev
```

---

## 9. 深圳外贸产业环境适配

### 9.1 本地化适配要点

| 适配维度 | 具体内容 |
|----------|----------|
| 物流时效 | 针对深圳物流特点，预设标准物流7-14天，加急3-5天 |
| 退货地址 | 默认深圳退货地址模板 |
| 报关信息 | 预设电子产品、服装等常见类目的报关模板 |
| 支付方式 | 支持PayPal、信用卡等海外常用支付方式的描述 |
| 节假日 | 考虑中国节假日对发货的影响 |

### 9.2 合规规则库预置

针对深圳跨境卖家常见类目，预置以下合规规则：
- **3C电子产品**: 电池容量限制、认证要求
- **服装类**: 材质标注规范、尺码标准
- **美妆类**: 成分标注、保质期要求
- **玩具类**: 安全认证、年龄警告

---

## 10. 项目实施计划

### 10.1 开发阶段划分

| 阶段 | 周期 | 主要任务 |
|------|------|----------|
| 第一阶段 | 1-2周 | 基础架构搭建、大模型API集成 |
| 第二阶段 | 2-3周 | 文案生成智能体开发 |
| 第三阶段 | 2-3周 | 合规审查智能体开发 |
| 第四阶段 | 2-3周 | 客服应答智能体开发 |
| 第五阶段 | 2-3周 | 法规检索智能体开发 |
| 第六阶段 | 2-3周 | 物流单据智能体开发（含PDF生成） |
| 第七阶段 | 1-2周 | 测试、优化、部署 |

### 10.2 关键里程碑

| 里程碑 | 交付物 |
|--------|--------|
| M1 | 系统可启动，API配置完成，可调用大模型 |
| M2 | 文案生成功能可用，支持英文生成和多语言翻译 |
| M3 | 合规审查功能可用，支持极限词、品牌侵权检测 |
| M4 | 客服应答功能可用，支持自动回复和人工转接 |
| M5 | 法规检索功能可用，支持多地区多分类查询 |
| M6 | 物流单据功能可用，支持发票、装箱单、报关单生成 |
| M7 | 系统上线部署，完成用户文档 |

---

## 11. 附录

### 11.1 支持的平台列表
- Amazon（亚马逊）
- eBay
- AliExpress（速卖通）

### 11.2 支持的语言列表
- English（英语）
- Español（西班牙语）
- Deutsch（德语）
- Français（法语）

### 11.3 合规风险等级定义
- **高风险**: 可能导致店铺被封或罚款的违规内容
- **中风险**: 可能导致商品下架或警告的违规内容
- **低风险**: 建议优化但不影响上架的内容

### 11.4 客服问题分类
- **shipping**: 物流查询
- **return**: 退货政策
- **product**: 商品问题
- **payment**: 支付问题
- **other**: 其他问题

### 11.5 法规检索地区代码
- **usa**: 美国
- **eu**: 欧盟
- **uk**: 英国
- **japan**: 日本
- **germany**: 德国
- **spain**: 西班牙

### 11.6 法规分类代码
- **consumer**: 消费者权益保护
- **product**: 产品安全
- **privacy**: 数据隐私
- **tax**: 税收合规
- **ad**: 广告合规
- **ip**: 知识产权

### 11.7 物流单据类型
- **commercial_invoice**: 商业发票
- **packing_list**: 装箱单
- **customs_declaration**: 报关单
- **bill_of_lading**: 提单信息
- **certificate_of_origin**: 原产地证
- **proforma_invoice**: 形式发票

### 11.8 贸易术语
- **FOB**: 离岸价（船上交货）
- **CIF**: 到岸价（成本、保险费加运费）
- **EXW**: 工厂交货
- **DDP**: 完税后交货