let groupPage = 1;
let messagePage = 1;
let charts = {};

// 页面加载
$(document).ready(function() {
    loadStatistics();
    loadGroups();
    
    // Tab切换事件
    $('a[data-bs-toggle="tab"]').on('shown.bs.event', function(e) {
        const target = $(e.target).attr('href');
        if (target === '#messagesTab') {
            loadMessages();
        } else if (target === '#statisticsTab') {
            renderCharts();
        }
    });
    
    // 搜索事件
    $('#groupSearch').on('input', debounce(function() {
        loadGroups();
    }, 500));
    
    $('#messageSearch').on('input', debounce(function() {
        loadMessages();
    }, 500));
    
    // 日期过滤
    $('#startDate, #endDate').on('change', function() {
        loadMessages();
    });
});

// 加载统计数据
function loadStatistics() {
    $.get('/api/data/statistics', function(response) {
        if (response.code === 200) {
            updateStatCards(response.data);
            window.statsData = response.data;
        }
    });
}

// 更新统计卡片
function updateStatCards(data) {
    // 计算总数
    let totalGroups = 0;
    let totalMessages = 0;
    let todayMessages = 0;
    
    if (data.group_distribution) {
        totalGroups = data.group_distribution.length;
        totalMessages = data.group_distribution.reduce((sum, item) => sum + item.message_count, 0);
    }
    
    if (data.daily_stats && data.daily_stats.length > 0) {
        todayMessages = data.daily_stats[data.daily_stats.length - 1].count;
    }
    
    $('#totalGroups').text(totalGroups);
    $('#totalMessages').text(totalMessages);
    $('#todayMessages').text(todayMessages);
    $('#runningTasks').text('0'); // 需要从任务API获取
}

// 加载群组列表
function loadGroups(page = 1) {
    groupPage = page;
    const keyword = $('#groupSearch').val();
    
    const params = { page: page };
    if (keyword) params.keyword = keyword;
    
    $.get('/api/data/groups', params, function(response) {
        if (response.code === 200) {
            renderGroups(response.data.data);
            renderGroupPagination(response.data);
        }
    });
}

// 渲染群组列表
function renderGroups(groups) {
    const tbody = $('#groupList');
    tbody.empty();
    
    if (groups.length === 0) {
        tbody.append('<tr><td colspan="6" class="text-center">暂无数据</td></tr>');
        return;
    }
    
    groups.forEach(group => {
        const row = `
            <tr>
                <td>${group.id}</td>
                <td>${group.title}</td>
                <td>${group.username || '-'}</td>
                <td>${group.member_count || 0}</td>
                <td>${formatDate(group.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="viewGroupMessages(${group.id})">
                        <i class="bi bi-chat-dots"></i> 查看消息
                    </button>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

// 渲染群组分页
function renderGroupPagination(data) {
    const pagination = $('#groupPagination');
    pagination.empty();
    
    if (data.total_pages <= 1) return;
    
    if (data.page > 1) {
        pagination.append(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadGroups(${data.page - 1}); return false;">上一页</a>
            </li>
        `);
    }
    
    for (let i = 1; i <= Math.min(data.total_pages, 10); i++) {
        const active = i === data.page ? 'active' : '';
        pagination.append(`
            <li class="page-item ${active}">
                <a class="page-link" href="#" onclick="loadGroups(${i}); return false;">${i}</a>
            </li>
        `);
    }
    
    if (data.page < data.total_pages) {
        pagination.append(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadGroups(${data.page + 1}); return false;">下一页</a>
            </li>
        `);
    }
}

// 加载消息列表
function loadMessages(page = 1) {
    messagePage = page;
    const keyword = $('#messageSearch').val();
    const startDate = $('#startDate').val();
    const endDate = $('#endDate').val();
    
    const params = { page: page };
    if (keyword) params.keyword = keyword;
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    
    $.get('/api/data/messages', params, function(response) {
        if (response.code === 200) {
            renderMessages(response.data.data);
            renderMessagePagination(response.data);
        }
    });
}

// 渲染消息列表
function renderMessages(messages) {
    const tbody = $('#messageList');
    tbody.empty();
    
    if (messages.length === 0) {
        tbody.append('<tr><td colspan="6" class="text-center">暂无数据</td></tr>');
        return;
    }
    
    messages.forEach(msg => {
        const content = msg.content ? truncate(msg.content, 50) : '-';
        const mediaType = getMediaTypeBadge(msg.media_type);
        
        const row = `
            <tr>
                <td>${msg.id}</td>
                <td>${msg.group_title || '-'}</td>
                <td>${msg.sender_name || '-'}</td>
                <td>${content}</td>
                <td>${mediaType}</td>
                <td>${formatDate(msg.message_date)}</td>
            </tr>
        `;
        tbody.append(row);
    });
}

// 渲染消息分页
function renderMessagePagination(data) {
    const pagination = $('#messagePagination');
    pagination.empty();
    
    if (data.total_pages <= 1) return;
    
    if (data.page > 1) {
        pagination.append(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadMessages(${data.page - 1}); return false;">上一页</a>
            </li>
        `);
    }
    
    for (let i = 1; i <= Math.min(data.total_pages, 10); i++) {
        const active = i === data.page ? 'active' : '';
        pagination.append(`
            <li class="page-item ${active}">
                <a class="page-link" href="#" onclick="loadMessages(${i}); return false;">${i}</a>
            </li>
        `);
    }
    
    if (data.page < data.total_pages) {
        pagination.append(`
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadMessages(${data.page + 1}); return false;">下一页</a>
            </li>
        `);
    }
}

// 查看群组消息
function viewGroupMessages(groupId) {
    // 切换到消息Tab
    $('a[href="#messagesTab"]').tab('show');
    
    // 加载该群组的消息
    $.get('/api/data/messages', { group_id: groupId }, function(response) {
        if (response.code === 200) {
            renderMessages(response.data.data);
            renderMessagePagination(response.data);
        }
    });
}

// 渲染图表
function renderCharts() {
    if (!window.statsData) return;
    
    // 销毁旧图表
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    
    // 每日趋势图
    const dailyCtx = document.getElementById('dailyChart');
    if (dailyCtx && window.statsData.daily_stats) {
        charts.daily = new Chart(dailyCtx, {
            type: 'line',
            data: {
                labels: window.statsData.daily_stats.map(d => d.date),
                datasets: [{
                    label: '消息数量',
                    data: window.statsData.daily_stats.map(d => d.count),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        });
    }
    
    // 群组分布图
    const groupCtx = document.getElementById('groupChart');
    if (groupCtx && window.statsData.group_distribution) {
        charts.group = new Chart(groupCtx, {
            type: 'bar',
            data: {
                labels: window.statsData.group_distribution.map(g => truncate(g.title, 20)),
                datasets: [{
                    label: '消息数量',
                    data: window.statsData.group_distribution.map(g => g.message_count),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // 消息类型图
    const typeCtx = document.getElementById('typeChart');
    if (typeCtx && window.statsData.message_type_stats) {
        charts.type = new Chart(typeCtx, {
            type: 'doughnut',
            data: {
                labels: window.statsData.message_type_stats.map(t => t.media_type),
                datasets: [{
                    data: window.statsData.message_type_stats.map(t => t.count),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(153, 102, 255, 0.5)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// 导出数据
function exportData(type, format) {
    const keyword = type === 'groups' ? $('#groupSearch').val() : $('#messageSearch').val();
    
    let url = `/api/data/export?type=${type}&format=${format}`;
    if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
    
    if (type === 'messages') {
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
    }
    
    window.location.href = url;
    showToast('导出中...', 'info');
}

// 工具函数
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

function getMediaTypeBadge(type) {
    const badges = {
        'text': '<span class="badge bg-secondary">文本</span>',
        'photo': '<span class="badge bg-info">图片</span>',
        'video': '<span class="badge bg-primary">视频</span>',
        'document': '<span class="badge bg-warning">文档</span>',
        'audio': '<span class="badge bg-success">音频</span>'
    };
    return badges[type] || '<span class="badge bg-secondary">其他</span>';
}

function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}
