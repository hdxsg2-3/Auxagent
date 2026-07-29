# Auxagent - 跨境智能助手

一站式跨境卖家运营工具，集成 AI 文案生成、合规审查、客服应答、商品管理、竞品分析、图片处理与自动巡检等能力。

> **代码仓库地址**：https://github.com/hdxsg2-3/Auxagent
> **智能体 URL**：（部署后更新）

## 功能模块

| 模块 | 说明 |
|------|------|
| **文案生成** | 手动输入 / 1688 链接一键生成 / 批量操作，多平台多语言 Listing 生成 |
| **合规审查** | 极限词、版权商标、违禁词检测，支持批量扫描 |
| **客服应答** | 灵活应答 + 话术库，模拟卖家客服回复 |
| **物流单据** | 物流单据文案生成 |
| **商品管理** | Listing 管理与优化 |
| **竞品分析** | 竞品标题分析、综合评分 |
| **图片处理** | 图片尺寸调整、信息查看 |
| **自动巡检** | 定时合规巡检、物流状态巡检，支持手动立即执行 |
| **法务专区** | 跨境法规查询与详情 |

## 技术栈

- **前端**：Vue 3 + Vite + Element Plus + Tailwind CSS + Lucide Icons
- **后端**：Python Flask + SQLite
- **AI 能力**：大语言模型驱动（文案生成、合规分析、客服应答等）

## 快速开始

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
python app.py
```

后端默认运行在 `http://localhost:5000`

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，自动代理 `/api/*` 到后端。

### 3. 配置

在 `backend/` 目录下创建 `.env` 文件，填入必要的 API Key：

```env
# LLM API 配置
API_KEY=your_api_key_here
API_BASE_URL=your_api_base_url
MODEL_NAME=your_model_name
```

### 4. 一键启动（Windows）

双击运行项目根目录下的 `start.bat`

## 项目结构

```
doncx/
├── backend/                # Flask 后端
│   ├── app.py             # 入口
│   ├── config.py          # 配置
│   ├── controllers/       # 路由控制器
│   ├── services/          # 业务服务（LLM、知识库等）
│   ├── platforms/         # 平台集成（Amazon、Temu、eBay）
│   ├── utils/             # 工具（数据库、API 客户端、校验器）
│   └── data/              # 数据文件
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/           # API 客户端
│   │   ├── components/    # 页面组件
│   │   ├── store/         # 状态管理
│   │   └── style.css      # 全局样式
│   └── vite.config.js     # Vite 配置（含 API 代理）
├── .gitignore
└── start.bat              # Windows 一键启动脚本
```
