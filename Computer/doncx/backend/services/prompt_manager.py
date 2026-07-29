# 文案生成通用合规约束（与合规审查模块对齐，避免生成后被二次打回）
COPYWRITER_COMPLIANCE_RULES = """合规与风控要求（避免生成后被审查驳回）：
1. 极限词：避免“最、第一、顶级、唯一、极致、超亮、超强、绝对、100%”等无证据的绝对化用语；可用“高亮、高亮度、优质、可靠、显著”等相对化表达。
2. 数据与百分比：如使用“亮度提升300%”等数据，必须明确对比对象（如“比传统灯泡亮度提升300%”），否则改为“亮度提升显著”或省略具体数字。
3. 医疗/健康宣称：禁用“护眼、保护视力、消除蓝光危害、长时间用眼不疲劳、预防近视、治疗、治愈”等暗示医疗功效的表述。可改为“柔和光线、适合阅读、减少眩光”等客观描述。
4. 场景与人群描述：避免“尤其适合儿童房、书房使用”等暗示功效或特定人群的绝对化说法；改为“适合儿童房、书房等场景使用”。
5. 不贬低竞品、不编造资质、不虚假宣传。
6. 所有卖点与描述必须是产品自身可验证属性，避免过度推断。"""


class PromptManager:
    def get_copywriter_prompt(self, product_desc, platform, target_language):
        language_map = {
            'en': 'English',
            'es': 'Spanish',
            'de': 'German',
            'fr': 'French',
            'zh': 'Chinese (简体中文)'
        }
        target_lang_name = language_map.get(target_language, 'Chinese')
        
        platform_rules = {
            'amazon': '亚马逊平台规则：标题不超过200字符，5个核心卖点，详情描述不超过2000字符，使用HTML格式',
            'ebay': 'eBay平台规则：标题不超过80字符，突出关键词，详情简洁明了',
            'aliexpress': '速卖通平台规则：标题不超过128字符，包含核心关键词，详情丰富图文并茂'
        }
        
        return f"""你是一个专业的跨境电商文案生成助手。请根据以下产品描述生成符合{platform_rules[platform]}的{target_lang_name}文案。

产品描述：{product_desc}

请输出以下格式的JSON：
{{
  "title": "生成的标题",
  "bullet_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
  "description": "详细描述内容"
}}

要求：
1. 标题要吸引人，包含核心关键词
2. 卖点要突出产品优势
3. 描述要详细，包含产品特性、使用方法、适用场景等
4. 语言必须是{target_lang_name}
5. {COPYWRITER_COMPLIANCE_RULES}
"""
    
    def get_refine_prompt(self, raw_text):
        return f"""你是一个资深的跨境电商选品与文案专家。下面是从 1688 商品详情页抓取到的原始杂乱文本（包含广告话术、冗余推荐、无关信息）。请从中精准提炼产品核心信息，去除夸张宣传和冗余内容。

原始抓取文本：
{raw_text}

请仅输出以下格式的 JSON（不要输出任何额外解释或 Markdown 标记）：
{{
  "product_name": "精准简练的产品名称",
  "core_selling_points": ["核心卖点1", "核心卖点2", "核心卖点3", "核心卖点4", "核心卖点5"],
  "key_parameters": ["关键参数1（含真实数值与单位，如 容量5000mAh）", "关键参数2", "关键参数3"],
  "applicable_scenarios": ["适用场景1", "适用场景2", "适用场景3"],
  "clean_description": "一段 150 字以内的客观产品简介，去除广告话术"
}}

要求：
1. 只保留产品自身真实信息，剔除"厂家直销""全网最低""爆款"等广告词；
2. 核心卖点聚焦产品功能与用户价值；
3. 关键参数保留真实数值（尺寸、容量、功率、材质、重量等）；
4. 字段缺失时返回空字符串或空数组，不要编造；
5. 仅输出 JSON；
6. 去除极限词、医疗/健康功效宣称、无证据的百分比提升、贬低竞品等违规表述，保持客观可验证。"""

    def get_manual_reply_translate_prompt(self, manual_reply, customer_message, platform):
        """
        人工客服回复自动翻译成客户咨询语言。
        先判断客户消息语言，再把人工回复译成该语言；若客户消息为中文则无需翻译。
        """
        platform_rules = {
            'amazon': 'Amazon（默认英语，但需按客户实际语言回复）',
            'ebay': 'eBay（默认英语）',
            'aliexpress': 'AliExpress（可能为多语言，常见俄语、西班牙语、法语、英语等）',
            'local-shop': '通用电商（按客户语言回复）',
            'temu': 'Temu（默认英语）',
            'tiktok': 'TikTok Shop（默认英语）',
            'shopee': 'Shopee（东南亚多语言）',
            'lazada': 'Lazada（东南亚多语言）'
        }
        platform_hint = platform_rules.get(platform, '通用电商（按客户语言回复）')

        return f"""你是一位跨境电商客服翻译助手。请将商家手写的人工客服回复翻译成客户咨询时使用的语言，方便客户直接阅读。

客户咨询消息：
{customer_message}

平台：{platform_hint}

商家手写人工回复（可能是中文）：
{manual_reply}

任务要求：
1. 首先判断客户咨询消息的主要语言（例如：英语、西班牙语、德语、法语、俄语、日语、简体中文等）；
2. 将「商家手写人工回复」翻译成该语言；
3. 若客户消息本身就是中文，则 translated_reply 与 manual_reply 保持一致；
4. 保持原意、语气友好专业，符合电商客服风格；
5. 不要添加原文中没有的解释或额外内容。

请仅输出以下格式的 JSON（不要输出任何额外解释或 Markdown 标记）：
{{
  "detected_language": "检测到的语言代码，如 en/es/de/fr/ru/ja/zh",
  "language_name": "语言名称，如 英语/西班牙语/德语",
  "translated_reply": "翻译后的人工回复，供客户直接阅读"
}}"""

    def get_translate_prompt(self, title, bullet_points, description, target_language):
        language_map = {
            'en': 'English',
            'es': 'Spanish',
            'de': 'German',
            'fr': 'French',
            'zh': 'Chinese (简体中文)'
        }
        target_lang_name = language_map.get(target_language, 'Chinese')
        
        return f"""请将以下电商文案翻译成{target_lang_name}，保持专业的电商风格。

标题：{title}

卖点：{', '.join(bullet_points)}

描述：{description}

请输出以下格式的JSON：
{{
  "title": "翻译后的标题",
  "bullet_points": ["翻译后的卖点1", "翻译后的卖点2", "翻译后的卖点3", "翻译后的卖点4", "翻译后的卖点5"],
  "description": "翻译后的描述内容"
}}

翻译要求：
1. 保持专业电商风格，保留原标题、卖点、描述的语义与结构；
2. 翻译后的文案不得引入极限词、医疗/健康功效宣称、无证据的绝对化数据、贬低竞品或虚假宣传；
3. 若原文包含违规表述，请在翻译时按合规规则改写，而非逐字翻译。"""
    
    def get_rewrite_prompt(self, original, compliance_result, platform, target_language):
        language_map = {
            'en': 'English',
            'es': 'Spanish',
            'de': 'German',
            'fr': 'French',
            'zh': 'Chinese (简体中文)'
        }
        target_lang_name = language_map.get(target_language, 'Chinese')
        
        platform_rules = {
            'amazon': '亚马逊平台规则：标题不超过200字符，5个核心卖点，详情描述不超过2000字符，使用HTML格式',
            'ebay': 'eBay平台规则：标题不超过80字符，突出关键词，详情简洁明了',
            'aliexpress': '速卖通平台规则：标题不超过128字符，包含核心关键词，详情丰富图文并茂'
        }
        
        title = original.get('title', '')
        bullets = original.get('bullet_points', [])
        desc = original.get('description', '')
        overall_risk = compliance_result.get('overall_risk', 'low')
        extreme = '；'.join([f"{x.get('word', '')}（建议：{x.get('suggestion', '')}）" for x in compliance_result.get('extreme_words', [])])
        forbidden = '；'.join([f"{x.get('word', '')}（类别：{x.get('category', '')}）" for x in compliance_result.get('forbidden_words', [])])
        suggestions = '；'.join(compliance_result.get('suggestions', []))
        
        return f"""你是跨境电商文案合规专家。请根据以下合规审查反馈，改写原始文案，消除所有违规风险，同时保持原意和卖点。
- 平台：{platform_rules[platform]}
- 目标语言：{target_lang_name}

原始文案：
标题：{title}
卖点：{'；'.join(bullets)}
描述：{desc}

合规审查反馈：
- 整体风险：{overall_risk}
- 极限词：{extreme or '无'}
- 违禁词：{forbidden or '无'}
- 优化建议：{suggestions or '无'}

改写要求：
1. 移除所有极限词、违禁词、医疗/健康功效宣称、无证据的绝对化数据、贬低竞品或虚假宣传。
2. 保留产品真实卖点，用客观、可验证、相对化的描述。
3. 保持标题、卖点、描述的结构不变，返回同样的 JSON 格式。
4. 语言必须是{target_lang_name}。

请输出以下格式的JSON：
{{
  "title": "改写后的标题",
  "bullet_points": ["改写后的卖点1", "改写后的卖点2", "改写后的卖点3", "改写后的卖点4", "改写后的卖点5"],
  "description": "改写后的描述内容"
}}"""
    
    def get_compliance_prompt(self, content, check_extreme_words, check_copyright, check_forbidden_words, image_texts=''):
        checks = []
        if check_extreme_words:
            checks.append('极限词检测（如：最、第一、顶级、唯一等）')
        if check_copyright:
            checks.append('版权风险检测（品牌名、卡通形象、专利产品名）')
        if check_forbidden_words:
            checks.append('违禁词检测（平台禁止使用的词汇）')
        
        image_section = ''
        if image_texts:
            image_section = f"""

用户还上传了以下图片，并已经过识别。请结合图片中的文字和描述一并审查：
{image_texts}
"""

        return f"""你是一个跨境电商合规审查专家。请审查以下文案内容，检测以下风险：{', '.join(checks)}。

待审查文案：{content}{image_section}

请输出以下格式的JSON：
{{
  "overall_risk": "high" | "medium" | "low",
  "extreme_words": [{{"word": "检测到的极限词", "suggestion": "建议替换词"}}],
  "copyright_issues": [{{"description": "版权风险描述", "risk_level": "风险等级"}}],
  "forbidden_words": [{{"word": "检测到的违禁词", "category": "所属类别"}}],
  "clean": true | false,
  "suggestions": ["优化建议1", "优化建议2"]
}}"""
    
    def get_customer_service_prompt(self, message, platform):
        platform_rules = {
            'amazon': '亚马逊客服规则：友好专业，24小时内回复，提供明确解决方案',
            'ebay': 'eBay客服规则：及时礼貌，积极解决问题',
            'aliexpress': '速卖通客服规则：中文沟通，详细解答，提供物流追踪',
            'local-shop': '通用电商客服规则：友好专业，及时回复，提供明确解决方案',
            'temu': 'Temu客服规则：友好专业，积极解决问题'
        }
        
        rules = platform_rules.get(platform, '通用电商客服规则：友好专业，及时回复，提供明确解决方案')
        
        return f"""你是一个跨境电商客服助手。请根据{rules}处理以下客户咨询。

客户消息：{message}

严格要求：
1. 回复使用与客户消息相同的语言（客户用英语则回复英语，用西班牙语则回复西班牙语；无法确定时默认英语）；
2. 回复必须真实可信：只能基于客服通用规范与常识作答，严禁编造订单号、物流单号、具体到货日期、退款金额、优惠额度等你不掌握的信息；
3. 回复简洁克制，控制在 2-4 句话，直奔主题，不要堆砌套话；
4. 若问题需要卖家才能确认的信息（如具体物流状态、退款审批、补偿方案），不要编造，给出诚实的临时安抚并说明将转交人工，status 设为 "pending"；
5. 若可基于通用规范直接解答（如兼容性、使用说明、通用退货政策），给出明确答复，status 设为 "auto_replied"；
6. 额外输出一段简体中文翻译 response_zh，与 response 内容一致，供商家核对回复是否准确；
7. message_zh：将客户的原消息翻译成简体中文，供商家快速理解客户咨询内容。若原消息已经是中文，则 message_zh 与 message 一致。

请输出以下格式的 JSON（不要输出任何额外解释或 Markdown 标记）：
{{
  "message_zh": "客户原消息的简体中文翻译",
  "response": "用客户语言写成的自动回复（简洁真实）",
  "response_zh": "上述 reply 的简体中文翻译，供商家核对",
  "status": "auto_replied" | "pending"
}}"""

    def get_rag_customer_service_prompt(self, message, platform, knowledge_context, memory_context, buyer_history_context=''):
        """
        RAG 增强版客服提示词 —— 注入检索到的知识库、买家历史对话、同类咨询参考
        knowledge_context: str，检索到的知识条目
        memory_context: str，语义检索到的同类历史对话（可能来自其他客户）
        buyer_history_context: str，该买家本人的历史对话（精确匹配 buyer_id）
        """
        platform_rules = {
            'amazon': '亚马逊客服规则：友好专业，24小时内回复，提供明确解决方案',
            'ebay': 'eBay客服规则：及时礼貌，积极解决问题',
            'aliexpress': '速卖通客服规则：中文沟通，详细解答，提供物流追踪',
            'local-shop': '通用电商客服规则：友好专业，及时回复，提供明确解决方案',
            'temu': 'Temu客服规则：友好专业，积极解决问题'
        }
        rules = platform_rules.get(platform, '通用电商客服规则：友好专业，及时回复，提供明确解决方案')

        kb_section = ""
        buyer_section = ""
        mem_section = ""

        if knowledge_context:
            kb_section = f"""
【店铺专属知识库（以下信息为本店铺真实规则，请优先参考）】
{knowledge_context}
"""

        if buyer_history_context:
            buyer_section = f"""
【此客户的历史对话（以下是该客户本人之前的咨询记录，请保持上下文连贯、记住客户身份和之前沟通的内容）】
{buyer_history_context}
"""

        if memory_context:
            mem_section = f"""
【同类咨询参考（以下为其他客户类似咨询的处理方式，可供风格参考，但不要将其内容误认为是当前客户的个人历史）】
{memory_context}
"""

        return f"""你是一个跨境电商客服助手，服务于一家真实运营中的店铺。请根据{rules}处理以下客户咨询。

{kb_section}{buyer_section}{mem_section}
客户消息：{message}

严格要求：
1. 回复使用与客户消息相同的语言（客户用英语则回复英语，用西班牙语则回复西班牙语；无法确定时默认英语）；
2. 优先依据【店铺专属知识库】中的信息作答：退换货政策、FAQ、商品信息等必须以知识库为准，不得凭空编造；
3. 若有【此客户的历史对话】，说明该客户是回头客：必须结合该客户之前咨询的内容做连贯回复，可自然提及之前处理过的问题和结论（如"根据我们上次沟通的情况..."），不要像第一次接触一样回复；
4. 若有【同类咨询参考】，仅作遣词造句风格参考，不要将其他客户的个人信息或订单状态代入当前回复；
5. 回复简洁克制，控制在 2-4 句话，直奔主题，不要堆砌套话；
6. 若问题超出知识库覆盖范围且需要卖家确认（如具体物流状态、退款审批、补偿方案），不要编造，给出诚实的临时安抚并说明将转交人工，status 设为 "pending"；
7. 若可基于知识库或通用规范直接解答，给出明确答复，status 设为 "auto_replied"；
8. 额外输出一段简体中文翻译 response_zh，与 response 内容一致，供商家核对回复是否准确；
9. message_zh：将客户的原消息翻译成简体中文，供商家快速理解客户咨询内容。若原消息已经是中文，则 message_zh 与 message 一致。

请输出以下格式的 JSON（不要输出任何额外解释、注释、Markdown 标记、示例或多个版本；只输出一段可被直接解析的 JSON）：
{{
  "message_zh": "客户原消息的简体中文翻译",
  "response": "用客户语言写成的自动回复（简洁真实，优先依据知识库，回头客保持上下文连贯）",
  "response_zh": "上述 reply 的简体中文翻译，供商家核对",
  "status": "auto_replied" | "pending"
}}

输出约束：
- 仅输出一个 JSON 对象；
- 不要加 "注："、"更正说明"、"最终按规则输出" 等额外文字；
- 不要输出任何 Markdown 代码块标记（如 ```json）；
- status 字段必须是字符串 "auto_replied" 或 "pending"，不要带其他描述。"""
    
    def get_legal_search_prompt(self, query, regions):
        return f"""你是一个跨境电商法律专家。请搜索关于"{query}"的法律法规信息。

目标地区：{', '.join(regions)}

请输出以下格式的JSON：
[
  {{
    "title": "法规标题",
    "region": "地区代码（如EU、US、JP）",
    "effective_date": "生效日期",
    "summary": "法规简介",
    "description": "详细描述",
    "scope": ["适用范围1", "适用范围2"],
    "requirements": ["合规要求1", "合规要求2"]
  }}
]"""
