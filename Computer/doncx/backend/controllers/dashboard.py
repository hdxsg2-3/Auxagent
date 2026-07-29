from flask import Blueprint, jsonify
from utils.db import (
    list_copywriter_records,
    list_compliance_records,
    list_invocation_logs,
    list_messages,
    list_logistics_documents,
    DEFAULT_MERCHANT,
)
from datetime import datetime

bp = Blueprint('dashboard', __name__)


@bp.route('/stats', methods=['GET'])
def get_stats():
    """聚合仪表盘核心数据"""
    try:
        today_str = datetime.now().strftime('%Y-%m-%d')

        # 文案生成统计
        all_copy = list_copywriter_records(DEFAULT_MERCHANT)
        copy_today = sum(1 for c in all_copy if c.get('created_at', '').startswith(today_str))

        # 合规审查统计
        all_comp = list_compliance_records(DEFAULT_MERCHANT)
        comp_today = sum(1 for c in all_comp if c.get('created_at', '').startswith(today_str))

        # 客服统计（消息数 + 调用记录）
        all_messages = list_messages(DEFAULT_MERCHANT)
        all_invocations = list_invocation_logs(DEFAULT_MERCHANT)
        cs_today = sum(1 for m in all_messages if m.get('created_at', '').startswith(today_str))

        # 物流统计
        all_logistics = list_logistics_documents(DEFAULT_MERCHANT) or []
        logistics_today = sum(1 for l in all_logistics if str(l.get('created_at', '')).startswith(today_str))
        logistics_by_status = {}
        for l in all_logistics:
            st = l.get('status', 'unknown')
            logistics_by_status[st] = logistics_by_status.get(st, 0) + 1

        stats = {
            'copywriter': {'total': len(all_copy), 'today': copy_today},
            'compliance': {'total': len(all_comp), 'today': comp_today},
            'customer_service': {'total': len(all_invocations), 'today': cs_today},
            'logistics': {'total': len(all_logistics), 'today': logistics_today, 'by_status': logistics_by_status},
        }

        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/activity', methods=['GET'])
def get_activity():
    """近期操作动态"""
    try:
        activities = []

        # 最新文案
        for c in list_copywriter_records(DEFAULT_MERCHANT)[:5]:
            mode = c.get('mode', '')
            language = c.get('language', '')
            detail = f"{mode or '文案'} {language or ''}".strip()
            activities.append({
                'type': 'copywriter',
                'label': '文案生成',
                'detail': detail[:40] or '文案记录',
                'color': 'violet',
                'time': str(c.get('created_at', ''))[:19],
            })

        # 最新合规
        for c in list_compliance_records(DEFAULT_MERCHANT)[:5]:
            result = c.get('result_json', '{}')
            import json
            try:
                result_obj = json.loads(result) if isinstance(result, str) else result
                risk = (result_obj or {}).get('summary', '正常') if isinstance(result_obj, dict) else '正常'
            except Exception:
                risk = '未知'
            activities.append({
                'type': 'compliance',
                'label': '合规审查',
                'detail': f"风险: {str(risk)[:30]}",
                'color': 'amber' if '异常' in str(risk) or '风险' in str(risk) else 'emerald',
                'time': str(c.get('created_at', ''))[:19],
            })

        # 最新客服
        for m in list_messages(DEFAULT_MERCHANT)[:5]:
            customer = m.get('customer_name', '')
            message = m.get('message', '')
            detail = f"{customer}: {str(message)[:30]}"
            activities.append({
                'type': 'customer_service',
                'label': '客服消息',
                'detail': detail,
                'color': 'blue',
                'time': str(m.get('created_at', ''))[:19],
            })

        # 最新物流
        for l in (list_logistics_documents(DEFAULT_MERCHANT) or [])[:8]:
            activities.append({
                'type': 'logistics',
                'label': '物流单据',
                'detail': str(l.get('doc_type', '')),
                'color': 'purple',
                'status': l.get('status', ''),
                'time': str(l.get('created_at', ''))[:19],
            })

        # 按时间倒排，取最近20条
        activities.sort(key=lambda x: x['time'], reverse=True)
        return jsonify({'success': True, 'data': activities[:20]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
