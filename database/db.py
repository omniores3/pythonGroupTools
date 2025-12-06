import sqlite3
import threading
from contextlib import contextmanager
from config import Config

class Database:
    """数据库连接管理类"""
    
    _local = threading.local()
    
    @classmethod
    def get_connection(cls):
        """获取数据库连接（线程安全）"""
        if not hasattr(cls._local, 'connection'):
            cls._local.connection = sqlite3.connect(
                Config.DATABASE_PATH,
                check_same_thread=False
            )
            cls._local.connection.row_factory = sqlite3.Row
        return cls._local.connection
    
    @classmethod
    @contextmanager
    def get_cursor(cls):
        """获取数据库游标（上下文管理器）"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    @classmethod
    def close_connection(cls):
        """关闭数据库连接"""
        if hasattr(cls._local, 'connection'):
            cls._local.connection.close()
            delattr(cls._local, 'connection')
    
    @classmethod
    def execute(cls, query, params=None):
        """执行SQL语句"""
        with cls.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid
    
    @classmethod
    def fetchone(cls, query, params=None):
        """查询单条记录"""
        with cls.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @classmethod
    def fetchall(cls, query, params=None):
        """查询多条记录"""
        with cls.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
