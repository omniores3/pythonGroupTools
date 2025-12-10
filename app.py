from flask import Flask, render_template
from config import Config, config
from database.init_db import init_database
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.data import data_bp
from routes.batch import batch_bp
import logging
import os
import sys

def create_app(config_name='default'):
    """创建Flask应用 - 纯API模式"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 启用CORS支持Vue前端
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化配置
    Config.init_app()
    
    # 初始化数据库
    init_database()
    
    # 配置日志
    setup_logging()
    
    # 注册API蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(batch_bp)
    
    # 健康检查接口
    @app.route('/')
    def index():
        return {'status': 'ok', 'message': 'Telegram Collector API Server'}
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'version': '1.0.0'}
    
    return app

def setup_logging():
    """配置日志"""
    log_file = os.path.join(Config.LOG_DIR, 'app.log')
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

if __name__ == '__main__':
    # 强制重新加载，避免缓存问题
    import sys
    if 'app' in sys.modules:
        del sys.modules['app']
    
    app = create_app()
    
    # 打印启动信息
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║   Telegram群组/频道采集系统                               ║
    ║   访问地址: http://{Config.HOST}:{Config.PORT}                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # 自动打开浏览器（仅在非调试模式下）
    if not Config.DEBUG:
        import webbrowser
        import threading
        def open_browser():
            import time
            time.sleep(1.5)  # 等待服务器启动
            webbrowser.open(f'http://localhost:{Config.PORT}')
        threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
