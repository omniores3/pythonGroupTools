from flask import Blueprint, request, jsonify
import asyncio
from database.models import Task, Account
from services.task_service import task_service
from services.telegram_service import telegram_service

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@tasks_bp.route('', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    
    tasks = Task.get_all(page, page_size)
    total = Task.count()
    
    # 为每个任务添加账号信息
    for task in tasks:
        account = Account.get_by_id(task['account_id'])
        if account:
            task['account_phone'] = account['phone']
        else:
            task['account_phone'] = '未知'
    
    return jsonify({
        'code': 200,
        'data': {
            'tasks': tasks,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    })

@tasks_bp.route('', methods=['POST'])
def create_task():
    """创建任务"""
    data = request.json
    
    # 验证必填字段
    required_fields = ['name', 'bot_username']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'code': 400, 'message': f'{field}不能为空'}), 400
    
    # 获取账号ID（如果指定了account_id则使用指定的，否则使用活跃账号）
    account_id = data.get('account_id')
    if account_id:
        account = Account.get_by_id(account_id)
        if not account:
            return jsonify({'code': 400, 'message': '指定的账号不存在'}), 400
    else:
        # 使用活跃账号
        account = Account.get_active()
        if not account:
            return jsonify({'code': 400, 'message': '请先设置活跃账号或指定账号'}), 400
        account_id = account['id']
    
    # 创建任务
    task_id = task_service.create_task(
        account_id=account_id,
        name=data['name'],
        task_type=data.get('task_type', 'bot_search'),
        bot_username=data.get('bot_username'),
        search_keywords=data.get('search_keywords'),
        target_groups=data.get('target_groups'),
        group_regex=data.get('group_regex'),
        message_regex=data.get('message_regex'),
        collect_mode=data.get('collect_mode', 'both'),
        history_limit=data.get('history_limit', 1000),
        pagination_config=data.get('pagination_config'),
        api_config=data.get('api_config')
    )
    
    return jsonify({
        'code': 200,
        'message': '任务创建成功',
        'data': {'task_id': task_id}
    })

@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    task = Task.get_by_id(task_id)
    
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在'}), 404
    
    return jsonify({
        'code': 200,
        'data': task
    })

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    task = Task.get_by_id(task_id)
    
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在'}), 404
    
    # 检查任务是否在运行
    if task['status'] == 'running':
        return jsonify({'code': 400, 'message': '请先停止任务'}), 400
    
    data = request.json
    Task.update(task_id, **data)
    
    return jsonify({
        'code': 200,
        'message': '任务更新成功'
    })

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    task = Task.get_by_id(task_id)
    
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在'}), 404
    
    # 检查任务是否在运行
    if task['status'] == 'running':
        return jsonify({'code': 400, 'message': '请先停止任务'}), 400
    
    Task.delete(task_id)
    
    return jsonify({
        'code': 200,
        'message': '任务删除成功'
    })

@tasks_bp.route('/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动任务"""
    task = Task.get_by_id(task_id)
    
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在'}), 404
    
    result = task_service.start_task(task_id)
    
    if result['status'] == 'success':
        return jsonify({'code': 200, 'message': result['message']})
    else:
        return jsonify({'code': 400, 'message': result['message']}), 400

@tasks_bp.route('/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止任务"""
    task = Task.get_by_id(task_id)
    
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在'}), 404
    
    result = task_service.stop_task(task_id)
    
    if result['status'] == 'success':
        return jsonify({'code': 200, 'message': result['message']})
    else:
        return jsonify({'code': 400, 'message': result['message']}), 400

@tasks_bp.route('/<int:task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    status = task_service.get_task_status(task_id)
    
    if not status:
        return jsonify({'code': 404, 'message': '任务不存在'}), 404
    
    return jsonify({
        'code': 200,
        'data': status
    })


@tasks_bp.route('/available-accounts', methods=['GET'])
def get_available_accounts():
    """获取可用的账号列表（已登录的账号）"""
    try:
        accounts = Account.get_all()
        available_accounts = []
        
        for account in accounts:
            # 检查登录状态
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                is_logged_in = loop.run_until_complete(
                    telegram_service.is_logged_in(account['id'])
                )
            finally:
                loop.close()
            
            if is_logged_in:
                available_accounts.append({
                    'id': account['id'],
                    'phone': account['phone'],
                    'is_active': account['is_active']
                })
        
        return jsonify({
            'code': 200,
            'data': available_accounts
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'获取账号列表失败: {str(e)}'}), 500
