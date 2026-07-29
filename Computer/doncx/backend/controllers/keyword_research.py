from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
import json

bp = Blueprint('keyword_research', __name__)
llm = LLMService()


@bp.route('/suggest', methods=['POST'])
def suggest_keywords():
    """输入产品名+平台，返回关键词建议"""
    data = request.get_json() or {}
    product_name = (data.get('product_name') or '').strip()
    platform = data.get('platform', 'amazon')
    category = data.get('category', '').strip()

    if not product_name:
        return jsonify({'success': False, 'message': '请输入产品名称'}), 400

    prompt = (
        f'你是一位{"亚马逊" if platform=="amazon" else ("eBay" if platform=="ebay" else "跨境电商")}SEO专家。\n\n'
        f'产品名称：{product_name}\n'
        + (f'品类：{category}\n' if category else '')
        + '\n请为这个产品生成关键词研究报告，用JSON格式返回：\n'
        '{\n'
        '  "core_keywords": [{"keyword": "核心词", "search_volume": "高/中/低", "competition": "高/中/低", "relevance": "高"}],\n'
        '  "long_tail_keywords": [{"keyword": "长尾词", "search_volume": "高/中/低", "competition": "高/中/低"}],\n'
        '  "title_suggestions": ["建议标题1包含主关键词", "建议标题2"],\n'
        '  "search_terms": ["后台搜索词1", "后台搜索词2"],\n'
        '  "negative_keywords": ["否定关键词"],\n'
        '  "analysis": "简要分析100字内"\n'
        '}\n请直接返回JSON，不要包含markdown代码块标记。'
    )

    try:
        response, error = llm.client.call_llm([{'role': 'user', 'content': prompt}])
        if error:
            return jsonify({'success': False, 'message': f'LLM调用失败: {error}'}), 500

        result = response
        if isinstance(result, str):
            result = result.strip()
            # 尝试提取 JSON
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]
            result = json.loads(result)

        return jsonify({'success': True, 'data': result})
    except json.JSONDecodeError:
        return jsonify({'success': False, 'message': '解析结果失败，请重试', 'raw': response[:500] if isinstance(response, str) else str(response)[:500]}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/optimize-title', methods=['POST'])
def optimize_title():
    """根据关键词优化标题"""
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    keywords = data.get('keywords', [])
    platform = data.get('platform', 'amazon')

    if not title:
        return jsonify({'success': False, 'message': '请输入原始标题'}), 400

    kw_str = '、'.join(keywords[:10]) if keywords else '无指定'
    platform_label = "亚马逊" if platform == "amazon" else ("eBay" if platform == "ebay" else "跨境电商")
    prompt = (
        f'你是一位{platform_label}Listing优化专家。\n\n'
        f'原始标题：{title}\n'
        f'需要融入的关键词：{kw_str}\n'
        f'平台：{platform}\n\n'
        '请做以下优化：\n'
        '1. 优化后的标题（融入关键词，控制在200字符内）\n'
        '2. 优化要点（3-5条修改说明）\n'
        '3. 估计提升效果（曝光/点击/转化提升百分比范围）\n'
        '以JSON返回：{"optimized_title": "...", "improvements": ["..."], "estimated_boost": {"impressions": "x%", "clicks": "x%", "conversion": "x%"}}'
    )

    try:
        response, error = llm.client.call_llm([{'role': 'user', 'content': prompt}])
        if error:
            return jsonify({'success': False, 'message': f'失败: {error}'}), 500
        if isinstance(response, str):
            response = response.strip()
            if response.startswith('```'): response = response.split('```')[1].replace('json', '', 1)
            response = json.loads(response)
        return jsonify({'success': True, 'data': response})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
