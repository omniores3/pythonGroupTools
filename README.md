# Telegram 群组/频道采集系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

基于 Flask 的 Web 可视化 Telegram 数据采集系统

支持群组/频道搜索、消息采集、实时监听和 API 推送

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用文档](#使用文档) • [截图预览](#截图预览)

</div>

---

## 📖 项目简介

Telegram 群组/频道采集系统是一个功能强大的 Web 应用，帮助你自动化采集 Telegram 群组和频道的数据。通过直观的 Web 界面，你可以轻松管理多个 Telegram 账号、创建采集任务、实时监听消息，并将数据推送到你的 API 服务器。

### 适用场景

- 📊 **数据分析**: 采集群组消息进行舆情分析、趋势研究
- 🔍 **信息监控**: 实时监听特定群组的新消息
- 🤖 **机器人开发**: 为 Telegram 机器人提供数据源
- 📈 **市场研究**: 采集行业相关群组的讨论内容
- 🎯 **内容聚合**: 从多个频道聚合感兴趣的内容

---

## ✨ 功能特性

### 🔐 多账号管理
- 支持添加多个 Telegram 账号
- 独立的登录流程和会话管理
- 账号状态实时显示
- 灵活的活跃账号切换

### 📋 任务化管理
- 可视化创建和管理采集任务
- 支持两种采集模式：
  - **机器人搜索**: 通过搜索机器人发现群组/频道
  - **直接采集**: 采集指定群组/频道的消息
- 任务状态实时监控（待执行、运行中、已完成、失败）
- 支持启动、停止、编辑、删除任务

### 🚀 并发执行
- 多任务同时运行
- 多账号并发执行
- 每个任务可选择不同账号
- 充分利用多账号资源

### 🎯 智能过滤
- **正则表达式过滤**: 支持群组名称和消息内容的正则过滤
- **自动翻页**: 配置翻页规则自动获取更多搜索结果
- **去重处理**: 自动去除重复的群组和消息

### 📡 实时监听
- 采集历史消息（可配置数量）
- 实时监听新消息
- 三种采集模式：
  - 历史 + 实时
  - 仅历史
  - 仅实时

### 🔗 API 推送
- 自定义 API 推送地址
- 灵活的参数映射配置
- 支持 GET/POST 请求
- 失败自动重试机制

### 📊 数据管理
- 群组/频道列表查看
- 消息列表分页显示
- 关键词搜索和过滤
- 数据导出（CSV、JSON）
- 统计图表展示

### 🎨 现代化界面
- 基于 Bootstrap 5 的美观界面
- 响应式设计，支持移动端
- 实时状态更新
- 友好的错误提示

---

## 🛠️ 技术栈

- **后端**: Python 3.12 + Flask 3.x
- **数据库**: SQLite3
- **Telegram 客户端**: Telethon 1.34.0
- **前端**: Bootstrap 5 + jQuery + Chart.js
- **异步处理**: threading + asyncio

---

## 🚀 快速开始

### 环境要求

- Python 3.12 或更高版本
- pip 包管理器
- Telegram 账号

### 1. 克隆项目

```bash
git clone https://github.com/omniores3/pythonGroupTools.git
cd pythonGroupTools
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 获取 Telegram API 密钥

1. 访问 [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. 使用你的手机号登录
3. 点击 "Create new application"
4. 填写应用信息（随意填写）
5. 复制 `api_id` 和 `api_hash`

### 4. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件
# Windows: notepad .env
# Linux/Mac: nano .env
```

在 `.env` 文件中填入你的 API 密钥：

```env
# Telegram 配置（必填）
TELEGRAM_API_ID=你的api_id
TELEGRAM_API_HASH=你的api_hash
```

### 5. 检查配置（可选）

```bash
python check_config.py
```

### 6. 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动

### 7. 添加 Telegram 账号

1. 打开浏览器访问 `http://localhost:5000`
2. 点击导航栏的 "账号管理"
3. 点击 "添加账号" 按钮
4. 输入手机号（包含国家代码，如 +8613800000000）
5. 输入收到的验证码
6. （如启用了两步验证）输入两步验证密码
7. 点击 "设为活跃" 将该账号用于任务执行

---

## 📚 使用文档

### 账号管理

#### 添加账号
1. 进入 "账号管理" 页面
2. 点击 "添加账号"
3. 输入手机号并完成验证
4. 设置为活跃账号

#### 管理账号
- **设为活跃**: 将账号设为默认使用的账号
- **删除账号**: 删除账号及其会话文件

### 任务管理

#### 创建任务

**模式 1: 机器人搜索**

适用于通过搜索机器人发现群组/频道

1. 进入 "任务管理" 页面
2. 点击 "创建任务"
3. 选择账号
4. 选择任务类型：通过机器人搜索群组/频道
5. 配置参数：
   - 任务名称
   - 机器人用户名（如 @search_bot）
   - 搜索关键词（每行一个）
   - 群组名称正则过滤（可选）
   - 翻页配置（下一页按钮文字、最大页数）
6. 保存并启动任务

**模式 2: 直接采集**

适用于采集指定群组/频道的消息

1. 进入 "任务管理" 页面
2. 点击 "创建任务"
3. 选择账号
4. 选择任务类型：直接采集指定群组/频道
5. 配置参数：
   - 任务名称
   - 目标群组/频道（每行一个，支持链接或用户名）
   - 采集模式（历史+实时、仅历史、仅实时）
   - 历史消息数量
   - 消息内容正则过滤（可选）
   - API 推送配置（可选）
6. 保存并启动任务

#### 管理任务
- **启动任务**: 开始执行采集
- **停止任务**: 停止正在运行的任务
- **查看详情**: 查看任务配置和状态
- **编辑任务**: 修改任务配置（需先停止）
- **删除任务**: 删除任务（需先停止）

### 数据管理

#### 查看数据
1. 进入 "数据管理" 页面
2. 切换标签查看：
   - 群组/频道列表
   - 消息列表

#### 搜索和过滤
- 使用搜索框输入关键词
- 选择时间范围
- 按群组过滤

#### 导出数据
1. 点击 "导出数据" 按钮
2. 选择格式（CSV 或 JSON）
3. 下载文件

#### 查看统计
- 采集数量趋势图
- 群组分布图
- 消息类型统计

### API 推送配置

如果需要将采集到的数据推送到你的 API 服务器：

1. 在创建任务时展开 "API 推送配置"
2. 填写 API 地址
3. 选择请求方法（GET/POST）
4. 配置参数映射（JSON 格式）：

```json
{
  "message": "content",
  "sender": "sender_name",
  "time": "message_date",
  "group": "group_title"
}
```

左侧是你的 API 参数名，右侧是系统字段名。

---

## 📸 截图预览

### 账号管理
![账号管理](docs/screenshots/accounts.png)

### 任务管理
![任务管理](docs/screenshots/tasks.png)

### 数据展示
![数据展示](docs/screenshots/data.png)

---

## 🔧 配置说明

### 环境变量

在 `.env` 文件中配置：

```env
# Flask 配置
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
HOST=0.0.0.0
PORT=5000

# 数据库配置
DATABASE_PATH=data/telegram_collector.db

# Telegram 配置（必填）
TELEGRAM_API_ID=你的api_id
TELEGRAM_API_HASH=你的api_hash

# 目录配置
SESSION_DIR=data/sessions
LOG_DIR=logs

# 日志配置
LOG_LEVEL=INFO
```

### 正则表达式示例

**群组名称过滤**:
```regex
.*crypto.*|.*bitcoin.*|.*区块链.*
```

**消息内容过滤**:
```regex
.*价格.*|.*涨跌.*|.*行情.*
```

---

## 📁 项目结构

```
telegram-collector/
├── app.py                      # Flask 应用入口
├── config.py                   # 配置文件
├── requirements.txt            # 依赖包
├── .env                        # 环境变量（需创建）
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略文件
├── check_config.py            # 配置检查脚本
├── QUICKSTART.md              # 快速启动指南
├── README.md                  # 项目说明
│
├── database/                  # 数据库模块
│   ├── __init__.py
│   ├── db.py                 # 数据库连接
│   ├── init_db.py            # 数据库初始化
│   └── models.py             # 数据模型
│
├── services/                  # 服务层
│   ├── __init__.py
│   ├── telegram_service.py   # Telegram 客户端服务
│   ├── task_service.py       # 任务管理服务
│   ├── api_service.py        # API 推送服务
│   └── data_service.py       # 数据管理服务
│
├── routes/                    # 路由层
│   ├── __init__.py
│   ├── auth.py               # 账号管理路由
│   ├── tasks.py              # 任务管理路由
│   └── data.py               # 数据管理路由
│
├── templates/                 # 前端模板
│   ├── base.html             # 基础模板
│   ├── auth.html             # 账号管理页面
│   ├── tasks.html            # 任务管理页面
│   └── data.html             # 数据展示页面
│
├── static/                    # 静态资源
│   ├── css/
│   │   └── custom.css        # 自定义样式
│   └── js/
│       ├── auth.js           # 账号管理逻辑
│       ├── tasks.js          # 任务管理逻辑
│       └── data.js           # 数据展示逻辑
│
├── data/                      # 数据目录（自动创建）
│   ├── telegram_collector.db # SQLite 数据库
│   └── sessions/             # Telegram 会话文件
│
├── logs/                      # 日志目录（自动创建）
│   └── app.log               # 应用日志
│
└── docs/                      # 文档目录
    └── telegram-collector/   # 项目文档
```

---

## ⚠️ 注意事项

### Telegram 使用限制

1. **API 频率限制**: Telegram 对 API 调用有频率限制，请合理设置采集间隔
2. **账号安全**: 避免频繁操作导致账号被限制或封禁
3. **隐私保护**: 采集的数据可能包含隐私信息，请妥善保管
4. **使用条款**: 请遵守 Telegram 的使用条款和服务协议

### 系统资源

1. **并发任务**: 建议根据系统资源控制并发任务数量
2. **数据库大小**: 定期清理不需要的数据，避免数据库过大
3. **日志文件**: 定期清理日志文件，避免占用过多磁盘空间

### 安全建议

1. **API 密钥**: 不要将 `.env` 文件提交到版本控制
2. **生产环境**: 修改 `SECRET_KEY` 为强密码
3. **网络访问**: 如果部署到公网，建议配置防火墙和访问控制
4. **数据备份**: 定期备份数据库文件

---

## 🐛 故障排查

### 问题 1: 添加账号时提示"请先在.env文件中配置..."

**原因**: `.env` 文件不存在或未配置 API 密钥

**解决**:
```bash
# 检查配置
python check_config.py

# 如果没有 .env 文件
cp .env.example .env

# 编辑 .env 文件，填入 API 密钥
# 重启应用
```

### 问题 2: 验证码在哪里查看？

**解决**: 打开 Telegram 应用，会收到来自 Telegram 的验证码消息

### 问题 3: 任务启动失败

**可能原因**:
- 账号未登录
- 机器人用户名错误
- 群组链接无效
- 网络连接问题

**解决**: 查看日志文件 `logs/app.log` 获取详细错误信息

### 问题 4: 数据库锁定错误

**原因**: SQLite 不支持高并发写入

**解决**: 减少并发任务数量，或考虑升级到 PostgreSQL/MySQL

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 报告问题

如果你发现了 bug 或有功能建议，请[创建 Issue](https://github.com/your-username/telegram-collector/issues)

---

## 📄 开源协议

本项目采用 MIT 协议开源 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 🙏 致谢

- [Telethon](https://github.com/LonamiWebs/Telethon) - 优秀的 Telegram 客户端库
- [Flask](https://flask.palletsprojects.com/) - 轻量级 Web 框架
- [Bootstrap](https://getbootstrap.com/) - 前端 UI 框架

---

## 📮 联系方式

- 项目主页: [https://github.com/omniores3/pythonGroupTools](https://github.com/omniores3/pythonGroupTools)
- 问题反馈: [Issues](https://github.com/omniores3/pythonGroupTools/issues)
- Telegram: @easSearchs

---

## ⭐ Star History

如果这个项目对你有帮助，请给它一个 Star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/telegram-collector&type=Date)](https://star-history.com/#your-username/telegram-collector&Date)

---

<div align="center">

**[⬆ 回到顶部](#telegram-群组频道采集系统)**

Made with ❤️ by [@easSearchs](https://t.me/easSearchs)

</div>
