import json

from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
from utils.validator import CopywriterGenerateSchema, CopywriterTranslateSchema, validate_request
from utils.logger import log_error
from utils.db import (
    list_copywriter_records, add_copywriter_record,
    delete_copywriter_record, clear_copywriter_records, DEFAULT_MERCHANT,
    list_knowledge_entries, add_knowledge_entry
)
from services.knowledge_base import KnowledgeBase

bp = Blueprint('copywriter', __name__)

@bp.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    validation = validate_request(CopywriterGenerateSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    try:
        llm_service = LLMService()
        # 默认关闭自动合规扫描，节省 1 次 LLM 调用（30-60s → 减少一半）
        # 用户可在生成结果页点击「合规扫描」按钮按需触发
        result = llm_service.generate_copywriter(
            data['product_desc'],
            data['platform'],
            data['target_language'],
            auto_compliance=False
        )
        
        if result and 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 400
        
        if result:
            # 自动写入知识库 style 分类，供 AI 学习文案风格
            title = result.get('title', '')
            bullets = '；'.join(result.get('bullet_points', []))
            desc = result.get('description', '')
            kb_content = f"标题：{title}\n卖点：{bullets}\n描述：{desc}"
            _auto_save_style_to_kb(
                _merchant(), title, kb_content,
                data['platform'], data['target_language']
            )
            return jsonify({'success': True, 'data': result})
        
        return jsonify({'success': False, 'message': 'AI 未返回任何内容'}), 500
    except Exception as e:
        log_error('copywriter.generate', e)
        return jsonify({'success': False, 'message': f'服务器内部错误：{str(e)}'}), 500

@bp.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    validation = validate_request(CopywriterTranslateSchema, data)
    
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400
    
    try:
        llm_service = LLMService()
        result = llm_service.translate_copywriter(
            data['title'],
            data['bullet_points'],
            data['description'],
            data['target_language']
        )
        
        if result and 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 400
        
        if result:
            return jsonify({'success': True, 'data': result})
        
        return jsonify({'success': False, 'message': 'AI 未返回任何内容'}), 500
    except Exception as e:
        log_error('copywriter.translate', e)
        return jsonify({'success': False, 'message': f'服务器内部错误：{str(e)}'}), 500


def _merchant():
    body = request.get_json(silent=True) or {}
    return body.get('merchant_id') or request.args.get('merchant_id') or DEFAULT_MERCHANT


def _auto_save_style_to_kb(merchant_id, title, content, platform, language):
    """将文案生成结果自动写入知识库的「文案风格」分类，供后续 AI 参考学习
    改为后台异步执行，避免阻塞文案返回（HuggingFace 不可达时重试 5 次会卡 40+ 秒）
    """
    def _bg_save():
        try:
            # 去重：检查知识库是否已有相同标题的 style 条目
            existing = list_knowledge_entries(merchant_id)
            for e in existing:
                if e.get('category') == 'style' and e.get('title', '').strip() == title.strip():
                    return  # 已存在，跳过

            kb = KnowledgeBase(merchant_id)
            platform_label = platform or '通用'
            lang_label = {'en': '英语', 'zh': '中文', 'es': '西班牙语', 'de': '德语', 'fr': '法语'}.get(language, language or '')
            label = f"[{platform_label}]" if platform_label else ""
            label += f" [{lang_label}]" if lang_label else ""
            full_title = f"文案参考：{label} {title}" if label else f"文案参考：{title}"
            kb.add_entry(full_title, content, category='style')
        except Exception as e:
            log_error('copywriter._auto_save_style_to_kb', e)

    # 后台线程执行，不阻塞响应
    import threading
    t = threading.Thread(target=_bg_save, daemon=True)
    t.start()


@bp.route('/history', methods=['GET'])
def history_list():
    try:
        records = list_copywriter_records(_merchant())
        for r in records:
            if r.get('result_json'):
                try:
                    r['result'] = json.loads(r['result_json'])
                except Exception:
                    r['result'] = None
            r.pop('result_json', None)
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        log_error('copywriter.history_list', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history', methods=['POST'])
def history_add():
    data = request.get_json() or {}
    try:
        rec_id = add_copywriter_record(
            _merchant(),
            data.get('mode', 'manual'),
            data.get('platform'),
            data.get('language'),
            data.get('input_text', ''),
            json.dumps(data.get('result', {}), ensure_ascii=False)
        )
        # 如果前端传了 result，也自动写入知识库
        result_obj = data.get('result', {})
        if isinstance(result_obj, dict) and result_obj.get('title'):
            title = result_obj.get('title', '')
            bullets = '；'.join(result_obj.get('bullet_points', []))
            desc = result_obj.get('description', '')
            kb_content = f"标题：{title}\n卖点：{bullets}\n描述：{desc}"
            _auto_save_style_to_kb(
                _merchant(), title, kb_content,
                data.get('platform'), data.get('language')
            )
        return jsonify({'success': True, 'data': {'id': rec_id}})
    except Exception as e:
        log_error('copywriter.history_add', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history/<int:rec_id>', methods=['DELETE'])
def history_delete(rec_id):
    try:
        delete_copywriter_record(_merchant(), rec_id)
        return jsonify({'success': True, 'data': {'id': rec_id}})
    except Exception as e:
        log_error('copywriter.history_delete', e)
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/history', methods=['DELETE'])
def history_clear():
    try:
        clear_copywriter_records(_merchant())
        return jsonify({'success': True, 'data': None})
    except Exception as e:
        log_error('copywriter.history_clear', e)
        return jsonify({'success': False, 'message': str(e)}), 500
