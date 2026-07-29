import json
from flask import Blueprint, request, jsonify
from platforms import get_platform
from utils.db import (
    add_shop, list_shops, get_shop, update_shop, delete_shop,
    update_shop_status, add_shop_log, list_shop_logs, add_message, message_exists,
    add_published_listing, list_published_listings, get_published_listing,
    update_published_listing, delete_published_listing, get_shop as db_get_shop,
    DEFAULT_MERCHANT
)
from utils.validator import validate_request, ShopCreateSchema, ShopUpdateSchema, ShopPublishSchema, ShopSendMessageSchema

bp = Blueprint('platforms', __name__)


def _merchant():
    return request.args.get('merchant_id', DEFAULT_MERCHANT) or DEFAULT_MERCHANT


def _credentials_summary(credentials_json):
    """返回凭证摘要，不暴露密钥值。"""
    try:
        creds = json.loads(credentials_json or '{}')
        return {k: '***' if v else '' for k, v in creds.items()}
    except Exception:
        return {}


def _shop_to_dict(shop):
    return {
        'id': shop['id'],
        'merchant_id': shop['merchant_id'],
        'platform': shop['platform'],
        'name': shop['name'],
        'region': shop['region'],
        'status': shop['status'],
        'last_error': shop['last_error'],
        'credentials_summary': _credentials_summary(shop.get('credentials_json')),
        'created_at': shop['created_at'],
        'updated_at': shop['updated_at']
    }


@bp.route('/shops', methods=['GET'])
def get_shops():
    rows = list_shops(_merchant())
    return jsonify({'success': True, 'data': [_shop_to_dict(r) for r in rows]})


@bp.route('/shops', methods=['POST'])
def create_shop():
    data = request.get_json() or {}
    validation = validate_request(ShopCreateSchema, data)
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    credentials = data.get('credentials') or {}
    # 如果提供了真实凭证（client_id + client_secret），自动关闭 mock
    if credentials.get('client_id') and credentials.get('client_secret'):
        credentials['mock'] = False
    else:
        credentials.setdefault('mock', True)
    shop_id = add_shop(
        _merchant(),
        data['platform'],
        data['name'],
        data.get('region', ''),
        json.dumps(credentials, ensure_ascii=False)
    )
    return jsonify({'success': True, 'data': {'id': shop_id}, 'message': '店铺创建成功'})


@bp.route('/shops/<int:shop_id>', methods=['GET'])
def get_shop_by_id(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404
    return jsonify({
        'success': True,
        'data': {
            'id': shop['id'],
            'merchant_id': shop['merchant_id'],
            'platform': shop['platform'],
            'name': shop['name'],
            'region': shop['region'],
            'status': shop['status'],
            'last_error': shop['last_error'],
            'credentials': json.loads(shop.get('credentials_json') or '{}'),
            'created_at': shop['created_at'],
            'updated_at': shop['updated_at']
        }
    })


@bp.route('/shops/<int:shop_id>', methods=['PUT'])
def put_shop(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404

    data = request.get_json() or {}
    validation = validate_request(ShopUpdateSchema, data)
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    existing = json.loads(shop.get('credentials_json') or '{}')
    if 'credentials' in data and data['credentials']:
        new_creds = data['credentials']
        # 合并：新值覆盖旧值，未提供的保持原值（留空则保留原值）
        for k, v in new_creds.items():
            if v or k not in existing:
                existing[k] = v
        # 如果提供了真实凭证，自动关闭 mock
        if existing.get('client_id') and existing.get('client_secret'):
            existing['mock'] = False
        else:
            existing.setdefault('mock', data.get('mock', existing.get('mock', True)))
    credentials_json = json.dumps(existing, ensure_ascii=False)

    update_shop(
        _merchant(), shop_id,
        data.get('platform', shop['platform']),
        data.get('name', shop['name']),
        data.get('region', shop['region']),
        credentials_json,
        data.get('status', shop['status'])
    )
    return jsonify({'success': True, 'message': '店铺更新成功'})


@bp.route('/shops/<int:shop_id>', methods=['DELETE'])
def remove_shop(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404
    delete_shop(_merchant(), shop_id)
    return jsonify({'success': True, 'message': '店铺已删除'})


@bp.route('/shops/<int:shop_id>/test', methods=['POST'])
def test_shop(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404

    try:
        adapter = get_platform(shop)
        result = adapter.test_connection()
        status = 'active' if result.get('success') else 'error'
        update_shop_status(_merchant(), shop_id, status, result.get('message', ''))
        add_shop_log(shop_id, 'test_connection', '{}', json.dumps(result, ensure_ascii=False), 'success' if result.get('success') else 'error')
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        update_shop_status(_merchant(), shop_id, 'error', str(e))
        add_shop_log(shop_id, 'test_connection', '{}', '{}', 'error', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/shops/<int:shop_id>/sync-products', methods=['POST'])
def sync_products(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404

    try:
        adapter = get_platform(shop)
        result = adapter.list_products()
        add_shop_log(shop_id, 'sync_products', '{}', json.dumps(result, ensure_ascii=False), 'success')
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        add_shop_log(shop_id, 'sync_products', '{}', '{}', 'error', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/shops/<int:shop_id>/sync-messages', methods=['POST'])
def sync_messages(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404

    try:
        adapter = get_platform(shop)
        messages = adapter.get_messages()
        created_ids = []
        skipped = 0
        for msg in messages:
            # 跳过卖家/系统自己发出的消息，避免把 AI 回复当成新的客户咨询导入
            direction = msg.get('direction', 'inbound')
            if direction == 'outbound':
                skipped += 1
                continue

            buyer_id = msg.get('buyer_id', '')
            message_body = msg.get('body') or msg.get('content', '')
            order_id = msg.get('order_id', '')

            # 去重：已存在相同买家 + 相同内容 + 相同订单的消息不再重复导入
            if message_exists(_merchant(), buyer_id, message_body, order_id):
                skipped += 1
                continue

            msg_id = add_message(
                _merchant(),
                msg.get('buyer_name') or f"{shop['platform']}_buyer",
                message_body,
                shop['platform'],
                'platform',
                order_id,
                buyer_id
            )
            created_ids.append(msg_id)
        add_shop_log(shop_id, 'sync_messages', '{}', json.dumps({'count': len(created_ids), 'skipped': skipped, 'ids': created_ids}), 'success')
        return jsonify({'success': True, 'data': {'messages': messages, 'imported': created_ids, 'skipped': skipped}})
    except Exception as e:
        add_shop_log(shop_id, 'sync_messages', '{}', '{}', 'error', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/shops/<int:shop_id>/publish-listing', methods=['POST'])
def publish_listing(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404

    data = request.get_json() or {}
    validation = validate_request(ShopPublishSchema, data)
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    try:
        adapter = get_platform(shop)
        result = adapter.create_listing(data)
        status = 'success' if result.get('success') else 'error'

        # 持久化到 published_listings 表
        bullet_points_json = json.dumps(data.get('bullet_points') or [], ensure_ascii=False)
        images_json = json.dumps(data.get('images') or [], ensure_ascii=False)
        result_meta_json = json.dumps(result, ensure_ascii=False)
        listing_id = add_published_listing(
            merchant_id=_merchant(),
            shop_id=shop_id,
            platform=shop['platform'],
            sku=data.get('sku', ''),
            title=data.get('title', ''),
            bullet_points_json=bullet_points_json,
            description=data.get('description', ''),
            price=data.get('price', 0),
            stock=data.get('stock', 0),
            product_type=data.get('product_type', ''),
            images_json=images_json,
            listing_status='active' if result.get('success') else 'error',
            platform_listing_id=result.get('listing_id', ''),
            result_meta_json=result_meta_json,
        )

        add_shop_log(shop_id, 'publish_listing', json.dumps(data, ensure_ascii=False), json.dumps(result, ensure_ascii=False), status)
        return jsonify({'success': result.get('success', False), 'data': result, 'listing_id': listing_id})
    except Exception as e:
        add_shop_log(shop_id, 'publish_listing', json.dumps(data, ensure_ascii=False), '{}', 'error', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/shops/<int:shop_id>/send-message', methods=['POST'])
def send_message(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404

    data = request.get_json() or {}
    validation = validate_request(ShopSendMessageSchema, data)
    if not validation['valid']:
        return jsonify({'success': False, 'errors': validation['errors']}), 400

    try:
        adapter = get_platform(shop)
        result = adapter.send_message(data)
        status = 'success' if result.get('success') else 'error'
        add_shop_log(shop_id, 'send_message', json.dumps(data, ensure_ascii=False), json.dumps(result, ensure_ascii=False), status)
        return jsonify({'success': result.get('success', False), 'data': result})
    except Exception as e:
        add_shop_log(shop_id, 'send_message', json.dumps(data, ensure_ascii=False), '{}', 'error', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------- Listing 管理中心 ----------------

@bp.route('/listings', methods=['GET'])
def get_listings():
    shop_id = request.args.get('shop_id', type=int)
    try:
        listings = list_published_listings(_merchant(), shop_id)
        return jsonify({'success': True, 'data': listings})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    try:
        listing = get_published_listing(_merchant(), listing_id)
        if not listing:
            return jsonify({'success': False, 'message': '商品不存在'}), 404
        return jsonify({'success': True, 'data': listing})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/listings/<int:listing_id>', methods=['PUT'])
def update_listing(listing_id):
    data = request.get_json() or {}
    try:
        existing = get_published_listing(_merchant(), listing_id)
        if not existing:
            return jsonify({'success': False, 'message': '商品不存在'}), 404

        updates = {}
        for key in ('title', 'description', 'price', 'stock', 'product_type', 'sku', 'listing_status'):
            if key in data:
                updates[key] = data[key]
        if 'bullet_points' in data:
            updates['bullet_points_json'] = json.dumps(data['bullet_points'], ensure_ascii=False)
        if 'images' in data:
            updates['images_json'] = json.dumps(data['images'], ensure_ascii=False)

        update_published_listing(_merchant(), listing_id, **updates)
        return jsonify({'success': True, 'message': '已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/listings/<int:listing_id>', methods=['DELETE'])
def delete_listing(listing_id):
    try:
        existing = get_published_listing(_merchant(), listing_id)
        if not existing:
            return jsonify({'success': False, 'message': '商品不存在'}), 404
        delete_published_listing(_merchant(), listing_id)
        return jsonify({'success': True, 'message': '已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/shops/<int:shop_id>/logs', methods=['GET'])
def get_logs(shop_id):
    shop = get_shop(_merchant(), shop_id)
    if not shop:
        return jsonify({'success': False, 'message': '店铺不存在'}), 404
    logs = list_shop_logs(shop_id)
    return jsonify({'success': True, 'data': logs})
