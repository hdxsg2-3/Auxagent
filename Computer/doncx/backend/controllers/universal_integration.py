"""通用店铺自动对接模块 —— 编排控制器。

提供一站式全自动对接 API：
1. 智能选择最优路径：真实 API → 浏览器自动化兜底 → LocalShop
2. 全自动上架演示：从 AI 生成文案 → 自动上架到指定平台
3. 消息自动收发演示：拉取消息 → AI 生成回复 → 自动发送
4. 浏览器自动化兜底状态查询
5. 一键创建 LocalShop 演示店铺

核心设计：
- 全程不用付费、不用等待平台人工审核
- 优先使用 LocalShop（零配置即时可用）做演示
- 当用户有真实平台凭证时自动切换到真实 API
- 当 API 不可用时自动降级到浏览器自动化兜底
"""
import json
import time
import logging
from flask import Blueprint, request, jsonify

from platforms import get_platform, PLATFORM_CLASSES, BROWSER_FALLBACK_PLATFORMS
from platforms.browser_fallback import BrowserFallback, is_playwright_available
from platforms.local_shop import LocalShopPlatform, _init_local_db, _local_conn
from utils.db import (
    list_shops, get_shop, add_shop, add_shop_log,
    add_message, message_exists, DEFAULT_MERCHANT
)
from services.llm_service import LLMService

logger = logging.getLogger(__name__)
bp = Blueprint('universal_integration', __name__)


def _merchant():
    return request.args.get('merchant_id', DEFAULT_MERCHANT) or DEFAULT_MERCHANT


@bp.route('/status', methods=['GET'])
def integration_status():
    """获取通用对接模块的全局状态。"""
    shops = list_shops(_merchant())

    # 按平台分组统计
    platform_stats = {}
    for s in shops:
        p = s['platform']
        if p not in platform_stats:
            platform_stats[p] = {'total': 0, 'active': 0, 'mock': 0}
        platform_stats[p]['total'] += 1
        if s['status'] == 'active':
            platform_stats[p]['active'] += 1
        try:
            creds = json.loads(s.get('credentials_json') or '{}')
            if creds.get('mock', True):
                platform_stats[p]['mock'] += 1
        except Exception:
            pass

    # 浏览器自动化状态
    browser_status = {
        'playwright_available': is_playwright_available(),
        'supported_platforms': BROWSER_FALLBACK_PLATFORMS,
        'message': 'Playwright 已安装，支持真实浏览器自动化兜底' if is_playwright_available()
                   else 'Playwright 未安装，浏览器自动化使用模拟模式（安装 playwright 可启用真实浏览器操作）',
    }

    # 支持的平台列表
    supported_platforms = []
    platform_info = {
        'local-shop': {
            'name': 'LocalShop 测试平台',
            'type': 'free_instant',
            'description': '内建免费电商平台，零配置即时开通，真实数据持久化',
            'requires_credentials': False,
            'requires_approval': False,
            'cost': '免费',
            'instant': True,
        },
        'ebay': {
            'name': 'eBay（Sandbox）',
            'type': 'free_sandbox',
            'description': 'eBay 开发者 Sandbox，免费真实上架，返回真实 Item ID',
            'requires_credentials': True,
            'requires_approval': False,
            'cost': '免费（Sandbox）/ 按成交付费（正式）',
            'instant': True,
        },
        'amazon': {
            'name': 'Amazon SP-API',
            'type': 'real_api',
            'description': 'Amazon Selling Partner API，需开发者注册审核',
            'requires_credentials': True,
            'requires_approval': True,
            'cost': '$39.99/月（专业卖家）',
            'instant': False,
        },
        'temu': {
            'name': 'Temu 开放平台',
            'type': 'real_api',
            'description': 'Temu 卖家开放 API，需商家审核',
            'requires_credentials': True,
            'requires_approval': True,
            'cost': '免费（但有入驻审核）',
            'instant': False,
        },
    }
    for p in PLATFORM_CLASSES:
        supported_platforms.append({
            'platform': p,
            **platform_info.get(p, {}),
        })

    return jsonify({
        'success': True,
        'data': {
            'platform_stats': platform_stats,
            'total_shops': len(shops),
            'browser_automation': browser_status,
            'supported_platforms': supported_platforms,
            'recommended': 'local-shop',
        }
    })


@bp.route('/create-demo-shop', methods=['POST'])
def create_demo_shop():
    """一键创建 LocalShop 演示店铺（零配置即时开通）。"""
    data = request.get_json() or {}
    name = data.get('name', 'LocalShop 演示店铺')
    region = data.get('region', 'global')

    # 检查是否已有 LocalShop 店铺
    shops = list_shops(_merchant())
    for s in shops:
        if s['platform'] == 'local-shop':
            return jsonify({
                'success': True,
                'data': {'id': s['id'], 'existing': True},
                'message': '已有 LocalShop 店铺，直接使用',
            })

    # 创建 LocalShop 店铺（凭证只需要标记 mock=false）
    credentials = {'mock': False, 'platform': 'local-shop'}
    shop_id = add_shop(
        _merchant(),
        'local-shop',
        name,
        region,
        json.dumps(credentials, ensure_ascii=False)
    )

    # 初始化 LocalShop 数据
    _init_local_db()
    platform = LocalShopPlatform(shop_id, credentials, mock=False)
    result = platform.test_connection()

    add_shop_log(shop_id, 'create_demo_shop', '{}',
                 json.dumps(result, ensure_ascii=False), 'success')

    return jsonify({
        'success': True,
        'data': {'id': shop_id, 'connection_test': result},
        'message': 'LocalShop 演示店铺创建成功，即时可用',
    })


@bp.route('/browser-fallback/status', methods=['GET'])
def browser_fallback_status():
    """查询浏览器自动化兜底方案的状态。"""
    platform = request.args.get('platform', 'amazon')
    fallback = BrowserFallback(platform)
    status = fallback.get_status()

    # 返回该平台的操作步骤预览
    from platforms.browser_fallback import PLATFORM_CONFIGS
    config = PLATFORM_CONFIGS.get(platform, {})
    steps_preview = {
        'create_listing': config.get('steps_create_listing', []),
        'get_messages': config.get('steps_get_messages', []),
        'send_message': config.get('steps_send_message', []),
    }

    return jsonify({
        'success': True,
        'data': {
            **status,
            'steps_preview': steps_preview,
        }
    })


@bp.route('/browser-fallback/execute', methods=['POST'])
def browser_fallback_execute():
    """通过浏览器自动化执行操作（兜底方案）。"""
    data = request.get_json() or {}
    platform = data.get('platform', 'amazon')
    action = data.get('action', '')  # create_listing / get_messages / send_message
    payload = data.get('payload', {})

    if platform not in BROWSER_FALLBACK_PLATFORMS:
        return jsonify({
            'success': False,
            'message': f'浏览器自动化不支持平台: {platform}，支持: {BROWSER_FALLBACK_PLATFORMS}'
        }), 400

    fallback = BrowserFallback(platform, data.get('credentials', {}))

    try:
        if action == 'create_listing':
            result = fallback.create_listing(payload)
        elif action == 'get_messages':
            result = fallback.get_messages(**payload)
        elif action == 'send_message':
            result = fallback.send_message(payload)
        else:
            return jsonify({'success': False, 'message': f'不支持的操作: {action}'}), 400

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"Browser fallback execute error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/auto-demo', methods=['POST'])
def auto_demo():
    """全自动演示：一键完成 上架 + 消息收发 全链路。

    请求参数：
    - shop_id: 指定店铺 ID（可选，不传则自动创建/使用 LocalShop）
    - product_info: 商品信息（可选，不传则使用 AI 生成）
    - use_browser_fallback: 是否使用浏览器自动化兜底（默认 false）

    执行流程：
    1. 确定目标店铺（指定 / 自动创建 LocalShop）
    2. AI 生成商品文案（如未提供 product_info）
    3. 自动上架到目标平台
    4. 拉取买家消息
    5. AI 生成回复
    6. 自动发送回复
    7. 返回完整演示报告
    """
    data = request.get_json() or {}
    merchant_id = _merchant()
    shop_id = data.get('shop_id')
    product_info = data.get('product_info')
    use_browser_fallback = data.get('use_browser_fallback', False)
    target_platform = data.get('platform', 'local-shop')

    demo_report = {
        'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'steps': [],
        'shop': None,
        'listing': None,
        'messages': [],
        'replies': [],
        'errors': [],
    }

    def _add_step(name, status, detail):
        demo_report['steps'].append({
            'step': len(demo_report['steps']) + 1,
            'name': name,
            'status': status,
            'detail': detail,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        })

    try:
        # ===== 步骤 1: 确定目标店铺 =====
        if shop_id:
            shop = get_shop(merchant_id, shop_id)
            if not shop:
                return jsonify({'success': False, 'message': f'店铺 {shop_id} 不存在'}), 404
        else:
            # 自动查找或创建 LocalShop 店铺
            shops = list_shops(merchant_id)
            local_shop = next((s for s in shops if s['platform'] == 'local-shop'), None)
            if local_shop:
                shop = local_shop
                shop_id = shop['id']
            else:
                # 创建 LocalShop 演示店铺
                credentials = {'mock': False, 'platform': 'local-shop'}
                shop_id = add_shop(
                    merchant_id, 'local-shop',
                    'LocalShop 自动演示店铺', 'global',
                    json.dumps(credentials, ensure_ascii=False)
                )
                shop = get_shop(merchant_id, shop_id)

        demo_report['shop'] = {
            'id': shop['id'],
            'platform': shop['platform'],
            'name': shop['name'],
        }
        _add_step('确定目标店铺', 'success',
                  f'店铺: {shop["name"]} (平台: {shop["platform"]}, ID: {shop["id"]})')

        # ===== 步骤 2: 准备商品信息 =====
        if not product_info:
            # 使用 AI 生成商品文案
            try:
                llm = LLMService()
                default_desc = 'Portable LED Camping Lantern with USB Charging, 1000 lumens, IPX4 waterproof, built-in 5200mAh battery'
                ai_result = llm.generate_copywriter(
                    default_desc, 'amazon', 'en',
                    auto_compliance=False
                )
                product_info = {
                    'sku': f'AUTO-{int(time.time())}',
                    'title': ai_result.get('title', 'Auto-Generated Product Listing'),
                    'bullet_points': ai_result.get('bullet_points', []),
                    'description': ai_result.get('description', ''),
                    'price': 29.99,
                    'stock': 100,
                    'product_type': 'GENERAL',
                }
                _add_step('AI 生成商品文案', 'success',
                          f'标题: {product_info["title"][:60]}...')
            except Exception as e:
                logger.warning(f"AI copywriter failed, using default: {e}")
                product_info = {
                    'sku': f'AUTO-{int(time.time())}',
                    'title': 'Premium Wireless Bluetooth Earbuds with Active Noise Cancellation',
                    'bullet_points': [
                        'Active noise cancellation up to 35dB for immersive audio',
                        'Bluetooth 5.3 technology for stable, low-latency connection',
                        '36-hour total battery life with fast-charging case',
                        'IPX5 sweat and water resistant - perfect for workouts',
                        'Touch controls with voice assistant support',
                    ],
                    'description': 'Experience premium sound quality with active noise cancellation. These wireless earbuds deliver crystal-clear audio, deep bass, and 36 hours of total playtime. The ergonomic design ensures a comfortable fit for all-day wear.',
                    'price': 39.99,
                    'stock': 200,
                    'product_type': 'ELECTRONICS',
                }
                _add_step('AI 生成商品文案', 'fallback',
                          f'AI 生成失败，使用默认商品信息: {str(e)[:80]}')
        else:
            _add_step('准备商品信息', 'success', '使用用户提供的商品信息')

        # ===== 步骤 3: 自动上架 =====
        if use_browser_fallback and shop['platform'] in BROWSER_FALLBACK_PLATFORMS:
            # 使用浏览器自动化兜底
            fallback = BrowserFallback(shop['platform'])
            listing_result = fallback.create_listing(product_info)
            _add_step('浏览器自动化上架', 'success',
                      f'方式: {listing_result["mode"]}, Listing ID: {listing_result.get("listing_id", "N/A")}')
        else:
            # 使用平台适配器
            adapter = get_platform(shop)
            listing_result = adapter.create_listing(product_info)
            method = 'Mock 模拟' if adapter.mock else '真实 API'
            _add_step(f'自动上架 ({method})', 'success' if listing_result.get('success') else 'error',
                      f'{listing_result.get("message", "")}')

        demo_report['listing'] = listing_result
        add_shop_log(shop_id, 'auto_demo_listing',
                     json.dumps(product_info, ensure_ascii=False),
                     json.dumps(listing_result, ensure_ascii=False),
                     'success' if listing_result.get('success') else 'error')

        # ===== 步骤 4: 拉取买家消息 =====
        if use_browser_fallback and shop['platform'] in BROWSER_FALLBACK_PLATFORMS:
            fallback = BrowserFallback(shop['platform'])
            msg_result = fallback.get_messages()
            messages = msg_result.get('messages', [])
            _add_step('浏览器自动化拉取消息', 'success',
                      f'获取到 {len(messages)} 条消息')
        else:
            adapter = get_platform(shop)
            messages = adapter.get_messages()
            _add_step('拉取买家消息', 'success',
                      f'获取到 {len(messages)} 条消息')

        demo_report['messages'] = messages

        # 消息入库：只保存买家发来的 inbound 消息，避免把已发送的 AI 回复再当新问题导入
        imported_count = 0
        for msg in messages:
            if msg.get('direction', 'inbound') == 'outbound':
                continue
            buyer_id = msg.get('buyer_id', '')
            message_body = msg.get('body') or msg.get('content', '')
            order_id = msg.get('order_id', '') or ''
            if message_exists(merchant_id, buyer_id, message_body, order_id):
                continue
            add_message(
                merchant_id,
                msg.get('buyer_name') or buyer_id or 'unknown',
                message_body,
                shop['platform'],
                'platform',
                order_id,
                buyer_id
            )
            imported_count += 1

        # ===== 步骤 5 & 6: AI 回复 + 发送 =====
        if messages:
            # 只取 inbound（买家发来的）消息，排除已发送的 outbound 回复
            inbound_messages = [m for m in messages if m.get('direction') != 'outbound']
            llm = LLMService()
            for msg in inbound_messages[:3]:  # 最多处理 3 条入站消息
                try:
                    # AI 生成回复
                    ai_reply = llm.process_customer_service(
                        msg.get('body', ''),
                        shop['platform']
                    )

                    if not ai_reply or 'error' in ai_reply:
                        reply_text = 'Thank you for your message. We will look into this and get back to you shortly.'
                        reply_zh = ''
                    else:
                        reply_text = ai_reply.get('response', 'Thank you for your message. We will look into this and get back to you shortly.')
                        reply_zh = ai_reply.get('response_zh', '')

                    # 发送回复
                    if use_browser_fallback and shop['platform'] in BROWSER_FALLBACK_PLATFORMS:
                        fallback = BrowserFallback(shop['platform'])
                        send_result = fallback.send_message({
                            'order_id': msg.get('order_id', ''),
                            'buyer_id': msg.get('buyer_id', ''),
                            'text': reply_text,
                        })
                    else:
                        adapter = get_platform(shop)
                        send_result = adapter.send_message({
                            'order_id': msg.get('order_id', ''),
                            'buyer_id': msg.get('buyer_id', ''),
                            'text': reply_text,
                        })

                    demo_report['replies'].append({
                        'original_message': msg.get('body', '')[:100],
                        'buyer': msg.get('buyer_name') or msg.get('buyer_id'),
                        'ai_reply': reply_text,
                        'reply_zh': reply_zh,
                        'send_result': send_result,
                    })
                    _add_step(f'AI 回复 + 发送 ({msg.get("buyer_name", msg.get("buyer_id", "买家"))})',
                              'success' if send_result.get('success') else 'error',
                              f'回复: {reply_text[:60]}...')

                except Exception as e:
                    logger.error(f"Auto reply failed: {e}")
                    demo_report['errors'].append({
                        'step': 'auto_reply',
                        'message': str(e),
                    })
                    _add_step(f'AI 回复 + 发送 ({msg.get("buyer_name", "买家")})',
                              'error', str(e)[:100])
        else:
            _add_step('AI 自动回复', 'skipped', '无消息需要回复')

        # ===== 完成报告 =====
        demo_report['completed_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        demo_report['success'] = len(demo_report['errors']) == 0
        demo_report['summary'] = {
            'total_steps': len(demo_report['steps']),
            'successful_steps': sum(1 for s in demo_report['steps'] if s['status'] == 'success'),
            'listing_created': bool(demo_report['listing'] and demo_report['listing'].get('success')),
            'messages_received': len(demo_report['messages']),
            'replies_sent': len(demo_report['replies']),
            'errors': len(demo_report['errors']),
        }

        return jsonify({'success': True, 'data': demo_report})

    except Exception as e:
        logger.error(f"Auto demo failed: {e}", exc_info=True)
        demo_report['errors'].append({'step': 'global', 'message': str(e)})
        demo_report['completed_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        demo_report['success'] = False
        return jsonify({'success': False, 'data': demo_report, 'message': str(e)}), 500


@bp.route('/local-shop/products/<int:shop_id>', methods=['GET'])
def local_shop_products(shop_id):
    """查看 LocalShop 店铺的商品列表。"""
    shop = get_shop(_merchant(), shop_id)
    if not shop or shop['platform'] != 'local-shop':
        return jsonify({'success': False, 'message': 'LocalShop 店铺不存在'}), 404

    platform = LocalShopPlatform(shop_id, {}, mock=False)
    products = platform.list_products()
    return jsonify({'success': True, 'data': products})


@bp.route('/local-shop/stats/<int:shop_id>', methods=['GET'])
def local_shop_stats(shop_id):
    """查看 LocalShop 店铺的统计数据。"""
    shop = get_shop(_merchant(), shop_id)
    if not shop or shop['platform'] != 'local-shop':
        return jsonify({'success': False, 'message': 'LocalShop 店铺不存在'}), 404

    platform = LocalShopPlatform(shop_id, {}, mock=False)
    stats = platform.get_stats()
    return jsonify({'success': True, 'data': stats})
