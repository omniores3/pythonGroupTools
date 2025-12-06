import csv
import json
import os
from datetime import datetime, timedelta
from database.models import Group, Message
from config import Config

class DataService:
    """数据管理服务"""
    
    @staticmethod
    def get_groups(filters=None, page=1, page_size=None):
        """获取群组列表"""
        if page_size is None:
            page_size = Config.PAGE_SIZE
        
        groups = Group.get_all(filters, page, page_size)
        total = Group.count(filters)
        
        return {
            'data': groups,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    @staticmethod
    def get_messages(filters=None, page=1, page_size=None):
        """获取消息列表"""
        if page_size is None:
            page_size = Config.PAGE_SIZE
        
        messages = Message.get_all(filters, page, page_size)
        total = Message.count(filters)
        
        return {
            'data': messages,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    @staticmethod
    def search(keyword, filters=None):
        """搜索数据"""
        if filters is None:
            filters = {}
        
        filters['keyword'] = keyword
        
        # 搜索群组
        groups = Group.get_all(filters, page=1, page_size=20)
        
        # 搜索消息
        messages = Message.get_all(filters, page=1, page_size=20)
        
        return {
            'groups': groups,
            'messages': messages
        }
    
    @staticmethod
    def export_data(data_type, format_type, filters=None):
        """导出数据"""
        if data_type == 'groups':
            data = Group.get_all(filters, page=1, page_size=10000)
        elif data_type == 'messages':
            data = Message.get_all(filters, page=1, page_size=10000)
        else:
            return None
        
        if format_type == 'csv':
            return ExportService.to_csv(data, data_type)
        elif format_type == 'json':
            return ExportService.to_json(data, data_type)
        else:
            return None
    
    @staticmethod
    def get_statistics():
        """获取统计数据"""
        return StatisticsService.get_all_stats()

class ExportService:
    """导出服务"""
    
    @staticmethod
    def to_csv(data, data_type):
        """导出为CSV"""
        if not data:
            return None
        
        # 创建临时文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{data_type}_{timestamp}.csv'
        filepath = os.path.join('data', filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            if data_type == 'groups':
                fieldnames = ['id', 'title', 'username', 'description', 'member_count', 'created_at']
            else:  # messages
                fieldnames = ['id', 'group_title', 'sender_name', 'content', 'media_type', 'message_date']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        
        return filepath
    
    @staticmethod
    def to_json(data, data_type):
        """导出为JSON"""
        if not data:
            return None
        
        # 创建临时文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{data_type}_{timestamp}.json'
        filepath = os.path.join('data', filename)
        
        # 处理日期时间
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=json_serial)
        
        return filepath

class StatisticsService:
    """统计服务"""
    
    @staticmethod
    def get_all_stats():
        """获取所有统计数据"""
        return {
            'daily_stats': StatisticsService.get_daily_stats(),
            'group_distribution': StatisticsService.get_group_distribution(),
            'message_type_stats': StatisticsService.get_message_type_stats()
        }
    
    @staticmethod
    def get_daily_stats():
        """获取每日统计"""
        from database.db import Database
        
        # 最近7天的消息统计
        query = '''
            SELECT DATE(message_date) as date, COUNT(*) as count
            FROM messages
            WHERE message_date >= datetime('now', '-7 days')
            GROUP BY DATE(message_date)
            ORDER BY date
        '''
        
        results = Database.fetchall(query)
        
        # 填充缺失的日期
        stats = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
            count = 0
            for row in results:
                if row['date'] == date:
                    count = row['count']
                    break
            stats.append({'date': date, 'count': count})
        
        return stats
    
    @staticmethod
    def get_group_distribution():
        """获取群组分布"""
        from database.db import Database
        
        query = '''
            SELECT g.title, COUNT(m.id) as message_count
            FROM groups g
            LEFT JOIN messages m ON g.id = m.group_id
            GROUP BY g.id
            ORDER BY message_count DESC
            LIMIT 10
        '''
        
        return Database.fetchall(query)
    
    @staticmethod
    def get_message_type_stats():
        """获取消息类型统计"""
        from database.db import Database
        
        query = '''
            SELECT media_type, COUNT(*) as count
            FROM messages
            GROUP BY media_type
            ORDER BY count DESC
        '''
        
        return Database.fetchall(query)
