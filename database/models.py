import json
from datetime import datetime
from database.db import Database

class Account:
    """账号模型"""
    
    @staticmethod
    def create(api_id, api_hash, phone, session_file=None):
        """创建账号"""
        query = '''
            INSERT INTO accounts (api_id, api_hash, phone, session_file)
            VALUES (?, ?, ?, ?)
        '''
        return Database.execute(query, (api_id, api_hash, phone, session_file))
    
    @staticmethod
    def get_all():
        """获取所有账号"""
        query = 'SELECT * FROM accounts ORDER BY created_at DESC'
        return Database.fetchall(query)
    
    @staticmethod
    def get_by_id(account_id):
        """根据ID获取账号"""
        query = 'SELECT * FROM accounts WHERE id = ?'
        return Database.fetchone(query, (account_id,))
    
    @staticmethod
    def get_active():
        """获取活跃账号"""
        query = 'SELECT * FROM accounts WHERE is_active = 1 LIMIT 1'
        return Database.fetchone(query)
    
    @staticmethod
    def update_session(account_id, session_file):
        """更新会话文件"""
        query = 'UPDATE accounts SET session_file = ? WHERE id = ?'
        Database.execute(query, (session_file, account_id))
    
    @staticmethod
    def set_active(account_id):
        """设置活跃账号"""
        # 先停用所有账号
        query = 'UPDATE accounts SET is_active = 0'
        Database.execute(query)
        # 激活指定账号
        query = 'UPDATE accounts SET is_active = 1 WHERE id = ?'
        Database.execute(query, (account_id,))
    
    @staticmethod
    def deactivate_all():
        """停用所有账号"""
        query = 'UPDATE accounts SET is_active = 0'
        Database.execute(query)
    
    @staticmethod
    def delete(account_id):
        """删除账号"""
        # 先获取账号信息，删除session文件
        account = Account.get_by_id(account_id)
        if account and account['session_file']:
            import os
            if os.path.exists(account['session_file']):
                try:
                    os.remove(account['session_file'])
                except:
                    pass
        
        # 删除数据库记录
        query = 'DELETE FROM accounts WHERE id = ?'
        Database.execute(query, (account_id,))

class Task:
    """任务模型"""
    
    @staticmethod
    def create(account_id, name, task_type='bot_search', bot_username=None, search_keywords=None,
               target_groups=None, group_regex=None, message_regex=None, collect_mode='both', 
               history_limit=1000, pagination_config=None, api_config=None):
        """创建任务"""
        query = '''
            INSERT INTO tasks (account_id, name, task_type, bot_username, search_keywords,
                             target_groups, group_regex, message_regex, collect_mode, 
                             history_limit, pagination_config, api_config)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        search_keywords_json = json.dumps(search_keywords) if search_keywords else None
        target_groups_json = json.dumps(target_groups) if target_groups else None
        pagination_json = json.dumps(pagination_config) if pagination_config else None
        api_json = json.dumps(api_config) if api_config else None
        
        return Database.execute(query, (
            account_id, name, task_type, bot_username, search_keywords_json,
            target_groups_json, group_regex, message_regex, collect_mode, 
            history_limit, pagination_json, api_json
        ))
    
    @staticmethod
    def get_by_id(task_id):
        """根据ID获取任务"""
        query = 'SELECT * FROM tasks WHERE id = ?'
        task = Database.fetchone(query, (task_id,))
        if task:
            task['pagination_config'] = json.loads(task['pagination_config']) if task['pagination_config'] else {}
            task['api_config'] = json.loads(task['api_config']) if task['api_config'] else {}
        return task
    
    @staticmethod
    def get_all(page=1, page_size=50):
        """获取所有任务（分页）"""
        offset = (page - 1) * page_size
        query = 'SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?'
        tasks = Database.fetchall(query, (page_size, offset))
        
        for task in tasks:
            task['pagination_config'] = json.loads(task['pagination_config']) if task['pagination_config'] else {}
            task['api_config'] = json.loads(task['api_config']) if task['api_config'] else {}
        
        return tasks
    
    @staticmethod
    def update(task_id, **kwargs):
        """更新任务"""
        allowed_fields = ['name', 'task_type', 'bot_username', 'search_keywords', 'target_groups', 
                         'group_regex', 'message_regex', 'collect_mode', 'history_limit', 
                         'pagination_config', 'api_config', 'status']
        
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key in ['pagination_config', 'api_config'] and value:
                    value = json.dumps(value)
                updates.append(f'{key} = ?')
                values.append(value)
        
        if not updates:
            return
        
        updates.append('updated_at = ?')
        values.append(datetime.now().isoformat())
        values.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        Database.execute(query, tuple(values))
    
    @staticmethod
    def delete(task_id):
        """删除任务"""
        query = 'DELETE FROM tasks WHERE id = ?'
        Database.execute(query, (task_id,))
    
    @staticmethod
    def count():
        """获取任务总数"""
        query = 'SELECT COUNT(*) as count FROM tasks'
        result = Database.fetchone(query)
        return result['count'] if result else 0

class Group:
    """群组模型"""
    
    @staticmethod
    def create(task_id, telegram_id, title, username=None, description=None, member_count=0):
        """创建群组记录"""
        query = '''
            INSERT OR IGNORE INTO groups (task_id, telegram_id, title, username, description, member_count)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        return Database.execute(query, (task_id, telegram_id, title, username, description, member_count))
    
    @staticmethod
    def get_by_telegram_id(telegram_id):
        """根据Telegram ID获取群组"""
        query = 'SELECT * FROM groups WHERE telegram_id = ?'
        return Database.fetchone(query, (telegram_id,))
    
    @staticmethod
    def get_all(filters=None, page=1, page_size=50):
        """获取所有群组（分页）"""
        offset = (page - 1) * page_size
        query = 'SELECT * FROM groups'
        params = []
        
        if filters:
            conditions = []
            if filters.get('task_id'):
                conditions.append('task_id = ?')
                params.append(filters['task_id'])
            if filters.get('keyword'):
                conditions.append('(title LIKE ? OR username LIKE ?)')
                keyword = f"%{filters['keyword']}%"
                params.extend([keyword, keyword])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([page_size, offset])
        
        return Database.fetchall(query, tuple(params))
    
    @staticmethod
    def count(filters=None):
        """获取群组总数"""
        query = 'SELECT COUNT(*) as count FROM groups'
        params = []
        
        if filters:
            conditions = []
            if filters.get('task_id'):
                conditions.append('task_id = ?')
                params.append(filters['task_id'])
            if filters.get('keyword'):
                conditions.append('(title LIKE ? OR username LIKE ?)')
                keyword = f"%{filters['keyword']}%"
                params.extend([keyword, keyword])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        
        result = Database.fetchone(query, tuple(params) if params else None)
        return result['count'] if result else 0

class Message:
    """消息模型"""
    
    @staticmethod
    def create(group_id, telegram_message_id, sender_id, sender_name, content,
               media_type='text', message_date=None):
        """创建消息记录"""
        query = '''
            INSERT OR IGNORE INTO messages 
            (group_id, telegram_message_id, sender_id, sender_name, content, media_type, message_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return Database.execute(query, (
            group_id, telegram_message_id, sender_id, sender_name,
            content, media_type, message_date
        ))
    
    @staticmethod
    def get_all(filters=None, page=1, page_size=50):
        """获取所有消息（分页）"""
        offset = (page - 1) * page_size
        query = '''
            SELECT m.*, g.title as group_title, g.username as group_username
            FROM messages m
            LEFT JOIN groups g ON m.group_id = g.id
        '''
        params = []
        
        if filters:
            conditions = []
            if filters.get('group_id'):
                conditions.append('m.group_id = ?')
                params.append(filters['group_id'])
            if filters.get('keyword'):
                conditions.append('m.content LIKE ?')
                params.append(f"%{filters['keyword']}%")
            if filters.get('start_date'):
                conditions.append('m.message_date >= ?')
                params.append(filters['start_date'])
            if filters.get('end_date'):
                conditions.append('m.message_date <= ?')
                params.append(filters['end_date'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY m.message_date DESC LIMIT ? OFFSET ?'
        params.extend([page_size, offset])
        
        return Database.fetchall(query, tuple(params))
    
    @staticmethod
    def count(filters=None):
        """获取消息总数"""
        query = 'SELECT COUNT(*) as count FROM messages m'
        params = []
        
        if filters:
            conditions = []
            if filters.get('group_id'):
                conditions.append('m.group_id = ?')
                params.append(filters['group_id'])
            if filters.get('keyword'):
                conditions.append('m.content LIKE ?')
                params.append(f"%{filters['keyword']}%")
            if filters.get('start_date'):
                conditions.append('m.message_date >= ?')
                params.append(filters['start_date'])
            if filters.get('end_date'):
                conditions.append('m.message_date <= ?')
                params.append(filters['end_date'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        
        result = Database.fetchone(query, tuple(params) if params else None)
        return result['count'] if result else 0

class APILog:
    """API日志模型"""
    
    @staticmethod
    def create(task_id, message_id, url, method, request_data, status_code=None,
               response=None, success=False):
        """创建API日志"""
        query = '''
            INSERT INTO api_logs (task_id, message_id, url, method, request_data,
                                status_code, response, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        request_json = json.dumps(request_data) if request_data else None
        
        return Database.execute(query, (
            task_id, message_id, url, method, request_json,
            status_code, response, success
        ))
    
    @staticmethod
    def get_by_task(task_id, page=1, page_size=50):
        """获取任务的API日志"""
        offset = (page - 1) * page_size
        query = '''
            SELECT * FROM api_logs 
            WHERE task_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        logs = Database.fetchall(query, (task_id, page_size, offset))
        
        for log in logs:
            log['request_data'] = json.loads(log['request_data']) if log['request_data'] else {}
        
        return logs
