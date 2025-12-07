from flask import Blueprint, request, jsonify
import requests
import time

batch_bp = Blueprint('batch', __name__, url_prefix='/api/batch')

@batch_bp.route('/submit', methods=['POST'])
def batch_submit():
    """批量提交数据到API"""
    try:
        data = request.json
        
        # 获取参数
        content = data.get('content', '')
        api_url = data.get('api_url', '')
        method = data.get('method', 'POST').upper()
        param_name = data.get('param_name', 'data')
        
        # 验证参数
        if not content or not api_url:
            return jsonify({'code': 400, 'message': '内容和API地址不能为空'}), 400
        
        if method not in ['GET', 'POST']:
            return jsonify({'code': 400, 'message': '请求方法只能是GET或POST'}), 400
        
        # 按行分割内容
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return jsonify({'code': 400, 'message': '没有有效的数据行'}), 400
        
        # 批量提交
        results = []
        success_count = 0
        fail_count = 0
        
        for index, line in enumerate(lines, 1):
            try:
                # 构建请求
                if method == 'POST':
                    response = requests.post(
                        api_url,
                        json={param_name: line},
                        timeout=10
                    )
                else:  # GET
                    response = requests.get(
                        api_url,
                        params={param_name: line},
                        timeout=10
                    )
                
                # 记录结果
                result = {
                    'index': index,
                    'data': line,
                    'status_code': response.status_code,
                    'success': 200 <= response.status_code < 300,
                    'response': response.text[:500]  # 保存响应内容（限制长度）
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
                
                results.append(result)
                
                # 避免请求过快，添加小延迟
                time.sleep(0.1)
                
            except Exception as e:
                fail_count += 1
                results.append({
                    'index': index,
                    'data': line,
                    'success': False,
                    'status_code': None,
                    'response': str(e),
                    'response_json': None
                })
        
        return jsonify({
            'code': 200,
            'message': f'提交完成：成功 {success_count} 条，失败 {fail_count} 条',
            'data': {
                'total': len(lines),
                'success': success_count,
                'fail': fail_count,
                'results': results
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'批量提交失败: {str(e)}'}), 500
