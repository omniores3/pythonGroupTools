let batchResults = [];

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
    
    // 显示进度
    $('#progressCard').show();
    $('#resultCard').hide();
    $('#progressBar').css('width', '0%').text('0%');
    $('#progressText').text('正在提交...');
    
    // 禁用表单
    $('#batchForm button[type="submit"]').prop('disabled', true);
    
    // 发送请求
    $.ajax({
        url: '/api/batch/submit',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            api_url: apiUrl,
            method: method,
            param_name: paramName,
            content: content
        }),
        success: function(response) {
            if (response.code === 200) {
                // 更新进度
                $('#progressBar').css('width', '100%').text('100%');
                $('#progressText').text('提交完成！');
                
                // 显示结果
                setTimeout(function() {
                    displayResults(response.data);
                    showToast(response.message, 'success');
                }, 500);
            } else {
                showToast(response.message || '提交失败', 'error');
            }
        },
        error: function(xhr) {
            const response = xhr.responseJSON;
            showToast(response?.message || '提交失败', 'error');
            $('#progressCard').hide();
        },
        complete: function() {
            // 启用表单
            $('#batchForm button[type="submit"]').prop('disabled', false);
        }
    });
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
    
    data.results.forEach(result => {
        const statusBadge = result.success 
            ? '<span class="badge bg-success">成功</span>'
            : '<span class="badge bg-danger">失败</span>';
        
        const statusCode = result.status_code || '-';
        const error = result.error || '-';
        
        const row = `
            <tr class="${result.success ? '' : 'table-danger'}">
                <td>${result.index}</td>
                <td class="text-truncate" style="max-width: 300px;" title="${result.data}">
                    ${result.data}
                </td>
                <td>${statusBadge}</td>
                <td>${statusCode}</td>
                <td class="text-truncate" style="max-width: 200px;" title="${error}">
                    ${error}
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
    let csv = '序号,数据,状态,HTTP状态码,错误信息\n';
    
    batchResults.forEach(result => {
        const status = result.success ? '成功' : '失败';
        const statusCode = result.status_code || '';
        const error = (result.error || '').replace(/"/g, '""'); // 转义引号
        
        csv += `${result.index},"${result.data}","${status}","${statusCode}","${error}"\n`;
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
