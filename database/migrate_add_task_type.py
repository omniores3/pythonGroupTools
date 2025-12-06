"""
数据库迁移脚本：添加任务类型字段
运行此脚本以更新现有数据库
"""

from database.db import Database

def migrate():
    """添加 task_type 和 target_groups 字段到 tasks 表"""
    
    try:
        columns = [col['name'] for col in Database.fetchall("PRAGMA table_info(tasks)")]
        
        # 添加 task_type 字段
        if 'task_type' not in columns:
            print("添加 task_type 字段...")
            Database.execute("""
                ALTER TABLE tasks 
                ADD COLUMN task_type VARCHAR(20) DEFAULT 'bot_search'
            """)
            print("✅ task_type 字段添加成功")
        else:
            print("ℹ️  task_type 字段已存在")
        
        # 添加 target_groups 字段
        if 'target_groups' not in columns:
            print("添加 target_groups 字段...")
            Database.execute("""
                ALTER TABLE tasks 
                ADD COLUMN target_groups TEXT
            """)
            print("✅ target_groups 字段添加成功")
        else:
            print("ℹ️  target_groups 字段已存在")
        
        # bot_username 改为可空
        print("\nℹ️  注意: bot_username 字段现在可以为空（直接采集模式不需要）")
        
        print("\n✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：添加任务类型支持")
    print("=" * 60)
    print()
    
    migrate()
