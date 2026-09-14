# -*- coding: utf-8 -*-
"""GEO（Generative Engine Optimization，生成式引擎优化）接口

让品牌/商品更容易被生成式 AI 引擎（ChatGPT / 豆包 / DeepSeek / Perplexity 等）
"看见、理解并主动推荐"。

本模块提供三个能力：
  1. /visibility   AI 可见度检测：模拟主流 AI 引擎的回答，评估品牌被提及与推荐情况
  2. /content      AI 友好内容生成：产出易被 AI 引用的结构化内容
  3. /prompts      AI 提问挖掘：挖掘目标买家会对 AI 提出的问题

升级版（A 档）：
  * 检测引擎：结构化多维评估（4 维度：提及次数、推荐位次、情感倾向、引用密度），
    按统一 rubric 打分，单次输出 JSON；多品牌横向对比。
  * 优化建议：每条带 priority / expected_lift / difficulty，落地可执行。
"""
from flask import Blueprint, request, jsonify
from services.llm_service import LLMService
import json
import copy

bp = Blueprint('geo', __name__)
llm = LLMService()

# 评估引擎白名单（按统一 rubric 打分，避免 LLM 自行决定维度）
ENGINES = ['ChatGPT', '豆包', 'DeepSeek', 'Perplexity']

# 评估细则（rubric）：给 LLM 一个固定刻度，减少随机性
RUBRIC = {
    "mention": {
        "0": "回答中完全未出现该品牌",
        "1": "仅在补充信息中一笔带过",
        "2": "作为可选项之一被列出",
        "3": "作为主要推荐之一被列举",
        "4": "被作为首选 / Top 推荐",
    },
    "rank": "推荐列表中的位次（1 为首位，未提及则 0）",
    "sentiment": "positive / neutral / negative",
    "citation_density": "回答里事实性陈述中引用该品牌信息占比 0-1 的小数",
}


def _parse_json_response(response):
    """从 LLM 返回文本中稳健地提取 JSON 对象"""
    if response is None:
        return None
    if isinstance(response, dict):
        return response
    text = str(response).strip()
    if text.startswith('```'):
        text = text.strip('`').strip()
        if text.lower().startswith('json'):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    start, end = text.find('{'), text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None
    return None


def _call_llm_json(prompt):
    """调用大模型并解析为 JSON，返回 (data, error)"""
    response, error = llm.client.call_llm([{'role': 'user', 'content': prompt}])
    if error:
        return None, f'AI 调用失败：{error}'
    parsed = _parse_json_response(response)
    if parsed is None:
        return None, 'AI 返回内容解析失败，请重试'
    return parsed, None


def _build_visibility_prompt(brands, keyword, platform):
    """构造可见度检测 prompt：支持多品牌横向对比，按统一 rubric 打分"""
    schema = {
        "brands": [
            {
                "name": "品牌名",
                "visibility_score": "0-100 整数，综合可见度评分",
                "mention_rank": "该品牌在 AI 推荐列表中的位次，未出现为 0",
                "recommended": "布尔值，AI 是否会主动推荐该品牌",
                "engines": [
                    {
                        "engine": "ChatGPT / 豆包 / DeepSeek / Perplexity",
                        "mention_score": "0-4 整数，按 rubric 打分",
                        "rank": "该引擎回答中的位次",
                        "sentiment": "positive / neutral / negative",
                        "citation_density": "0-1 的小数",
                        "note": "该引擎下的简要评估（30字内）"
                    }
                ],
                "strengths_in_ai": ["已被 AI 认可的优势 1", "优势 2"],
                "gaps": ["导致曝光不足的短板 1", "短板 2"]
            }
        ],
        "comparative_summary": "横向对比主品牌与竞品的差距（80字内）",
        "key_insight": "本次评估的关键洞察（40字内，告诉卖家最该先做什么）",
        "suggestions": [
            {
                "priority": "high / medium / low",
                "expected_lift": "预估可提升的可见度评分（如 +12 分）",
                "difficulty": "1 / 2 / 3（1=易，3=难）",
                "text": "具体可立即执行的优化动作（40字内）"
            }
        ]
    }
    return (
        '你是一位资深 GEO（生成式引擎优化）专家。请严格按统一 rubric 对多个品牌做横向评估，'
        '避免主观飘忽。\n\n'
        f'【评估对象】{", ".join(brands)}\n'
        f'【目标关键词 / 类目】{keyword}\n'
        f'【面向平台 / 市场】{platform}\n\n'
        '【评估 rubric】\n'
        f'- mention_score: {RUBRIC["mention"]["0"]} ~ {RUBRIC["mention"]["4"]}\n'
        '- rank: 推荐列表中的位次（1 为首位，未提及则 0）\n'
        '- sentiment: positive / neutral / negative\n'
        '- citation_density: 该品牌信息在事实陈述中的占比（0-1）\n'
        '- visibility_score = mention_score × 15 + citation_density × 30 + (10 - rank) × 4 + sentiment 加成（正+5 中+0 负-5），\n'
        '  取整后 clamp 到 0-100。\n\n'
        '【评估引擎】ChatGPT、豆包、DeepSeek、Perplexity 四个必须全部评估。\n\n'
        '【建议要求】给出 3-5 条优化建议，每条带优先级、预估提升、难度。优先级判断标准：\n'
        '- high = 短板明显、ROI 高、可在 1 周内落地\n'
        '- medium = 有价值但需要更多投入\n'
        '- low = 锦上添花或长期才能见效\n\n'
        '请严格以如下 JSON 结构返回（不要输出 JSON 以外的文字，不要 markdown 代码块）：\n'
        + json.dumps(schema, ensure_ascii=False)
    )


def _normalize_brand(b):
    """规范化单个品牌的输出：补默认值、规整引擎列表、按 rubric 计算综合分"""
    b = dict(b or {})
    b.setdefault('name', '')
    b.setdefault('engines', [])

    # 强制每台引擎都有记录（缺失则补 neutral / 0）
    by_engine = {e.get('engine'): e for e in b['engines'] if e.get('engine')}
    normalized_engines = []
    for eng in ENGINES:
        e = by_engine.get(eng, {})
        normalized_engines.append({
            'engine': eng,
            'mention_score': int(e.get('mention_score', 0) or 0),
            'rank': int(e.get('rank', 0) or 0),
            'sentiment': e.get('sentiment') or 'neutral',
            'citation_density': float(e.get('citation_density', 0) or 0),
            'note': (e.get('note') or '—')[:60],
        })
    b['engines'] = normalized_engines

    # 用 rubric 公式重算 visibility_score，保证口径一致
    agg_score = 0
    mention_max = max((e['mention_score'] for e in normalized_engines), default=0)
    rank_min = min((e['rank'] for e in normalized_engines if e['rank'] > 0), default=0)
    citation_avg = sum(e['citation_density'] for e in normalized_engines) / len(normalized_engines)
    sent_bonus = 5 if any(e['sentiment'] == 'positive' for e in normalized_engines) \
                 else -5 if any(e['sentiment'] == 'negative' for e in normalized_engines) else 0
    computed = int(round(
        mention_max * 15 + citation_avg * 30 + (10 - rank_min) * 4 + sent_bonus
    )) if rank_min > 0 else int(round(mention_max * 15 + citation_avg * 30 + sent_bonus))
    computed = max(0, min(100, computed))

    # 如果模型给的值与计算值差距过大（>15），用计算值替换，避免随机性
    try:
        model_score = int(b.get('visibility_score', 0) or 0)
    except (TypeError, ValueError):
        model_score = 0
    if abs(model_score - computed) > 15:
        b['visibility_score'] = computed
        b['_score_normalized'] = True
    else:
        b['visibility_score'] = model_score
        b['_score_normalized'] = False

    # 推荐位次取所有引擎中的最优（最小）
    ranks = [e['rank'] for e in normalized_engines if e['rank'] > 0]
    b['mention_rank'] = min(ranks) if ranks else int(b.get('mention_rank', 0) or 0)
    b['recommended'] = bool(b.get('recommended', mention_max >= 2))

    # 短板 / 优势保底
    b.setdefault('strengths_in_ai', [])
    b.setdefault('gaps', [])
    return b


def _normalize_suggestions(suggestions):
    """规范化建议：保证每条带 priority / expected_lift / difficulty / text"""
    if not isinstance(suggestions, list):
        return []
    out = []
    for s in suggestions:
        if isinstance(s, str):
            s = {'text': s}
        elif not isinstance(s, dict):
            continue
        text = (s.get('text') or s.get('suggestion') or s.get('action') or '').strip()
        if not text:
            continue
        priority = str(s.get('priority', 'medium')).lower()
        if priority not in ('high', 'medium', 'low'):
            priority = 'medium'
        diff = s.get('difficulty', 2)
        try:
            diff = max(1, min(3, int(diff)))
        except (TypeError, ValueError):
            diff = 2
        out.append({
            'priority': priority,
            'expected_lift': s.get('expected_lift') or '—',
            'difficulty': diff,
            'text': text[:120],
        })
    # 高 -> 中 -> 低 排序
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    out.sort(key=lambda x: (priority_order[x['priority']], x['difficulty']))
    return out


@bp.route('/visibility', methods=['POST'])
def visibility():
    """AI 可见度检测：支持多品牌横向对比 + 结构化多维评估 + 建议带优先级"""
    data = request.get_json() or {}
    brand = (data.get('brand') or '').strip()
    keyword = (data.get('keyword') or '').strip()
    platform = (data.get('platform') or 'Amazon').strip()
    # 支持 brands 数组（多品牌对比）；若未传则用 brand 兜底
    brands_input = data.get('brands') or []
    if not isinstance(brands_input, list):
        brands_input = []
    if brand and not brands_input:
        brands_input = [brand]
    # 兼容 {competitors:[...]} 入参
    competitors = data.get('competitors') or []
    if isinstance(competitors, list):
        for c in competitors:
            c = (c or '').strip()
            if c and c not in brands_input:
                brands_input.append(c)
    # 去空、去重、限制数量（避免 LLM 输入爆炸）
    brands_input = [b for b in brands_input if b and b.strip()]
    brands_input = list(dict.fromkeys(brands_input))[:5]

    if not brands_input:
        return jsonify({'success': False, 'message': '请至少输入 1 个品牌 / 店铺名称'}), 400
    if not keyword:
        return jsonify({'success': False, 'message': '请输入目标关键词或商品类目'}), 400

    prompt = _build_visibility_prompt(brands_input, keyword, platform)
    result, err = _call_llm_json(prompt)
    if err:
        return jsonify({'success': False, 'message': err}), 500

    # 规范化每个品牌的结果（保证 rubric 一致、引擎齐备、建议带优先级）
    raw_brands = result.get('brands') or []
    normalized = []
    for i, name in enumerate(brands_input):
        rb = next((b for b in raw_brands if (b or {}).get('name') == name), None)
        if rb is None and i < len(raw_brands):
            rb = raw_brands[i]
        rb = dict(rb or {})
        rb['name'] = name
        normalized.append(_normalize_brand(rb))

    return jsonify({
        'success': True,
        'data': {
            'brands': normalized,
            'main_brand': brand or brands_input[0],
            'comparative_summary': (result.get('comparative_summary') or '').strip()[:200],
            'key_insight': (result.get('key_insight') or '').strip()[:120],
            'suggestions': _normalize_suggestions(result.get('suggestions')),
            'keyword': keyword,
            'platform': platform,
        }
    })


@bp.route('/content', methods=['POST'])
def content():
    """AI 友好内容生成：产出易被生成式 AI 引用的结构化内容"""
    data = request.get_json() or {}
    brand = (data.get('brand') or '').strip()
    product = (data.get('product') or '').strip()
    keyword = (data.get('keyword') or '').strip()
    language = (data.get('language') or '中文').strip()

    if not product:
        return jsonify({'success': False, 'message': '请输入商品 / 服务描述'}), 400

    prompt = (
        '你是一位 GEO 内容策略专家。请把下面的商品 / 服务信息，改写成"生成式 AI 最容易抓取、'
        '引用并推荐"的权威内容。要点：结论前置、结构清晰、包含可引用的事实与数据位、'
        '覆盖用户高频提问、突出差异化。\n\n'
        f'- 品牌：{brand or "（未填写）"}\n'
        f'- 商品 / 服务：{product}\n'
        f'- 目标关键词：{keyword or "（未填写）"}\n'
        f'- 输出语言：{language}\n\n'
        '请严格以如下 JSON 结构返回（不要输出 JSON 以外的文字，不要 markdown 代码块）：\n'
        + json.dumps({
            "ai_friendly_intro": "一段结论前置、可直接被 AI 引用的品牌/商品介绍（120字内）",
            "structured_summary": "结构化信息摘要，用 3-5 个短句罗列核心事实",
            "faq": [
                {"q": "AI / 用户高频提问的问题", "a": "简洁准确的回答（60字内）"}
            ],
            "authority_points": ["可被 AI 当作依据引用的权威要点 / 数据 / 认证 1", "要点2"],
            "differentiators": ["与竞品区隔的关键差异点1", "差异点2"],
            "target_keywords": ["建议覆盖的 AI 检索关键词1", "关键词2"],
            "schema_hint": "建议补充的结构化数据标记建议（如 FAQPage / Product Schema）"
        }, ensure_ascii=False)
    )

    result, err = _call_llm_json(prompt)
    if err:
        return jsonify({'success': False, 'message': err}), 500
    return jsonify({'success': True, 'data': result})


@bp.route('/prompts', methods=['POST'])
def prompts():
    """AI 提问挖掘：挖掘目标买家会对 AI 提的问题，抢占回答位"""
    data = request.get_json() or {}
    keyword = (data.get('keyword') or '').strip()
    platform = (data.get('platform') or 'Amazon').strip()
    market = (data.get('market') or '北美').strip()

    if not keyword:
        return jsonify({'success': False, 'message': '请输入商品类目 / 关键词'}), 400

    prompt = (
        '你是一位 GEO / 用户意图分析专家。请站在目标买家角度，挖掘他们在购买前最可能向'
        '生成式 AI 助手（如 ChatGPT、豆包）提出的问题，并给出抢占 AI 回答位的建议。\n\n'
        f'- 商品类目 / 关键词：{keyword}\n'
        f'- 面向平台：{platform}\n'
        f'- 目标市场：{market}\n\n'
        '请严格以如下 JSON 结构返回（不要输出 JSON 以外的文字，不要 markdown 代码块）：\n'
        + json.dumps({
            "questions": [
                {
                    "question": "买家可能向 AI 提出的完整问题",
                    "intent": "问题背后的购买意图（20字内）",
                    "priority": "high / medium / low",
                    "difficulty": "该问题被回答的竞争难度（高/中/低）"
                }
            ],
            "clusters": [
                {"theme": "问题主题聚类名称", "keywords": ["该聚类下的关键词1", "关键词2"]}
            ],
            "recommended_targets": ["最值得优先抢占回答位的问题 / 方向1", "方向2"],
            "content_angles": ["针对上述问题，建议产出的内容角度1", "角度2"]
        }, ensure_ascii=False)
    )

    result, err = _call_llm_json(prompt)
    if err:
        return jsonify({'success': False, 'message': err}), 500
    return jsonify({'success': True, 'data': result})