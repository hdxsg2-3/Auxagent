import os
import sys
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.copywriter import bp as copywriter_bp
from controllers.auto_listing import bp as auto_listing_bp
from controllers.compliance import bp as compliance_bp
from controllers.customer_service import bp as customer_service_bp
from controllers.legal import bp as legal_bp
from controllers.logistics import bp as logistics_bp
from controllers.settings import bp as settings_bp
from controllers.platforms import bp as platforms_bp
from controllers.universal_integration import bp as universal_integration_bp
from controllers.dashboard import bp as dashboard_bp
from controllers.batch import bp as batch_bp
from controllers.keyword_research import bp as keyword_bp
from controllers.scheduler import bp as scheduler_bp
from controllers.feedback import bp as feedback_bp
from controllers.image_tools import bp as image_tools_bp
from controllers.competitor import bp as competitor_bp
from utils.db import init_db

app = Flask(__name__)
CORS(app)

app.register_blueprint(copywriter_bp, url_prefix='/api/copywriter')
app.register_blueprint(auto_listing_bp, url_prefix='/api/auto-listing')
app.register_blueprint(compliance_bp, url_prefix='/api/compliance')
app.register_blueprint(customer_service_bp, url_prefix='/api/customer-service')
app.register_blueprint(legal_bp, url_prefix='/api/legal')
app.register_blueprint(logistics_bp, url_prefix='/api/logistics')
app.register_blueprint(settings_bp, url_prefix='/api/settings')
app.register_blueprint(platforms_bp, url_prefix='/api/platforms')
app.register_blueprint(universal_integration_bp, url_prefix='/api/universal-integration')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(batch_bp, url_prefix='/api/batch')
app.register_blueprint(keyword_bp, url_prefix='/api/keyword-research')
app.register_blueprint(scheduler_bp, url_prefix='/api/scheduler')
app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
app.register_blueprint(image_tools_bp, url_prefix='/api/image-tools')
app.register_blueprint(competitor_bp, url_prefix='/api/competitor')

init_db()

# ────────── 后台预下载 embedding 模型（加速首次使用）──────────
_embedding_ready = False


def _preload_embedding():
    """后台线程预下载 embedding 模型，解决首次调用卡顿问题"""
    global _embedding_ready
    try:
        print("[App] 正在后台预下载 embedding 模型...")
        from services.embedding_service import embedding_service
        ok = embedding_service.ensure_ready()
        _embedding_ready = ok
        if ok:
            print("[App] embedding 模型预下载完成")
        else:
            print("[App] embedding 模型预下载失败，将使用关键词兜底")
    except Exception as e:
        _embedding_ready = False
        print(f"[App] embedding 模型预下载异常: {e}")


# 启动后台线程（不阻塞 Flask 启动）
_preload_thread = threading.Thread(target=_preload_embedding, daemon=True)
_preload_thread.start()


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Crossborder AI Agent is running',
        'embedding_ready': _embedding_ready
    })


if __name__ == '__main__':
    # threaded=True 启用多线程，避免单请求阻塞（如 HuggingFace 模型加载重试）导致全站卡死
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
