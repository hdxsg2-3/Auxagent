from flask import Blueprint, request, jsonify
from utils.db import DEFAULT_MERCHANT

bp = Blueprint('feedback', __name__)

# 简单的内存存储（可选升级到DB表）
_feedback_store = []


@bp.route('/submit', methods=['POST'])
def submit_feedback():
    """提交内容质量评分"""
    data = request.get_json() or {}
    module = data.get('module', '')
    content_id = data.get('content_id', data.get('id', ''))
    rating = data.get('rating', '')  # 'like' or 'dislike'
    comment = data.get('comment', '')
    original = data.get('original', '')
    generated = data.get('generated', '')

    if not module or rating not in ('like', 'dislike'):
        return jsonify({'success': False, 'message': '请提供 module 和 rating'}), 400

    _feedback_store.append({
        'module': module,
        'content_id': content_id,
        'rating': rating,
        'comment': comment,
        'original': original[:200],
        'generated': generated[:200],
    })

    likes = sum(1 for f in _feedback_store if f.get('rating') == 'like')
    dislikes = sum(1 for f in _feedback_store if f.get('rating') == 'dislike')

    return jsonify({'success': True, 'data': {'likes': likes, 'dislikes': dislikes, 'total': len(_feedback_store)}})


@bp.route('/stats', methods=['GET'])
def get_stats():
    module = request.args.get('module', '')
    filtered = [f for f in _feedback_store if not module or f.get('module') == module]
    likes = sum(1 for f in filtered if f.get('rating') == 'like')
    dislikes = sum(1 for f in filtered if f.get('rating') == 'dislike')
    return jsonify({
        'success': True,
        'data': {
            'total': len(filtered),
            'likes': likes,
            'dislikes': dislikes,
            'rate': f"{likes / max(len(filtered), 1) * 100:.0f}%"
        }
    })


@bp.route('/list', methods=['GET'])
def list_feedback():
    module = request.args.get('module', '')
    filtered = [f for f in _feedback_store if not module or f.get('module') == module]
    return jsonify({'success': True, 'data': filtered[-20:]})
