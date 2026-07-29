from flask import Blueprint, request, jsonify
from utils.db import DEFAULT_MERCHANT
from services.llm_service import LLMService
import json

bp = Blueprint('competitor', __name__)
llm = LLMService()


@bp.route('/analyze', methods=['POST'])
def analyze_competitor():
    """输入竞品链接或ASIN/标题，生成分析报告"""
    data = request.get_json() or {}
    target = (data.get('url') or data.get('asin') or data.get('title') or '').strip()
    if not target:
        return jsonify({'success': False, 'message': '请输入竞品链接、ASIN 或标题'}), 400

    prompt = (
        f'你是一位跨境电商竞品分析专家。请对以下竞品进行分析：\n\n'
        f'目标：{target}\n\n'
        f'以JSON格式返回分析报告：\n'
        + json.dumps({
            "product_summary": "产品概述50字",
            "strengths": ["优势1", "优势2", "优势3"],
            "weaknesses": ["劣势1", "劣势2"],
            "pricing_analysis": "定价策略分析",
            "keyword_strategy": ["关键词1", "关键词2"],
            "customer_feedback_highlights": "买家属性的关注点",
            "differentiation_suggestions": ["差异化建议1", "差异化建议2"],
            "overall_score": "综合评分(1-10)"
        }, ensure_ascii=False)
        + '\n请直接返回JSON，不要markdown代码块。'
    )

    try:
        response, error = llm.client.call_llm([{'role': 'user', 'content': prompt}])
        if error:
            return jsonify({'success': False, 'message': f'LLM调用失败: {error}'}), 500
        if isinstance(response, str):
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1].replace('json', '', 1).strip()
            response = json.loads(response)
        return jsonify({'success': True, 'data': response})
    except json.JSONDecodeError:
        return jsonify({'success': False, 'message': '解析失败', 'raw': str(response)[:500]}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
