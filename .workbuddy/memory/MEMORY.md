# 项目记忆：跨境电商 AI 运营 Agent 工作台 (cross_border_agent/gm/Computer/doncx)

## 架构概览
- 后端：Python Flask（`backend/`），蓝图路由 `/api/<模块>`；方舟大模型(Volces Ark)封装在 `services/llm_service.py`，提示词在 `services/prompt_manager.py`，HTTP 客户端在 `utils/api_client.py`。
- 前端：Vue3 + Vite + Tailwind + Element Plus（`frontend/`），axios 基址 `/api`，Vite 代理到 `localhost:5000`。
- 模块：copywriter(文案生成) / compliance(合规审查) / customer-service(客服应答) / legal / logistics / settings。

## 本次新增：链接一键生成上架文案智能 Agent（自动链路）
- 入口：前端「文案生成」页新增"链接一键生成"模式（Copywriter.vue，1688 链接输入→一键生成）。
- 后端新增 `controllers/auto_listing.py`（蓝图 `/api/auto-listing`，`POST /generate`），编排 5 步：
  1) `services/scraper.py` 爬 1688（requests + 标准库 html.parser，反爬请求头+随机延时，失败抛 ScrapeError）
  2) LLMService.refine_product_info 提炼（PromptManager.get_refine_prompt）
  3) 复用 generate_copywriter 并行生成 英/西/德 亚马逊 Listing
  4) 复用 scan_compliance 逐语种风控校验
  5) 返回 raw_scraped / refined_info / listings / compliance 四板块
- 爬虫仅依赖 requests + 标准库，未引入 bs4/lxml。
- **2026-07-18 更新**：1688 反爬导致 500 / 抓取失败，已升级 scraper：
  - 优先使用 Playwright 浏览器渲染（未安装时回退 requests）；
  - requests 模式改为访问 `m.1688.com` 移动端 + 清洗 URL 追踪参数 + 完整移动浏览器头；
  - 增强内嵌 JSON / img alt 提取，作为规格与卖点补充；
  - 反爬检测更准确，返回带解决建议的友好错误；
  - `requirements.txt` 增加可选 `playwright` 注释；`auto_listing.py` 整个接口加顶层 try/except 防止未捕获 500。
- 已知限制：1688 图文内文字(图片承载)无法 OCR 提取；详情描述可能懒加载不完整；高频/异常 IP 仍可能触发反爬，建议安装 Playwright。
- **2026-07-18 更新**：文案生成新增「中文」语种选项。
  - 手动模式语言下拉新增 `{zh: 中文}`（Copywriter.vue `languages`）；prompt_manager 两个 `language_map` 与 validator 的 `OneOf` 均已加入 `zh`。
  - 链接一键生成 LANGUAGES 由 `['en','es','de']` 扩为 `['en','es','de','zh']`，生成四语种(英/西/德/中)Listing 与风控；前端 `listingLangs` 加中文 ZH，`copyAllLink` 遍历同步加入 `zh`。

## 本次新增：客服回复中文翻译 + 真实简洁约束
- `get_customer_service_prompt` 重写为：用与客户相同语言回复、简洁 2-4 句、**严禁编造订单/物流/退款等不掌握信息**、返回 `response_zh`（简体中文翻译供商家核对）；需卖家确认的信息 status 设 `pending`。
- `LLMService._parse_customer_service_response` 解析并兜底 `response_zh`（缺失时 `''`）。
- 前端 CustomerService.vue：消息数据加 `response_zh`；详情区新增"中文翻译（供商家核对）"板块；"复制回复"/"复制翻译"按钮已接线。

## 运行依赖
- 后端 `backend/requirements.txt`：flask, flask-cors, requests, marshmallow（沙箱内 .venv 为空，需先 `pip install -r requirements.txt`）。
- 前端 `npm install && npm run dev`（端口 5173，代理到 5000）。
