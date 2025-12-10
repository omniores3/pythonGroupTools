import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = False  # 暂时关闭调试模式解决模板加载问题
    
    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/telegram_collector.db')
    
    # Telegram配置
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')
    
    # 目录配置
    SESSION_DIR = os.getenv('SESSION_DIR', 'data/sessions')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # 分页配置
    PAGE_SIZE = 50
    
    # API推送配置
    API_TIMEOUT = 30
    API_MAX_RETRIES = 3
    API_RETRY_DELAY = [1, 3, 5]
    
    # 任务配置
    MAX_PAGINATION_PAGES = 10
    MESSAGE_FETCH_LIMIT = 1000
    
    @staticmethod
    def init_app():
        """初始化应用配置"""
        # 确保必要的目录存在
        os.makedirs(Config.SESSION_DIR, exist_ok=True)
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    
    @staticmethod
    def validate():
        """验证配置"""
        errors = []
        
        if not Config.SECRET_KEY or Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            if Config.FLASK_ENV == 'production':
                errors.append('SECRET_KEY must be set in production')
        
        return errors

# 配置字典（用于Flask app.config.from_object）
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
