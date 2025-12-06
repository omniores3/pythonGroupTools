# 多账号管理改造方案

## 改造目标
将系统从单账号改造为多账号管理，支持：
- 账号列表展示
- 添加新账号（走完整登录流程）
- 删除账号
- 切换活跃账号
- 每个账号独立的session管理

## 改造内容

### 1. 数据库层改造
**无需修改** - 现有的accounts表已经支持多账号，只需要：
- 移除 `get_active()` 的 `LIMIT 1` 限制
- 添加 `get_all()` 方法获取所有账号
- 添加 `get_by_id()` 方法
- 添加 `delete()` 方法
- 添加 `set_active()` 方法切换活跃账号

### 2. 服务层改造
**TelegramService** 需要支持多实例：
- 改为支持多个client实例（每个账号一个）
- 使用字典管理多个client：`{account_id: client}`
- 登录时指定account_id
- 操作时指定使用哪个account_id的client

### 3. 路由层改造
**auth.py** 需要调整：
- `/api/auth/accounts` - GET 获取账号列表
- `/api/auth/accounts` - POST 添加新账号（登录流程）
- `/api/auth/accounts/:id` - DELETE 删除账号
- `/api/auth/accounts/:id/activate` - POST 设置为活跃账号
- `/api/auth/verify` - 验证时需要account_id参数

### 4. 前端改造
**auth.html** 需要重新设计：
- 显示账号列表（表格形式）
- 每个账号显示：手机号、状态（已登录/未登录）、活跃标记、操作按钮
- 添加账号按钮 → 弹出模态框 → 输入api_id、api_hash、phone → 登录流程
- 删除账号按钮
- 设置为活跃账号按钮

## 实施步骤

1. ✅ 修改 `database/models.py` - Account模型增加方法
2. ✅ 修改 `services/telegram_service.py` - 支持多client管理
3. ✅ 修改 `routes/auth.py` - 新增账号管理API
4. ✅ 修改 `templates/auth.html` - 账号列表界面
5. ✅ 修改 `static/js/auth.js` - 前端逻辑
6. ✅ 测试完整流程

## 兼容性
- 任务管理保持不变（任务关联account_id）
- 现有数据库数据兼容
- 现有任务继续使用原账号
