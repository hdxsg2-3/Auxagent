from flask import Blueprint, request, jsonify, send_file
from PIL import Image
import io
import os
import tempfile

bp = Blueprint('image_tools', __name__)


@bp.route('/resize', methods=['POST'])
def resize():
    """调整图片尺寸"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '请上传图片'}), 400

    width = int(request.form.get('width', 1000))
    height = int(request.form.get('height', 1000))
    quality = int(request.form.get('quality', 85))

    try:
        file = request.files['image']
        img = Image.open(file.stream)

        # 保持比例缩放到目标尺寸内
        img.thumbnail((width, height), Image.LANCZOS)

        # 转RGB（PNG可能RGBA）
        if img.mode in ('RGBA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality)
        buf.seek(0)

        return send_file(buf, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/info', methods=['POST'])
def image_info():
    """获取图片信息"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '请上传图片'}), 400
    try:
        file = request.files['image']
        img = Image.open(file.stream)
        return jsonify({
            'success': True,
            'data': {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_kb': round(img.fp.tell() / 1024, 1) if hasattr(img, 'fp') else 0,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
