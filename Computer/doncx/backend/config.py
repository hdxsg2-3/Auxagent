import os
from pathlib import Path


def _load_dotenv():
    """从项目根目录与 backend 目录读取 .env（纯标准库实现，不引入新依赖）。
    .env 已被 .gitignore 忽略，不会提交到仓库，仅用于本地开发保存真实密钥。
    """
    candidates = [
        Path(__file__).resolve().parent.parent / '.env',  # 项目根 doncx/.env
        Path(__file__).resolve().parent / '.env',         # backend/.env
    ]
    for p in candidates:
        if p.is_file():
            try:
                with open(p, encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#') or '=' not in line:
                            continue
                        k, v = line.split('=', 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        os.environ.setdefault(k, v)
            except Exception:
                pass


_load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-me-in-production'

    # 方舟大模型 API Key（从环境变量 / .env 读取，禁止硬编码真实值）
    API_KEY = os.environ.get('ARK_API_KEY') or os.environ.get('API_KEY') or ''
    API_ENDPOINT = os.environ.get('API_ENDPOINT') or 'https://ark.cn-beijing.volces.com/api/v3'

    MODEL_NAME = os.environ.get('MODEL_NAME') or 'ep-20260405222155-5xsbr'
    TEMPERATURE = float(os.environ.get('TEMPERATURE') or 0.7)
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS') or 4096)
    TIMEOUT = int(os.environ.get('TIMEOUT') or 300)

    VOLC_CONTENT_AK = os.environ.get('VOLC_CONTENT_AK') or ''
    VOLC_CONTENT_SK = os.environ.get('VOLC_CONTENT_SK') or ''

    VOLC_TRANS_AK = os.environ.get('VOLC_TRANS_AK') or ''
    VOLC_TRANS_SK = os.environ.get('VOLC_TRANS_SK') or ''

    # 火山内容安全审核所需的审核资产 AppId（在火山控制台创建内容安全资产后获得）
    VOLC_CONTENT_APP_ID = os.environ.get('VOLC_CONTENT_APP_ID') or ''

    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/app.log'
