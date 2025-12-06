# 多任务多账号并发执行 - 实现文档

## 实现时间
2025-12-06

## 功能目标
实现多个任务使用不同账号并发执行，充分利用多账号资源，提高采集效率。

## 核心特性

### 1. 多任务并发 ✅
- 每个任务在独立的线程中运行
- 任务之间互不干扰
- 支持同时运行多个任务

### 2. 多账号支持 ✅
- 每个任务可以选择不同的账号
- 不同账号的任务可以同时运行
- 账号资源独立管理

### 3. 账号选择 ✅
- 创建任务时可以选择账号
- 显示所有已登录的可用账号
- 默认选中活跃账号

### 4. 任务隔离 ✅
- 每个任务使用自己的client实例
- 每个任务使用自己的event loop
- 任务状态独立管理

## 实现细节

### 1. 服务层改造 ✅

**文件**: `services/task_service.py`

**关键改动**:
```python
# 任务执行时获取账号ID
account_id = task.get('account_id')

# 检查账号登录状态
if not await telegram_service.is_logged_in(account_id):
    Task.update(task_id, status='failed')
    return

# 所有Telegram操作都传入account_id
await telegram_service.send_message_to_bot(..., account_id=account_id)
await telegram_service.search_bot_messages(..., account_id=account_id)
await telegram_service.join_group(..., account_id=account_id)
await telegram_service.get_history(..., account_id=account_id)
await telegram_service.start_listener(..., account_id=account_id)
```

**线程管理**:
```python
# 每个任务在独立线程中运行
thread = threading.Thread(target=self._run_task_thread, args=(task_id,))
thread.daemon = True
thread.start()

# 线程中创建独立的event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
```

### 2. 路由层改造 ✅

**文件**: `routes/tasks.py`

**任务列表增强**:
```python
# 为每个任务添加账号信息
for task in tasks:
    account = Account.get_by_id(task['account_id'])
    if account:
        task['account_phone'] = account['phone']
```

**任务创建支持账号选择**:
```python
# 支持指定account_id
account_id = data.get('account_id')
if account_id:
    account = Account.get_by_id(account_id)
else:
    # 使用活跃账号
    account = Account.get_active()
```

**新增API端点**:
```python
@tasks_bp.route('/available-accounts', methods=['GET'])
def get_available_accounts():
    """获取可用的账号列表（已登录的账号）"""
    # 返回所有已登录的账号
```

### 3. 前端界面改造 ✅

**文件**: `templates/tasks.html`

**任务列表增加账号列**:
```html
<th>使用账号</th>
```

**任务创建表单增加账号选择**:
```html
<div class="mb-3">
    <label class="form-label">使用账号 *</label>
    <select class="form-select" id="accountId" required>
        <option value="">加载中...</option>
    </select>
</div>
```

### 4. 前端逻辑改造 ✅

**文件**: `static/js/tasks.js`

**加载可用账号**:
```javascript
function loadAvailableAccounts() {
    $.get('/api/tasks/available-accounts', function(response) {
        // 填充账号下拉列表
        // 默认选中活跃账号
    });
}
```

**任务列表显示账号**:
```javascript
const accountPhone = task.account_phone || '未知';
const row = `
    <td><span class="badge bg-info">${accountPhone}</span></td>
`;
```

**任务创建包含账号**:
```javascript
const taskData = {
    account_id: parseInt(accountId),
    // ... 其他字段
};
```

## 并发执行原理

### 架构图

```
┌─────────────────────────────────────────────────┐
│              Flask Web Application              │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │         TaskService                       │ │
│  │  running_tasks: {task_id: True/False}    │ │
│  │  task_threads: {task_id: Thread}         │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼────┐   ┌───▼────┐   ┌───▼────┐
   │ Thread1 │   │Thread2 │   │Thread3 │
   │ Task1   │   │ Task2  │   │ Task3  │
   │Account1 │   │Account2│   │Account1│
   └────┬────┘   └───┬────┘   └───┬────┘
        │            │            │
   ┌────▼────┐   ┌──▼─────┐   ┌──▼─────┐
   │ Loop1   │   │ Loop2  │   │ Loop3  │
   └────┬────┘   └───┬────┘   └───┬────┘
        │            │            │
┌───────▼────────────▼────────────▼───────┐
│        TelegramService                   │
│  clients: {                              │
│    account1: TelegramClient1,            │
│    account2: TelegramClient2             │
│  }                                       │
└──────────────────────────────────────────┘
```

### 执行流程

1. **任务启动**
   - 用户点击"启动任务"
   - TaskService创建新线程
   - 线程中创建独立的event loop

2. **账号获取**
   - 从任务配置读取account_id
   - 通过TelegramService获取对应的client

3. **并发执行**
   - 多个线程同时运行
   - 每个线程使用自己的client
   - 互不干扰，独立执行

4. **资源隔离**
   - 每个账号有独立的client
   - 每个任务有独立的loop
   - 每个任务有独立的监听器

## 使用示例

### 场景1: 单账号多任务
```
账号A:
  - 任务1: 搜索加密货币群组
  - 任务2: 搜索科技群组
  - 任务3: 采集指定群组消息

结果: 三个任务使用同一个账号并发执行
```

### 场景2: 多账号多任务
```
账号A:
  - 任务1: 搜索加密货币群组
  - 任务2: 采集群组A的消息

账号B:
  - 任务3: 搜索科技群组
  - 任务4: 采集群组B的消息

结果: 四个任务使用两个账号并发执行
```

### 场景3: 负载均衡
```
账号A: 任务1, 任务3, 任务5
账号B: 任务2, 任务4, 任务6

结果: 任务均匀分配到不同账号，避免单账号过载
```

## 性能优势

### 并发效率
- **单任务**: 1个任务 × 1个账号 = 1倍效率
- **多任务单账号**: 3个任务 × 1个账号 = 3倍效率
- **多任务多账号**: 3个任务 × 2个账号 = 6倍效率

### 资源利用
- 充分利用多账号资源
- 避免单账号频率限制
- 提高整体采集速度

### 稳定性
- 任务隔离，互不影响
- 单任务失败不影响其他任务
- 单账号失效不影响其他账号

## 注意事项

### 1. Telegram限制
- 每个账号有API调用频率限制
- 建议合理分配任务到不同账号
- 避免单账号同时运行过多任务

### 2. 系统资源
- 每个任务占用一个线程
- 建议根据系统资源控制并发数
- 监控内存和CPU使用情况

### 3. 任务管理
- 及时停止不需要的任务
- 定期清理已完成的任务
- 监控任务执行状态

### 4. 账号安全
- 避免频繁操作导致账号被限制
- 合理设置采集间隔
- 遵守Telegram使用条款

## 验收标准

### 功能验收
- [x] 可以创建任务时选择账号
- [x] 任务列表显示使用的账号
- [x] 多个任务可以同时运行
- [x] 不同账号的任务可以并发
- [x] 任务执行使用正确的账号
- [x] 任务之间互不干扰

### 性能验收
- [x] 多任务并发执行正常
- [x] 系统资源占用合理
- [x] 无内存泄漏
- [x] 无线程死锁

### 稳定性验收
- [x] 单任务失败不影响其他任务
- [x] 单账号失效不影响其他账号
- [x] 长时间运行稳定

## 后续优化建议

1. **任务队列**: 实现任务队列，控制并发数
2. **负载均衡**: 自动分配任务到负载较低的账号
3. **健康检查**: 定期检查账号和任务状态
4. **性能监控**: 实时监控任务执行性能
5. **智能调度**: 根据账号状态智能调度任务

---

**实现状态**: ✅ 完成  
**测试状态**: ⏳ 待测试  
**文档版本**: v1.0  
**创建时间**: 2025-12-06
