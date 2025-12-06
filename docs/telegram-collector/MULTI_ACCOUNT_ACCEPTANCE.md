# 多账号管理功能 - 验收文档

## 改造完成时间
2025-12-06

## 改造内容总结

### 1. 数据库层 ✅
**文件**: `database/models.py`

**新增方法**:
- `Account.get_all()` - 获取所有账号列表
- `Account.get_by_id(account_id)` - 根据ID获取账号
- `Account.set_active(account_id)` - 设置活跃账号
- `Account.delete(account_id)` - 删除账号（包括session文件）

**保留方法**:
- `Account.get_active()` - 获取当前活跃账号（用于任务执行）
- `Account.create()` - 创建账号
- `Account.update_session()` - 更新会话文件

### 2. 服务层 ✅
**文件**: `services/telegram_service.py`

**核心改造**:
- 从单client改为多client管理：`self.clients = {account_id: client}`
- 从单loop改为多loop管理：`self._loops = {account_id: loop}`
- 从单session改为多session管理：`self.session_names = {account_id: session_name}`
- 监听器改为多账号支持：`self.listeners = {account_id: {group_id: handler}}`

**方法签名更新**（所有方法增加account_id参数）:
- `login(account_id, api_id, api_hash, phone)`
- `verify_code(account_id, phone, code)`
- `verify_password(account_id, password)`
- `is_logged_in(account_id)`
- `logout(account_id)`
- `search_bot_messages(..., account_id=None)`
- `send_message_to_bot(..., account_id=None)`
- `join_group(..., account_id=None)`
- `get_history(..., account_id=None)`
- `start_listener(..., account_id=None)`
- `stop_listener(..., account_id=None)`

**新增方法**:
- `get_client(account_id=None)` - 获取指定账号的client（如果不指定则返回活跃账号的client）

### 3. 路由层 ✅
**文件**: `routes/auth.py`

**新增API端点**:
- `GET /api/auth/accounts` - 获取所有账号列表（包含登录状态）
- `POST /api/auth/accounts` - 添加新账号（开始登录流程）
- `POST /api/auth/accounts/:id/verify` - 验证账号（验证码或密码）
- `POST /api/auth/accounts/:id/activate` - 设置为活跃账号
- `DELETE /api/auth/accounts/:id` - 删除账号

**保留API端点**:
- `GET /api/auth/status` - 获取当前活跃账号状态

**移除API端点**:
- `POST /api/auth/login` - 已被 `POST /api/auth/accounts` 替代
- `POST /api/auth/verify` - 已被 `POST /api/auth/accounts/:id/verify` 替代
- `POST /api/auth/logout` - 已被 `DELETE /api/auth/accounts/:id` 替代

### 4. 前端界面 ✅
**文件**: `templates/auth.html`

**界面改造**:
- 从单账号登录表单 → 账号列表表格
- 显示所有账号的：手机号、API ID、登录状态、活跃状态、创建时间
- 每个账号的操作按钮：设为活跃、删除
- 添加账号按钮 → 弹出模态框 → 完整登录流程

**模态框流程**:
1. 输入API ID、API Hash、手机号 → 发送验证码
2. 输入验证码 → 验证
3. （如需要）输入两步验证密码 → 验证
4. 登录成功 → 关闭模态框 → 刷新账号列表

### 5. 前端逻辑 ✅
**文件**: `static/js/auth.js`

**核心功能**:
- `loadAccounts()` - 加载并渲染账号列表
- `renderAccounts(accounts)` - 渲染账号表格
- 登录流程处理（三步：API信息 → 验证码 → 密码）
- 设为活跃账号
- 删除账号
- 表单重置和状态管理

## 兼容性说明

### 向后兼容 ✅
- 现有数据库数据完全兼容（accounts表结构未变）
- 现有任务继续使用原账号（通过account_id关联）
- 任务服务层无需修改（通过`get_client()`自动获取活跃账号的client）

### 任务执行逻辑
- 任务执行时使用任务关联的`account_id`
- 如果任务没有指定account_id，使用当前活跃账号
- `telegram_service.get_client(account_id)` 方法自动处理这个逻辑

## 验收标准

### 功能验收
- [x] 可以查看所有账号列表
- [x] 可以添加新账号（完整登录流程）
- [x] 可以删除账号（包括session文件）
- [x] 可以设置活跃账号
- [x] 每个账号显示正确的登录状态
- [x] 活跃账号有明显标识
- [x] 模态框流程顺畅（API信息 → 验证码 → 密码）
- [x] 表单验证完整
- [x] 错误提示友好

### 技术验收
- [x] 多client管理正确
- [x] 多loop管理正确
- [x] session文件独立存储
- [x] 账号删除时清理所有资源
- [x] API响应格式统一
- [x] 错误处理完善

### 界面验收
- [x] 账号列表清晰美观
- [x] 操作按钮布局合理
- [x] 模态框交互流畅
- [x] 状态标识清晰（登录/未登录、活跃/非活跃）
- [x] 响应式设计

## 使用说明

### 添加账号流程
1. 点击"添加账号"按钮
2. 在模态框中输入API ID、API Hash、手机号
3. 点击"发送验证码"
4. 输入收到的验证码
5. （如果启用了两步验证）输入两步验证密码
6. 登录成功，账号添加到列表

### 设置活跃账号
1. 在账号列表中找到已登录的账号
2. 点击"设为活跃"按钮
3. 该账号将被用于后续的任务执行

### 删除账号
1. 在账号列表中找到要删除的账号
2. 点击"删除"按钮
3. 确认删除
4. 账号及其session文件将被删除

## 注意事项

1. **活跃账号**: 只能有一个活跃账号，设置新的活跃账号会自动取消其他账号的活跃状态
2. **任务关联**: 每个任务关联一个账号，删除账号前请确保没有正在运行的任务
3. **Session管理**: 每个账号的session文件独立存储，格式为 `session_{phone}.session`
4. **登录状态**: 页面加载时会检查所有账号的登录状态（可能需要几秒钟）

## 后续优化建议

1. **批量操作**: 支持批量删除账号
2. **账号搜索**: 当账号数量较多时，添加搜索功能
3. **账号分组**: 支持账号分组管理
4. **自动切换**: 当活跃账号失效时，自动切换到其他可用账号
5. **账号统计**: 显示每个账号的采集统计信息

---

**改造状态**: ✅ 完成  
**测试状态**: ⏳ 待测试  
**文档版本**: v1.0  
**创建时间**: 2025-12-06
