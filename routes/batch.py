from flask import Blueprint, request, jsonify, Response, stream_with_context
import requests
import time
import json

batch_bp = Blueprint('batch', __name__, url_prefix='/api/batch')

@batch_bp.route('/submit', methods=['GET'])
def batch_submit():
    """批量提交数据到API - 使用SSE流式响应"""
    try:
        # 获取参数（从URL参数）
        content = request.args.get('content', '')
        api_url = request.args.get('api_url', '')
        method = request.args.get('method', 'POST').upper()
        param_name = request.args.get('param_name', 'data')
        
        # 验证参数
        if not content or not api_url:
            return jsonify({'code': 400, 'message': '内容和API地址不能为空'}), 400
        
        if method not in ['GET', 'POST']:
            return jsonify({'code': 400, 'message': '请求方法只能是GET或POST'}), 400
        
        # 按行分割内容
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return jsonify({'code': 400, 'message': '没有有效的数据行'}), 400
        
        # 使用生成器函数进行流式响应
        def generate():
            success_count = 0
            fail_count = 0
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'total': len(lines)})}\n\n"
            
            for index, line in enumerate(lines, 1):
                try:
                    # 发送处理中事件
                    yield f"data: {json.dumps({'type': 'processing', 'index': index, 'data': line})}\n\n"
                    
                    # 构建请求
                    start_time = time.time()
                    if method == 'POST':
                        response = requests.post(
                            api_url,
                            json={param_name: line},
                            timeout=30
                        )
                    else:  # GET
                        response = requests.get(
                            api_url,
                            params={param_name: line},
                            timeout=30
                        )
                    elapsed_time = time.time() - start_time
                    
                    # 记录结果
                    result = {
                        'type': 'result',
                        'index': index,
                        'data': line,
                        'status_code': response.status_code,
                        'success': 200 <= response.status_code < 300,
                        'response': response.text[:500],
                        'elapsed_time': round(elapsed_time, 2)
                    }
                    
                    # 尝试解析JSON响应
                    try:
                        result['response_json'] = response.json()
                    except:
                        result['response_json'] = None
                    
                    if result['success']:
                        success_count += 1
                    else:
                        fail_count += 1
                    
                    # 发送结果事件
                    yield f"data: {json.dumps(result)}\n\n"
                    
                    # 避免请求过快，添加小延迟
                    time.sleep(0.1)
                    
                except Exception as e:
                    fail_count += 1
                    result = {
                        'type': 'result',
                        'index': index,
                        'data': line,
                        'success': False,
                        'status_code': None,
                        'response': str(e),
                        'response_json': None,
                        'elapsed_time': 0
                    }
                    yield f"data: {json.dumps(result)}\n\n"
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete', 'success': success_count, 'fail': fail_count})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'批量提交失败: {str(e)}'}), 500
