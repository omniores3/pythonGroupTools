from flask import Flask, render_template
from config import Config, config
from database.init_db import init_database
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.data import data_bp
from routes.batch import batch_bp
import logging
import os

def create_app(config_name='default'):
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化配置
    Config.init_app()
    
    # 初始化数据库
    init_database()
    
    # 配置日志
    setup_logging()
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(batch_bp)
    
    # 注册路由
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/auth')
    def auth():
        return render_template('auth.html')
    
    @app.route('/tasks')
    def tasks():
        return render_template('tasks.html')
    
    @app.route('/data')
    def data():
        return render_template('data.html')
    
    @app.route('/batch')
    def batch():
        return render_template('batch.html')
    
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
    app = create_app()
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║   Telegram群组/频道采集系统                               ║
    ║   访问地址: http://{Config.HOST}:{Config.PORT}                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
