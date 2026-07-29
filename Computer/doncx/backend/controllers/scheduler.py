from flask import Blueprint, jsonify, request
from services.scheduler import get_all_tasks, run_task, add_task, remove_task

bp = Blueprint('scheduler', __name__)


@bp.route('/tasks', methods=['GET'])
def list_tasks():
    try:
        tasks = get_all_tasks()
        return jsonify({'success': True, 'data': tasks})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/tasks/<task_id>/run', methods=['POST'])
def trigger_task(task_id):
    try:
        result = run_task(task_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/tasks/<task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    try:
        from services.scheduler import _tasks, _lock
        with _lock:
            task = _tasks.get(task_id)
            if not task:
                return jsonify({'success': False, 'message': '任务不存在'}), 404
            task['status'] = 'paused' if task['status'] == 'active' else 'active'
        return jsonify({'success': True, 'data': task})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
