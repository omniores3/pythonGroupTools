from database.db import Database

def init_database():
    """初始化数据库表结构"""
    
    # 账号表
    Database.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id VARCHAR(50) NOT NULL,
            api_hash VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            session_file VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 任务表
    Database.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            task_type VARCHAR(20) DEFAULT 'bot_search',
            bot_username VARCHAR(100),
            search_keywords TEXT,
            target_groups TEXT,
            group_regex TEXT,
            message_regex TEXT,
            collect_mode VARCHAR(20) DEFAULT 'both',
            history_limit INTEGER DEFAULT 1000,
            pagination_config TEXT,
            api_config TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    # 群组表
    Database.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            telegram_id BIGINT UNIQUE NOT NULL,
            title VARCHAR(255),
            username VARCHAR(100),
            description TEXT,
            member_count INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')
    
    # 消息表
    Database.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            telegram_message_id BIGINT NOT NULL,
            sender_id BIGINT,
            sender_name VARCHAR(255),
            content TEXT,
            media_type VARCHAR(50),
            message_date DATETIME,
            collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            UNIQUE(group_id, telegram_message_id)
        )
    ''')
    
    # API日志表
    Database.execute('''
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            message_id INTEGER,
            url VARCHAR(500),
            method VARCHAR(10),
            request_data TEXT,
            status_code INTEGER,
            response TEXT,
            success BOOLEAN,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (message_id) REFERENCES messages(id)
        )
    ''')
    
    # 创建索引
    Database.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
    Database.execute('CREATE INDEX IF NOT EXISTS idx_groups_telegram_id ON groups(telegram_id)')
    Database.execute('CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id)')
    Database.execute('CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(message_date)')
    Database.execute('CREATE INDEX IF NOT EXISTS idx_api_logs_task_id ON api_logs(task_id)')
    
    print("✅ 数据库初始化完成")

if __name__ == '__main__':
    init_database()
