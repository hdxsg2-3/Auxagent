"""轻量定时任务调度器（零依赖，应用内轮询）"""
import threading
import time
import json
from datetime import datetime
from utils.db import DEFAULT_MERCHANT, list_compliance_records, list_logistics_documents
from services.llm_service import LLMService

_tasks = {}
_lock = threading.Lock()
_llm = LLMService()


def add_task(task_id, task_type, description, interval_minutes, callback, merchant_id=DEFAULT_MERCHANT):
    """添加一个周期性任务"""
    with _lock:
        _tasks[task_id] = {
            'id': task_id,
            'type': task_type,
            'description': description,
            'interval_minutes': interval_minutes,
            'callback': callback,
            'merchant_id': merchant_id,
            'last_run': None,
            'next_run': None,
            'last_result': None,
            'status': 'active',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }


def remove_task(task_id):
    with _lock:
        if task_id in _tasks:
            del _tasks[task_id]


def get_all_tasks():
    with _lock:
        result = []
        for task in _tasks.values():
            item = dict(task)
            item.pop('callback', None)
            result.append(item)
        return result


def run_task(task_id):
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            return {'success': False, 'message': '任务不存在'}
    try:
        result = task['callback']()
        result_str = str(result)
        with _lock:
            task['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            task['last_result'] = result_str
        return {'success': True, 'result': result_str}
    except Exception as e:
        with _lock:
            task['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            task['last_result'] = str(e)
        return {'success': False, 'message': str(e)}


def _scheduler_loop():
    """后台轮询执行到期任务"""
    while True:
        time.sleep(30)
        with _lock:
            now = datetime.now()
            for task_id, task in list(_tasks.items()):
                if task['status'] != 'active':
                    continue
                if task['last_run']:
                    last = datetime.strptime(task['last_run'], '%Y-%m-%d %H:%M:%S')
                    if (now - last).total_seconds() < task['interval_minutes'] * 60:
                        continue
                try:
                    task['last_run'] = now.strftime('%Y-%m-%d %H:%M:%S')
                    task['last_result'] = task['callback']()
                except Exception as e:
                    task['last_result'] = str(e)


# 启动后台调度线程
_scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
_scheduler_thread.start()


# ---- 预置巡检任务回调 ----
def _compliance_audit():
    """合规巡检：检查最近的上架商品合规状态"""
    records = list_compliance_records(DEFAULT_MERCHANT)[:20]
    high_risk = sum(1 for r in records if 'high' in str(r.get('result_json', '')).lower())
    return f'扫描 {len(records)} 条记录，发现 {high_risk} 条高风险'


def _logistics_sweep():
    """物流巡检：检查滞留的物流单据"""
    docs = list_logistics_documents(DEFAULT_MERCHANT) or []
    stalled = [d for d in docs if d.get('status') not in ('delivered', '')]
    return f'共 {len(docs)} 单，{len(stalled)} 单未签收'


# 注册默认巡检任务
add_task('compliance-audit', 'compliance', '每小时自动合规巡检', 60, _compliance_audit)
add_task('logistics-sweep', 'logistics', '每天物流状态巡检', 1440, _logistics_sweep)
