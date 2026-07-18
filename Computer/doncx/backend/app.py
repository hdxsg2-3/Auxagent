import os
import sys
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

init_db()

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Crossborder AI Agent is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
