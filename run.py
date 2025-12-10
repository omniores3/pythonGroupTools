#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本 - 强制重新加载所有模块
"""
import sys
import os

# 禁用字节码缓存
sys.dont_write_bytecode = True

# 清除已导入的模块
modules_to_remove = [m for m in sys.modules.keys() if m.startswith('app') or m.startswith('routes') or m.startswith('services')]
for module in modules_to_remove:
    del sys.modules[module]

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 导入并运行
from flask import Flask, render_template
from config import Config, config
from database.init_db import init_database
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.data import data_bp
from routes.batch import batch_bp
import logging

def create_app(config_name='default'):
    """创建Flask应用"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    app = Flask(__name__,
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))
    
    app.config.from_object(config[config_name])
    Config.init_app()
    init_database()
    
    # 配置日志
    log_file = os.path.join(Config.LOG_DIR, 'app.log')
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(batch_bp)
    
    # 页面路由
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

if __name__ == '__main__':
    app = create_app()
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║   Telegram群组/频道采集系统                               ║
    ║   访问地址: http://{Config.HOST}:{Config.PORT}                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    if not Config.DEBUG:
        import webbrowser
        import threading
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(f'http://localhost:{Config.PORT}')
        threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
