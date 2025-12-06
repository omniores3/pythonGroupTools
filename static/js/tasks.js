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
            $('#botUsername').val(task.bot_username);
            $('#groupRegex').val(task.group_regex || '');
            $('#messageRegex').val(task.message_regex || '');
            
            // 采集配置
            $('#collectMode').val(task.collect_mode || 'both');
            $('#historyLimit').val(task.history_limit || 1000);
            
            // 根据模式显示/隐藏历史消息数量
            if (task.collect_mode === 'realtime_only') {
                $('#historyLimitGroup').hide();
            } else {
                $('#historyLimitGroup').show();
            }
            
            // 翻页配置
            $('#nextButtonText').val(task.pagination_config?.next_button_text || '');
            $('#maxPages').val(task.pagination_config?.max_pages || 10);
            
            // API配置
            if (task.api_config) {
                $('#apiUrl').val(task.api_config.url || '');
                $('#apiMethod').val(task.api_config.method || 'POST');
                $('#apiParamMapping').val(JSON.stringify(task.api_config.param_mapping || {}, null, 2));
            }
            
            $('#taskModal').modal('show');
        }
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
