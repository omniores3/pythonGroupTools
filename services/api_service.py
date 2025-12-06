import requests
import time
from config import Config
from database.models import APILog

class APIService:
    """API推送服务"""
    
    @staticmethod
    def push_data(message, api_config, task_id, message_id=None):
        """推送数据到外部API"""
        if not api_config or not api_config.get('url'):
            return False
        
        url = api_config['url']
        method = api_config.get('method', 'POST').upper()
        param_mapping = api_config.get('param_mapping', {})
        
        # 构建请求数据
        request_data = APIService._build_request_data(message, param_mapping)
        
        # 发送请求（带重试）
        success, status_code, response = APIService._send_with_retry(
            url, method, request_data
        )
        
        # 记录日志
        APILog.create(
            task_id=task_id,
            message_id=message_id,
            url=url,
            method=method,
            request_data=request_data,
            status_code=status_code,
            response=response,
            success=success
        )
        
        return success
    
    @staticmethod
    def _build_request_data(message, param_mapping):
        """构建请求数据"""
        data = {}
        
        # 默认映射
        default_mapping = {
            'content': 'content',
            'sender_id': 'sender_id',
            'sender_name': 'sender_name',
            'message_date': 'message_date',
            'media_type': 'media_type'
        }
        
        # 合并用户自定义映射
        mapping = {**default_mapping, **param_mapping}
        
        # 映射数据
        for source_key, target_key in mapping.items():
            if source_key in message:
                value = message[source_key]
                # 处理日期时间
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                data[target_key] = value
        
        return data
    
    @staticmethod
    def _send_with_retry(url, method, data):
        """发送请求（带重试机制）"""
        max_retries = Config.API_MAX_RETRIES
        retry_delays = Config.API_RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                if method == 'GET':
                    response = requests.get(
                        url,
                        params=data,
                        timeout=Config.API_TIMEOUT
                    )
                else:  # POST
                    response = requests.post(
                        url,
                        json=data,
                        timeout=Config.API_TIMEOUT
                    )
                
                # 检查响应状态
                if response.status_code < 400:
                    return True, response.status_code, response.text
                else:
                    # 4xx或5xx错误
                    if attempt < max_retries - 1:
                        time.sleep(retry_delays[attempt])
                        continue
                    return False, response.status_code, response.text
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delays[attempt])
                    continue
                return False, None, 'Request timeout'
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delays[attempt])
                    continue
                return False, None, str(e)
        
        return False, None, 'Max retries exceeded'
