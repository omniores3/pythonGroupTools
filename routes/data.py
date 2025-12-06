from flask import Blueprint, request, jsonify, send_file
from services.data_service import DataService

data_bp = Blueprint('data', __name__, url_prefix='/api/data')

@data_bp.route('/groups', methods=['GET'])
def get_groups():
    """获取群组列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    task_id = request.args.get('task_id', type=int)
    keyword = request.args.get('keyword')
    
    filters = {}
    if task_id:
        filters['task_id'] = task_id
    if keyword:
        filters['keyword'] = keyword
    
    result = DataService.get_groups(filters, page, page_size)
    
    return jsonify({
        'code': 200,
        'data': result
    })

@data_bp.route('/messages', methods=['GET'])
def get_messages():
    """获取消息列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    group_id = request.args.get('group_id', type=int)
    keyword = request.args.get('keyword')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    filters = {}
    if group_id:
        filters['group_id'] = group_id
    if keyword:
        filters['keyword'] = keyword
    if start_date:
        filters['start_date'] = start_date
    if end_date:
        filters['end_date'] = end_date
    
    result = DataService.get_messages(filters, page, page_size)
    
    return jsonify({
        'code': 200,
        'data': result
    })

@data_bp.route('/search', methods=['GET'])
def search():
    """搜索数据"""
    keyword = request.args.get('keyword')
    
    if not keyword:
        return jsonify({'code': 400, 'message': '关键词不能为空'}), 400
    
    result = DataService.search(keyword)
    
    return jsonify({
        'code': 200,
        'data': result
    })

@data_bp.route('/export', methods=['GET'])
def export():
    """导出数据"""
    data_type = request.args.get('type', 'messages')  # groups or messages
    format_type = request.args.get('format', 'csv')  # csv or json
    
    # 获取过滤条件
    filters = {}
    if request.args.get('group_id'):
        filters['group_id'] = int(request.args.get('group_id'))
    if request.args.get('task_id'):
        filters['task_id'] = int(request.args.get('task_id'))
    if request.args.get('keyword'):
        filters['keyword'] = request.args.get('keyword')
    
    filepath = DataService.export_data(data_type, format_type, filters)
    
    if not filepath:
        return jsonify({'code': 400, 'message': '导出失败'}), 400
    
    return send_file(filepath, as_attachment=True)

@data_bp.route('/statistics', methods=['GET'])
def statistics():
    """获取统计数据"""
    stats = DataService.get_statistics()
    
    return jsonify({
        'code': 200,
        'data': stats
    })
