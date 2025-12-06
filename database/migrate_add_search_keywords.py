"""
数据库迁移脚本：添加搜索关键词字段
运行此脚本以更新现有数据库
"""

from database.db import Database

def migrate():
    """添加 search_keywords 字段到 tasks 表"""
    
    try:
        columns = [col['name'] for col in Database.fetchall("PRAGMA table_info(tasks)")]
        
        # 添加 search_keywords 字段
        if 'search_keywords' not in columns:
            print("添加 search_keywords 字段...")
            Database.execute("""
                ALTER TABLE tasks 
                ADD COLUMN search_keywords TEXT
            """)
            print("✅ search_keywords 字段添加成功")
        else:
            print("ℹ️  search_keywords 字段已存在")
        
        print("\n✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：添加搜索关键词支持")
    print("=" * 60)
    print()
    
    migrate()
