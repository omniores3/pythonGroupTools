"""
数据库迁移脚本：添加采集模式字段
运行此脚本以更新现有数据库
"""

from database.db import Database

def migrate():
    """添加 collect_mode 和 history_limit 字段到 tasks 表"""
    
    try:
        # 检查字段是否已存在
        result = Database.fetchone("PRAGMA table_info(tasks)")
        columns = [col['name'] for col in Database.fetchall("PRAGMA table_info(tasks)")]
        
        # 添加 collect_mode 字段
        if 'collect_mode' not in columns:
            print("添加 collect_mode 字段...")
            Database.execute("""
                ALTER TABLE tasks 
                ADD COLUMN collect_mode VARCHAR(20) DEFAULT 'both'
            """)
            print("✅ collect_mode 字段添加成功")
        else:
            print("ℹ️  collect_mode 字段已存在")
        
        # 添加 history_limit 字段
        if 'history_limit' not in columns:
            print("添加 history_limit 字段...")
            Database.execute("""
                ALTER TABLE tasks 
                ADD COLUMN history_limit INTEGER DEFAULT 1000
            """)
            print("✅ history_limit 字段添加成功")
        else:
            print("ℹ️  history_limit 字段已存在")
        
        print("\n✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：添加采集模式配置")
    print("=" * 60)
    print()
    
    migrate()
