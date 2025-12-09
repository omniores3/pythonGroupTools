let batchResults = [];
let eventSource = null;
let totalCount = 0;
let processedCount = 0;

$(document).ready(function() {
    // 实时统计行数
    $('#content').on('input', function() {
        const lines = $(this).val().split('\n').filter(line => line.trim()).length;
        $('#lineCount').text(lines);
    });
    
    // 表单提交
    $('#batchForm').submit(function(e) {
        e.preventDefault();
        submitBatch();
    });
});

// 提交批量数据
function submitBatch() {
    const apiUrl = $('#apiUrl').val();
    const method = $('#method').val();
    const paramName = $('#paramName').val();
    const content = $('#content').val();
    
    // 验证
    if (!apiUrl || !content) {
        showToast('请填写完整信息', 'warning');
        return;
    }
    
    // 统计行数
    const lines = content.split('\n').filter(line => line.trim());
    if (lines.length === 0) {
        showToast('没有有效的数据行', 'warning');
        return;
    }
    
    // 确认提交
    if (!confirm(`确定要提交 ${lines.length} 条数据吗？`)) {
        return;
    }
    
    // 重置状态
    batchResults = [];
    processedCount = 0;
    
    // 显示进度卡片
    $('#progressCard').show();
    $('#resultCard').hide();
    $('#progressBar').css('width', '0%').text('0%');
    $('#progressText').text('准备提交...');
    $('#logContent').empty();
    $('#stopBtn').show();
    
    // 禁用表单
    $('#batchForm button[type="submit"]').prop('disabled', true);
    
    // 构建请求参数
    const params = new URLSearchParams({
        api_url: apiUrl,
        method: method,
        param_name: paramName,
        content: content
    });
    
    // 使用EventSource接收SSE
    eventSource = new EventSource('/api/batch/submit?' + params.toString());
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleSSEMessage(data);
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        eventSource = null;
        $('#stopBtn').hide();
        $('#batchForm button[type="submit"]').prop('disabled', false);
        showToast('连接中断，请重试', 'error');
    };
}

// 处理SSE消息
function handleSSEMessage(data) {
    switch(data.type) {
        case 'start':
            totalCount = data.total;
            addLog(`开始提交 ${totalCount} 条数据...`, 'info');
            break;
            
        case 'processing':
            addLog(`[${data.index}/${totalCount}] 正在处理: ${data.data}`, 'processing');
            break;
            
        case 'result':
            processedCount++;
            batchResults.push(data);
            
            // 更新进度
            const progress = Math.round((processedCount / totalCount) * 100);
            $('#progressBar').css('width', progress + '%').text(progress + '%');
            $('#progressText').text(`已处理 ${processedCount}/${totalCount} 条`);
            
            // 添加日志
            if (data.success) {
                addLog(`[${data.index}] ✓ 成功 (${data.elapsed_time}s) - HTTP ${data.status_code}`, 'success');
                addLog(`请求数据: ${data.data}`, 'request');
                
                // 显示响应内容
                if (data.response_json) {
                    // JSON格式美化显示
                    addLog(`API响应:`, 'response-header');
                    addLogJSON(data.response_json, 'response');
                } else if (data.response) {
                    // 普通文本响应
                    addLog(`API响应: ${data.response}`, 'response');
                }
            } else {
                addLog(`[${data.index}] ✗ 失败 (${data.status_code || 'N/A'})`, 'error');
                addLog(`请求数据: ${data.data}`, 'request');
                
                // 显示错误响应
                if (data.response_json) {
                    addLog(`错误响应:`, 'error-header');
                    addLogJSON(data.response_json, 'error-response');
                } else if (data.response) {
                    addLog(`错误信息: ${data.response}`, 'error-response');
                }
            }
            addLog('', 'separator'); // 添加空行分隔
            break;
            
        case 'complete':
            // 关闭连接
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            
            // 更新UI
            $('#progressBar').css('width', '100%').text('100%');
            $('#progressText').text('提交完成！');
            $('#stopBtn').hide();
            $('#batchForm button[type="submit"]').prop('disabled', false);
            
            // 添加完成日志
            addLog(`\n提交完成！成功: ${data.success} 条，失败: ${data.fail} 条`, 'complete');
            
            // 显示结果
            setTimeout(function() {
                displayResults({
                    total: totalCount,
                    success: data.success,
                    fail: data.fail,
                    results: batchResults
                });
                showToast(`提交完成：成功 ${data.success} 条，失败 ${data.fail} 条`, 'success');
            }, 500);
            break;
    }
}

// 添加日志
function addLog(message, type = 'info') {
    if (type === 'separator') {
        $('#logContent').append('<div style="height: 8px;"></div>');
        return;
    }
    
    const timestamp = new Date().toLocaleTimeString();
    let colorClass = 'text-light';
    let icon = '';
    let showTimestamp = true;
    let indent = '';
    
    switch(type) {
        case 'info':
            colorClass = 'text-info';
            icon = 'ℹ';
            break;
        case 'processing':
            colorClass = 'text-warning';
            icon = '⟳';
            break;
        case 'success':
            colorClass = 'text-success fw-bold';
            icon = '✓';
            break;
        case 'error':
            colorClass = 'text-danger fw-bold';
            icon = '✗';
            break;
        case 'request':
            colorClass = 'text-info';
            icon = '📤';
            showTimestamp = false;
            indent = '  ';
            break;
        case 'response-header':
            colorClass = 'text-success';
            icon = '📥';
            showTimestamp = false;
            indent = '  ';
            break;
        case 'response':
            colorClass = 'text-success';
            icon = '';
            showTimestamp = false;
            indent = '    ';
            break;
        case 'error-header':
            colorClass = 'text-danger';
            icon = '📥';
            showTimestamp = false;
            indent = '  ';
            break;
        case 'error-response':
            colorClass = 'text-danger';
            icon = '';
            showTimestamp = false;
            indent = '    ';
            break;
        case 'complete':
            colorClass = 'text-success fw-bold';
            icon = '✓';
            break;
    }
    
    const timePrefix = showTimestamp ? `[${timestamp}] ` : '';
    const logLine = `<div class="${colorClass}">${indent}${timePrefix}${icon} ${escapeHtml(message)}</div>`;
    $('#logContent').append(logLine);
    
    // 自动滚动到底部
    const logContainer = $('#logContainer')[0];
    logContainer.scrollTop = logContainer.scrollHeight;
}

// 添加JSON格式的日志
function addLogJSON(jsonObj, type = 'response') {
    const jsonStr = JSON.stringify(jsonObj, null, 2);
    const lines = jsonStr.split('\n');
    
    lines.forEach(line => {
        addLog(line, type);
    });
}

// 清空日志
function clearLogs() {
    $('#logContent').empty();
}

// 停止提交
function stopSubmit() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
        addLog('用户手动停止提交', 'error');
        $('#stopBtn').hide();
        $('#batchForm button[type="submit"]').prop('disabled', false);
        showToast('已停止提交', 'warning');
    }
}

// 显示结果
function displayResults(data) {
    batchResults = data.results;
    
    // 更新统计
    $('#totalCount').text(data.total);
    $('#successCount').text(data.success);
    $('#failCount').text(data.fail);
    
    // 渲染结果列表
    const tbody = $('#resultList');
    tbody.empty();
    
    data.results.forEach((result, idx) => {
        const statusBadge = result.success 
            ? '<span class="badge bg-success">成功</span>'
            : '<span class="badge bg-danger">失败</span>';
        
        const statusCode = result.status_code || '-';
        
        // 格式化响应内容（显示简短版本）
        let responsePreview = result.response || '-';
        if (responsePreview.length > 50) {
            responsePreview = responsePreview.substring(0, 50) + '...';
        }
        
        // 转义HTML
        responsePreview = $('<div>').text(responsePreview).html();
        
        const row = `
            <tr class="${result.success ? '' : 'table-danger'}">
                <td>${result.index}</td>
                <td class="text-truncate" style="max-width: 250px;" title="${escapeHtml(result.data)}">
                    ${escapeHtml(result.data)}
                </td>
                <td>${statusBadge}</td>
                <td>${statusCode}</td>
                <td class="text-truncate" style="max-width: 300px;" title="${escapeHtml(result.response || '')}">
                    ${responsePreview}
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewResponse(${idx})">
                        <i class="bi bi-eye"></i> 查看
                    </button>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
    
    // 显示结果卡片
    $('#resultCard').show();
    
    // 滚动到结果
    $('html, body').animate({
        scrollTop: $('#resultCard').offset().top - 100
    }, 500);
}

// 查看响应详情
function viewResponse(index) {
    const result = batchResults[index];
    
    // 填充模态框内容
    $('#modalRequestData').text(result.data);
    $('#modalStatusCode').text(result.status_code || '无');
    
    // 格式化响应内容
    let responseText = result.response || '无响应';
    
    // 如果有JSON格式的响应，美化显示
    if (result.response_json) {
        try {
            responseText = JSON.stringify(result.response_json, null, 2);
        } catch (e) {
            // 使用原始响应
        }
    }
    
    $('#modalResponse').text(responseText);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('responseModal'));
    modal.show();
}

// 复制响应内容
function copyResponse() {
    const responseText = $('#modalResponse').text();
    
    // 创建临时文本框
    const textarea = document.createElement('textarea');
    textarea.value = responseText;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    
    // 选择并复制
    textarea.select();
    document.execCommand('copy');
    
    // 移除临时文本框
    document.body.removeChild(textarea);
    
    showToast('响应内容已复制', 'success');
}

// HTML转义函数
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// 清空表单
function clearForm() {
    if (confirm('确定要清空所有内容吗？')) {
        $('#batchForm')[0].reset();
        $('#lineCount').text('0');
        $('#progressCard').hide();
        $('#resultCard').hide();
        batchResults = [];
    }
}

// 导出结果
function exportResults() {
    if (batchResults.length === 0) {
        showToast('没有可导出的结果', 'warning');
        return;
    }
    
    // 生成CSV内容
    let csv = '序号,数据,状态,HTTP状态码,接口响应\n';
    
    batchResults.forEach(result => {
        const status = result.success ? '成功' : '失败';
        const statusCode = result.status_code || '';
        const response = (result.response || '').replace(/"/g, '""').replace(/\n/g, ' '); // 转义引号和换行
        
        csv += `${result.index},"${result.data}","${status}","${statusCode}","${response}"\n`;
    });
    
    // 创建下载链接
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `batch_results_${Date.now()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('结果已导出', 'success');
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}
