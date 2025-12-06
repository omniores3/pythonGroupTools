# Telegram群组/频道采集系统 - 待办事项

## 🔧 必须完成的配置

### 1. 获取Telegram API密钥 ⚠️
**重要性**: 🔴 必须  
**步骤**:
1. 访问 https://my.telegram.org/apps
2. 使用您的Telegram账号登录
3. 创建一个新的应用
4. 记录 `api_id` 和 `api_hash`

**说明**: 没有API密钥无法使用系统

---

### 2. 安装Python依赖 ⚠️
**重要性**: 🔴 必须  
**命令**:
```bash
pip install -r requirements.txt
```

**可能遇到的问题**:
- 如果安装失败，尝试使用国内镜像源:
  ```bash
  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

---

### 3. 配置环境变量（可选）
**重要性**: 🟡 可选  
**步骤**:
```bash
cp .env.example .env
# 编辑 .env 文件，修改配置项
```

**说明**: 也可以在Web界面直接配置，不是必须的

---

## 🧪 需要测试的功能

### 1. Telegram登录测试
**测试步骤**:
1. 运行 `python app.py`
2. 访问 http://localhost:5000/auth
3. 输入 api_id、api_hash 和手机号
4. 输入收到的验证码
5. 如有两步验证，输入密码

**预期结果**: 显示"已登录"状态

---

### 2. 任务创建测试
**测试步骤**:
1. 访问 http://localhost:5000/tasks
2. 点击"创建任务"
3. 填写任务配置
4. 保存任务

**预期结果**: 任务列表中显示新创建的任务

---

### 3. 采集功能测试
**测试步骤**:
1. 创建一个测试任务
2. 配置一个已知的机器人用户名
3. 启动任务
4. 等待采集完成

**预期结果**: 
- 任务状态变为"运行中"
- 数据管理页面显示采集到的群组和消息

---

### 4. API推送测试（如需要）
**前提条件**: 需要一个可用的API端点

**测试步骤**:
1. 准备一个测试API（可以使用 https://webhook.site 获取临时URL）
2. 在任务配置中填写API地址
3. 启动任务
4. 检查API是否收到推送数据

**预期结果**: API端点收到正确格式的数据

---

## 🐛 可能遇到的问题

### 问题1: 端口被占用
**错误信息**: `Address already in use`  
**解决方案**:
- 修改 `.env` 文件中的 `PORT` 配置
- 或者在 `app.py` 中修改端口号

---

### 问题2: 数据库文件权限错误
**错误信息**: `unable to open database file`  
**解决方案**:
```bash
mkdir -p data/sessions
mkdir -p logs
chmod 755 data
```

---

### 问题3: Telethon安装失败
**错误信息**: `Failed building wheel for cryptg`  
**解决方案**:
- Windows: 安装 Visual C++ Build Tools
- Linux: `sudo apt-get install python3-dev`
- Mac: `xcode-select --install`

---

### 问题4: 登录时网络超时
**错误信息**: `Connection timeout`  
**解决方案**:
- 检查网络连接
- 确认可以访问Telegram服务器
- 如在国内，可能需要代理

---

## 📋 可选的优化配置

### 1. 配置日志级别
**文件**: `.env`  
**配置项**: `LOG_LEVEL=DEBUG`  
**说明**: 开发时可设置为DEBUG，生产环境建议INFO或WARNING

---

### 2. 修改数据库路径
**文件**: `.env`  
**配置项**: `DATABASE_PATH=/path/to/your/database.db`  
**说明**: 默认在 `data/` 目录，可以修改到其他位置

---

### 3. 调整分页大小
**文件**: `config.py`  
**配置项**: `PAGE_SIZE = 50`  
**说明**: 根据数据量调整每页显示的记录数

---

### 4. 修改API重试次数
**文件**: `config.py`  
**配置项**: `API_MAX_RETRIES = 3`  
**说明**: 根据API稳定性调整重试次数

---

## 🚀 生产环境部署（如需要）

### 1. 使用WSGI服务器
**推荐**: Gunicorn (Linux) 或 Waitress (Windows)

**安装**:
```bash
pip install gunicorn  # Linux
pip install waitress  # Windows
```

**运行**:
```bash
# Linux
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Windows
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

---

### 2. 配置Nginx反向代理（可选）
**配置示例**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

### 3. 设置系统服务（可选）
**创建服务文件**: `/etc/systemd/system/telegram-collector.service`

```ini
[Unit]
Description=Telegram Collector
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/telegram-collector
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务**:
```bash
sudo systemctl enable telegram-collector
sudo systemctl start telegram-collector
```

---

## 📝 测试清单

完成以下测试后，在方框中打勾：

### 基础功能
- [ ] 成功安装所有依赖
- [ ] 应用可以正常启动
- [ ] 可以访问Web界面
- [ ] 数据库自动创建成功

### 账号管理
- [ ] 可以输入API密钥
- [ ] 验证码发送成功
- [ ] 登录流程完整
- [ ] 登录状态显示正确

### 任务管理
- [ ] 可以创建任务
- [ ] 可以编辑任务
- [ ] 可以删除任务
- [ ] 可以启动任务
- [ ] 可以停止任务

### 数据采集
- [ ] 可以搜索机器人消息
- [ ] 可以提取群组链接
- [ ] 可以采集历史消息
- [ ] 正则过滤正常工作
- [ ] 数据正确保存到数据库

### 数据管理
- [ ] 群组列表显示正常
- [ ] 消息列表显示正常
- [ ] 搜索功能正常
- [ ] 导出CSV成功
- [ ] 导出JSON成功
- [ ] 统计图表显示正确

### API推送（如配置）
- [ ] 数据推送成功
- [ ] 参数映射正确
- [ ] 重试机制正常
- [ ] 日志记录完整

---

## 🎯 下一步行动

### 立即执行
1. ✅ 获取Telegram API密钥
2. ✅ 安装Python依赖
3. ✅ 运行应用并测试登录

### 短期计划
1. 创建测试任务
2. 验证采集功能
3. 检查数据完整性

### 长期计划
1. 根据实际使用情况优化配置
2. 监控系统性能
3. 定期备份数据库

---

## 📞 需要帮助？

如果遇到问题：
1. 查看 `logs/app.log` 日志文件
2. 参考 `README.md` 常见问题部分
3. 检查 `FINAL_telegram-collector.md` 故障排查章节

---

**文档版本**: v1.0  
**创建时间**: 2025-12-03  
**状态**: 📝 待完成
