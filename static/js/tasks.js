let currentPage = 1;
let currentTaskId = null;

// 页面加载时获取任务列表
$(document).ready(function() {
    loadTasks();
    
    // 搜索功能（可选）
    $('#taskSearch').on('input', function() {
        loadTasks();
    });
});

// 加载任务列表
function loadTasks(page = 1) {
    currentPage = page;
    
    $.get('/api/tasks', { page: page }, function(response) {
        if (response.code === 200) {
            renderTasks(response.data.tasks);
            renderPagination(response.data);
        } else {
            showToast('加载任务失败', 'error');
        }
    }).fail(function() {
        showToast('网络错误', 'error');
    });
}

// 渲染任务列表
function renderTasks(tasks) {
    const tbody = $('#taskList');
    tbody.empty();
    
    if (tasks.length === 0) {
        tbody.append('<tr><td colspan="7" class="text-center">暂无任务</td></tr>');
        return;
    }
    
    tasks.forEach(task => {
        const statusBadge = getStatusBadge(task.status);
        const actionButtons = getActionButtons(task);
        const accountPhone = task.account_phone || '未知';
        
        const row = `
            <tr>
                <td>${task.id}</td>
                <td>${task.name}</td>
                <td><span class="badge bg-info">${accountPhone}</span></td>
                <td>${task.bot_username}</td>
                <td>${statusBadge}</td>
                <td>${formatDate(task.created_at)}</td>
                <td>${actionButtons}</td>
            </tr>
        `;
        tbody.append(row);
    });
}

// 获取状态徽章
function getStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge bg-secondary">待执行</span>',
        'running': '<span class="badge bg-primary">运行中</span>',
        'stopped': '<span class="badge bg-warning">已停止</span>',
        'completed': '<span class="badge bg-success">已完成</span>',
        'failed': '<span class="badge bg-danger">失败</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">未知</span>';
}

// 获取操作按钮
function getActionButtons(task) {
    let buttons = '';
    
    if (task.status === 'running') {
        buttons += `<button class="btn btn-sm btn-warning" onclick="stopTask(${task.id})">
            <i class="bi bi-stop-circle"></i> 停止
        </button> `;
    } else {
        buttons += `<button class="btn btn-sm btn-success" onclick="startTask(${task.id})">
            <i class="bi bi-play-circle"></i> 启动
        </button> `;
    }
    
    buttons += `<button class="btn btn-sm btn-info" onclick="viewTask(${task.id})">
        <i class="bi bi-eye"></i> 查看
    </button> `;
    
    if (task.status !== 'running') {
        buttons += `<button class="btn btn-sm btn-primary" onclick="editTask(${task.id})">
            <i class="bi bi-pencil"></i> 编辑
        </button> `;
        buttons += `<button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">
            <i class="bi bi-trash"></i> 删除
        </button>`;
    }
    
    return buttons;
}

// 渲染分页
function renderPagination(data) {
    const pagination = $('#pagination');
    pagination.empty();
    
    if (data.total_pages <= 1) return;
    
    // 上一页
    if (data.page > 1) {
        pagination.append(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadTasks(${data.page - 1}); return false;">上一页</a>
            </li>
        `);
    }
    
    // 页码
    for (let i = 1; i <= data.total_pages; i++) {
        const active = i === data.page ? 'active' : '';
        pagination.append(`
            <li class="page-item ${active}">
                <a class="page-link" href="#" onclick="loadTasks(${i}); return false;">${i}</a>
            </li>
        `);
    }
    
    // 下一页
    if (data.page < data.total_pages) {
        pagination.append(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadTasks(${data.page + 1}); return false;">下一页</a>
            </li>
        `);
    }
}

// 加载可用账号列表
function loadAvailableAccounts() {
    $.get('/api/tasks/available-accounts', function(response) {
        if (response.code === 200) {
            const select = $('#accountId');
            select.empty();
            
            if (response.data.length === 0) {
                select.append('<option value="">没有可用账号，请先添加并登录账号</option>');
                return;
            }
            
            response.data.forEach(account => {
                const activeLabel = account.is_active ? ' (活跃)' : '';
                const option = `<option value="${account.id}">${account.phone}${activeLabel}</option>`;
                select.append(option);
                
                // 默认选中活跃账号
                if (account.is_active) {
                    select.val(account.id);
                }
            });
        } else {
            showToast('加载账号列表失败', 'error');
        }
    }).fail(function() {
        showToast('加载账号列表失败', 'error');
    });
}

// 打开创建模态框
function openCreateModal() {
    currentTaskId = null;
    $('#taskModalTitle').text('创建任务');
    $('#taskForm')[0].reset();
    $('#taskId').val('');
    
    // 加载可用账号
    loadAvailableAccounts();
}

// 任务类型和采集模式变化处理
$(document).ready(function() {
    // 任务类型切换
    $('#taskType').on('change', function() {
        const type = $(this).val();
        if (type === 'bot_search') {
            // 机器人搜索：只搜索群组，不采集消息
            $('#botSearchConfig').show();
            $('#directCollectConfig').hide();
            $('#paginationConfig').show();
            $('#collectConfig').hide();  // 隐藏采集配置
            $('#groupRegexGroup').show();  // 显示群组过滤
            $('#messageRegexGroup').hide();  // 隐藏消息过滤
            $('#botUsername').prop('required', true);
            $('#targetGroups').prop('required', false);
        } else {
            // 直接采集：采集指定群组的消息
            $('#botSearchConfig').hide();
            $('#directCollectConfig').show();
            $('#paginationConfig').hide();
            $('#collectConfig').show();  // 显示采集配置
            $('#groupRegexGroup').hide();  // 隐藏群组过滤
            $('#messageRegexGroup').show();  // 显示消息过滤
            $('#botUsername').prop('required', false);
            $('#targetGroups').prop('required', true);
        }
    });
    
    // 采集模式变化时显示/隐藏历史消息数量
    $('#collectMode').on('change', function() {
        const mode = $(this).val();
        if (mode === 'realtime_only') {
            $('#historyLimitGroup').hide();
        } else {
            $('#historyLimitGroup').show();
        }
    });
});

// 保存任务
function saveTask() {
    const taskType = $('#taskType').val();
    const accountId = $('#accountId').val();
    
    if (!accountId) {
        showToast('请选择账号', 'error');
        return;
    }
    
    const taskData = {
        name: $('#taskName').val(),
        account_id: parseInt(accountId),
        task_type: taskType,
        api_config: null
    };
    
    // 根据任务类型设置不同的配置
    if (taskType === 'bot_search') {
        // 机器人搜索：只搜索群组，不采集消息
        taskData.bot_username = $('#botUsername').val();
        taskData.search_keywords = $('#searchKeywords').val().split('\n').filter(k => k.trim());
        taskData.target_groups = null;
        taskData.group_regex = $('#groupRegex').val() || null;
        taskData.message_regex = null;  // 不采集消息，不需要消息过滤
        taskData.collect_mode = null;   // 不采集消息
        taskData.history_limit = null;  // 不采集消息
        taskData.pagination_config = {
            next_button_text: $('#nextButtonText').val() || null,
            max_pages: parseInt($('#maxPages').val()) || 10
        };
    } else {
        // 直接采集：采集指定群组的消息
        taskData.bot_username = null;
        taskData.target_groups = $('#targetGroups').val().split('\n').filter(g => g.trim());
        taskData.group_regex = null;  // 已经指定了群组，不需要过滤
        taskData.message_regex = $('#messageRegex').val() || null;
        taskData.collect_mode = $('#collectMode').val() || 'both';
        taskData.history_limit = parseInt($('#historyLimit').val()) || 1000;
        taskData.pagination_config = null;
    }
    
    // 解析API配置
    const apiUrl = $('#apiUrl').val();
    if (apiUrl) {
        taskData.api_config = {
            url: apiUrl,
            method: $('#apiMethod').val(),
            param_mapping: {}
        };
        
        // 解析参数映射
        const paramMapping = $('#apiParamMapping').val();
        if (paramMapping) {
            try {
                taskData.api_config.param_mapping = JSON.parse(paramMapping);
            } catch (e) {
                showToast('参数映射JSON格式错误', 'error');
                return;
            }
        }
    }
    
    // 验证必填字段
    if (!taskData.name || !taskData.bot_username) {
        showToast('请填写必填字段', 'error');
        return;
    }
    
    // 发送请求
    const url = currentTaskId ? `/api/tasks/${currentTaskId}` : '/api/tasks';
    const method = currentTaskId ? 'PUT' : 'POST';
    
    $.ajax({
        url: url,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(taskData),
        success: function(response) {
            if (response.code === 200) {
                showToast(currentTaskId ? '任务更新成功' : '任务创建成功', 'success');
                $('#taskModal').modal('hide');
                loadTasks(currentPage);
            } else {
                showToast(response.message, 'error');
            }
        },
        error: function() {
            showToast('操作失败', 'error');
        }
    });
}

// 启动任务
function startTask(taskId) {
    if (!confirm('确定要启动此任务吗？')) return;
    
    $.post(`/api/tasks/${taskId}/start`, function(response) {
        if (response.code === 200) {
            showToast('任务已启动', 'success');
            loadTasks(currentPage);
        } else {
            showToast(response.message, 'error');
        }
    }).fail(function() {
        showToast('操作失败', 'error');
    });
}

// 停止任务
function stopTask(taskId) {
    if (!confirm('确定要停止此任务吗？')) return;
    
    $.post(`/api/tasks/${taskId}/stop`, function(response) {
        if (response.code === 200) {
            showToast('任务已停止', 'success');
            loadTasks(currentPage);
        } else {
            showToast(response.message, 'error');
        }
    }).fail(function() {
        showToast('操作失败', 'error');
    });
}

// 查看任务详情
function viewTask(taskId) {
    $.get(`/api/tasks/${taskId}`, function(response) {
        if (response.code === 200) {
            const task = response.data;
            const content = `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>任务名称:</strong> ${task.name}</p>
                        <p><strong>机器人:</strong> ${task.bot_username}</p>
                        <p><strong>状态:</strong> ${getStatusBadge(task.status)}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>创建时间:</strong> ${formatDate(task.created_at)}</p>
                        <p><strong>更新时间:</strong> ${formatDate(task.updated_at)}</p>
                    </div>
                </div>
                <hr>
                <h6>采集配置</h6>
                <p><strong>采集模式:</strong> ${getCollectModeText(task.collect_mode)}</p>
                <p><strong>历史消息数量:</strong> ${task.history_limit || 1000}条</p>
                <hr>
                <h6>过滤配置</h6>
                <p><strong>群组正则:</strong> ${task.group_regex || '无'}</p>
                <p><strong>消息正则:</strong> ${task.message_regex || '无'}</p>
                <hr>
                <h6>翻页配置</h6>
                <pre>${JSON.stringify(task.pagination_config, null, 2)}</pre>
                <hr>
                <h6>API配置</h6>
                <pre>${JSON.stringify(task.api_config, null, 2)}</pre>
            `;
            $('#taskDetailContent').html(content);
            $('#taskDetailModal').modal('show');
        }
    });
}

// 编辑任务
function editTask(taskId) {
    $.get(`/api/tasks/${taskId}`, function(response) {
        if (response.code === 200) {
            const task = response.data;
            currentTaskId = taskId;
            
            $('#taskModalTitle').text('编辑任务');
            $('#taskId').val(task.id);
            $('#taskName').val(task.name);
            
            // 加载账号列表并设置当前账号
            loadAvailableAccounts();
            setTimeout(() => {
                $('#accountId').val(task.account_id);
            }, 500);
            
            // 设置任务类型
            $('#taskType').val(task.task_type || 'bot_search').trigger('change');
            
            // 根据任务类型设置不同的字段
            if (task.task_type === 'bot_search') {
                $('#botUsername').val(task.bot_username || '');
                $('#groupRegex').val(task.group_regex || '');
                
                // 处理搜索关键词（JSON数组转换为多行文本）
                if (task.search_keywords) {
                    try {
                        const keywords = typeof task.search_keywords === 'string' 
                            ? JSON.parse(task.search_keywords) 
                            : task.search_keywords;
                        $('#searchKeywords').val(Array.isArray(keywords) ? keywords.join('\n') : '');
                    } catch (e) {
                        $('#searchKeywords').val('');
                    }
                }
                
                // 翻页配置
                if (task.pagination_config) {
                    $('#nextButtonText').val(task.pagination_config.next_button_text || '');
                    $('#maxPages').val(task.pagination_config.max_pages || 10);
                }
            } else {
                // 直接采集模式
                $('#messageRegex').val(task.message_regex || '');
                $('#collectMode').val(task.collect_mode || 'both');
                $('#historyLimit').val(task.history_limit || 1000);
                
                // 处理目标群组（JSON数组转换为多行文本）
                if (task.target_groups) {
                    try {
                        const groups = typeof task.target_groups === 'string' 
                            ? JSON.parse(task.target_groups) 
                            : task.target_groups;
                        $('#targetGroups').val(Array.isArray(groups) ? groups.join('\n') : '');
                    } catch (e) {
                        $('#targetGroups').val('');
                    }
                }
                
                // 根据模式显示/隐藏历史消息数量
                if (task.collect_mode === 'realtime_only') {
                    $('#historyLimitGroup').hide();
                } else {
                    $('#historyLimitGroup').show();
                }
            }
            
            // API配置
            if (task.api_config) {
                $('#apiUrl').val(task.api_config.url || '');
                $('#apiMethod').val(task.api_config.method || 'POST');
                $('#apiParamMapping').val(JSON.stringify(task.api_config.param_mapping || {}, null, 2));
            } else {
                $('#apiUrl').val('');
                $('#apiMethod').val('POST');
                $('#apiParamMapping').val('');
            }
            
            $('#taskModal').modal('show');
        }
    }).fail(function() {
        showToast('加载任务失败', 'error');
    });
}

// 删除任务
function deleteTask(taskId) {
    if (!confirm('确定要删除此任务吗？此操作不可恢复！')) return;
    
    $.ajax({
        url: `/api/tasks/${taskId}`,
        method: 'DELETE',
        success: function(response) {
            if (response.code === 200) {
                showToast('任务已删除', 'success');
                loadTasks(currentPage);
            } else {
                showToast(response.message, 'error');
            }
        },
        error: function() {
            showToast('删除失败', 'error');
        }
    });
}

// 获取采集模式文本
function getCollectModeText(mode) {
    const modes = {
        'both': '采集历史 + 实时监听',
        'history_only': '仅采集历史消息',
        'realtime_only': '仅实时监听'
    };
    return modes[mode] || '采集历史 + 实时监听';
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}


// 正则表达式示例库数据
const regexExamples = {
    group: [
        {
            category: '推荐搜索机器人',
            bot: '@soso, @hao1234bot, @zh_secretary_bot, @kuaisou03bot, @sou07_bot',
            examples: [
                { name: '匹配链接和标题（通用格式）', regex: '(https?://t\\.me/[a-zA-Z0-9_]+)\\s*[\\-|:：]?\\s*(.+)', desc: '同时提取链接和标题，格式：链接 - 标题 或 链接：标题' },
                { name: '匹配标题和链接（标题在前）', regex: '(.+?)\\s*[\\-|:：]?\\s*(https?://t\\.me/[a-zA-Z0-9_]+)', desc: '同时提取标题和链接，格式：标题 - 链接 或 标题：链接' },
                { name: '匹配@用户名和标题', regex: '(@[a-zA-Z0-9_]+)\\s*[\\-|:：]?\\s*(.+)', desc: '同时提取@用户名和标题' },
                { name: '匹配带括号的格式', regex: '(.+?)\\s*[【\\[\\(]\\s*(https?://t\\.me/[a-zA-Z0-9_]+|@[a-zA-Z0-9_]+)\\s*[】\\]\\)]', desc: '提取：标题【链接】或 标题[链接] 格式' },
                { name: '匹配joinchat链接和标题', regex: '(https?://t\\.me/(?:joinchat|\\+)[a-zA-Z0-9_-]+)\\s*[\\-|:：]?\\s*(.+)', desc: '同时提取私有群组链接和标题' },
                { name: '过滤包含关键词的标题', regex: '(https?://t\\.me/[a-zA-Z0-9_]+)\\s*[\\-|:：]?\\s*(.*(crypto|bitcoin|区块链).*)', desc: '只匹配标题包含crypto/bitcoin/区块链的群组' },
                { name: '过滤中文标题', regex: '(https?://t\\.me/[a-zA-Z0-9_]+)\\s*[\\-|:：]?\\s*(.*[\u4e00-\u9fa5]+.*)', desc: '只匹配包含中文标题的群组' },
                { name: '排除测试群', regex: '(https?://t\\.me/[a-zA-Z0-9_]+)\\s*[\\-|:：]?\\s*(?!.*(test|测试))(.+)', desc: '排除标题包含test或测试的群组' }
            ]
        }
    ],
    message: [
        {
            category: '价格/交易信息',
            bot: '通用',
            examples: [
                { name: '包含价格', regex: '.*(价格|price|\\$\\d+|¥\\d+|€\\d+).*', desc: '匹配包含价格信息的消息' },
                { name: '涨跌信息', regex: '.*(涨|跌|上涨|下跌|\\+\\d+%|\\-\\d+%).*', desc: '匹配涨跌信息' },
                { name: '交易信号', regex: '.*(买入|卖出|做多|做空|开仓|平仓).*', desc: '匹配交易信号' },
                { name: '数字范围', regex: '.*\\d{1,5}\\.\\d{2}.*', desc: '匹配包含小数的数字（如价格）' }
            ]
        },
        {
            category: '链接/资源',
            bot: '通用',
            examples: [
                { name: '包含链接', regex: '.*https?://.*', desc: '匹配包含HTTP链接的消息' },
                { name: 'Telegram链接', regex: '.*t\\.me/.*', desc: '匹配包含Telegram链接' },
                { name: '包含邮箱', regex: '.*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}.*', desc: '匹配包含邮箱地址' },
                { name: '包含手机号', regex: '.*1[3-9]\\d{9}.*', desc: '匹配包含中国手机号' }
            ]
        },
        {
            category: '关键词匹配',
            bot: '通用',
            examples: [
                { name: '加密货币', regex: '.*(bitcoin|btc|ethereum|eth|crypto|币).*', desc: '匹配加密货币相关' },
                { name: '技术开发', regex: '.*(代码|code|开发|develop|API|SDK).*', desc: '匹配技术开发相关' },
                { name: '营销推广', regex: '.*(推广|营销|引流|获客|转化).*', desc: '匹配营销相关' },
                { name: 'AI相关', regex: '.*(AI|人工智能|ChatGPT|GPT|机器学习).*', desc: '匹配AI相关内容' }
            ]
        },
        {
            category: '时间/日期',
            bot: '通用',
            examples: [
                { name: '包含日期', regex: '.*\\d{4}-\\d{2}-\\d{2}.*', desc: '匹配包含日期格式（YYYY-MM-DD）' },
                { name: '包含时间', regex: '.*\\d{1,2}:\\d{2}.*', desc: '匹配包含时间格式（HH:MM）' },
                { name: '今天/明天', regex: '.*(今天|明天|昨天|today|tomorrow).*', desc: '匹配时间相关词' },
                { name: '最近发布', regex: '.*(刚刚|刚才|最新|new|latest).*', desc: '匹配最新消息' }
            ]
        },
        {
            category: '内容类型',
            bot: '通用',
            examples: [
                { name: '问题/提问', regex: '.*(\\?|？|如何|怎么|为什么|how|why|what).*', desc: '匹配提问类消息' },
                { name: '通知/公告', regex: '.*(通知|公告|提醒|notice|announcement).*', desc: '匹配通知公告' },
                { name: '教程/指南', regex: '.*(教程|指南|攻略|tutorial|guide|how to).*', desc: '匹配教程类内容' },
                { name: '新闻/资讯', regex: '.*(新闻|资讯|消息|news|breaking).*', desc: '匹配新闻资讯' }
            ]
        },
        {
            category: '排除/过滤',
            bot: '通用',
            examples: [
                { name: '排除广告', regex: '^(?!.*(广告|AD|推广|spam)).*', desc: '排除广告消息' },
                { name: '排除短消息', regex: '.{10,}', desc: '只匹配10个字符以上的消息' },
                { name: '排除表情', regex: '^(?!.*[😀-🙏]).*', desc: '排除只有表情的消息' },
                { name: '只要中文', regex: '.*[\u4e00-\u9fa5]+.*', desc: '只匹配包含中文的消息' }
            ]
        }
    ]
};

// 显示正则表达式示例
function showRegexExamples(type) {
    const examples = regexExamples[type];
    const targetInput = type === 'group' ? '#groupRegex' : '#messageRegex';
    const title = type === 'group' ? '群组名称' : '消息内容';
    
    let html = `<h5 class="mb-3">${title}正则表达式示例</h5>`;
    
    examples.forEach(category => {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-light">
                    <h6 class="mb-0">
                        <i class="bi bi-folder"></i> ${category.category}
                        <span class="badge bg-secondary ms-2">推荐机器人: ${category.bot}</span>
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row">
        `;
        
        category.examples.forEach(example => {
            html += `
                <div class="col-md-6 mb-3">
                    <div class="border rounded p-3 h-100 regex-example" style="cursor: pointer;" 
                         onclick="applyRegex('${targetInput}', '${example.regex.replace(/'/g, "\\'")}')">
                        <h6 class="text-primary">
                            <i class="bi bi-code-square"></i> ${example.name}
                        </h6>
                        <code class="d-block mb-2 text-break">${example.regex}</code>
                        <small class="text-muted">${example.desc}</small>
                    </div>
                </div>
            `;
        });
        
        html += `
                    </div>
                </div>
            </div>
        `;
    });
    
    $('#regexExamplesContent').html(html);
    $('#regexExamplesModal').modal('show');
}

// 应用正则表达式到输入框
function applyRegex(targetInput, regex) {
    $(targetInput).val(regex);
    $('#regexExamplesModal').modal('hide');
    showToast('正则表达式已应用', 'success');
}
