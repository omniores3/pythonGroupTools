$(document).ready(function() {
    let currentAccountId = null;
    let currentPhone = null;
    
    // 加载账号列表
    function loadAccounts() {
        $.get('/api/auth/accounts', function(response) {
            if (response.code === 200) {
                renderAccounts(response.data);
            } else {
                showToast('加载账号列表失败', 'error');
            }
        }).fail(function() {
            showToast('加载账号列表失败', 'error');
        });
    }
    
    // 渲染账号列表
    function renderAccounts(accounts) {
        const tbody = $('#accountList');
        tbody.empty();
        
        if (accounts.length === 0) {
            tbody.html(`
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="bi bi-inbox"></i> 暂无账号，请添加
                    </td>
                </tr>
            `);
            return;
        }
        
        accounts.forEach(function(account) {
            const loginStatus = account.is_logged_in 
                ? '<span class="badge bg-success"><i class="bi bi-check-circle"></i> 已登录</span>'
                : '<span class="badge bg-secondary"><i class="bi bi-x-circle"></i> 未登录</span>';
            
            const activeStatus = account.is_active 
                ? '<span class="badge bg-primary"><i class="bi bi-star-fill"></i> 活跃</span>'
                : '<span class="badge bg-light text-dark">非活跃</span>';
            
            const activateBtn = account.is_logged_in && !account.is_active
                ? `<button class="btn btn-sm btn-outline-primary activate-btn" data-id="${account.id}">
                       <i class="bi bi-star"></i> 设为活跃
                   </button>`
                : '';
            
            const createdAt = new Date(account.created_at).toLocaleString('zh-CN');
            
            tbody.append(`
                <tr>
                    <td>${account.phone}</td>
                    <td>${account.api_id}</td>
                    <td>${loginStatus}</td>
                    <td>${activeStatus}</td>
                    <td>${createdAt}</td>
                    <td>
                        ${activateBtn}
                        <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${account.id}">
                            <i class="bi bi-trash"></i> 删除
                        </button>
                    </td>
                </tr>
            `);
        });
    }
    
    // 登录表单提交
    $('#loginForm').submit(function(e) {
        e.preventDefault();
        
        const phone = $('#phone').val();
        
        if (!phone) {
            showToast('请输入手机号', 'warning');
            return;
        }
        
        // 保存手机号供后续使用
        currentPhone = phone;
        
        // 禁用提交按钮
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> 发送中...');
        
        $.ajax({
            url: '/api/auth/accounts',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                phone: phone
            }),
            success: function(response) {
                if (response.code === 200) {
                    currentAccountId = response.data.account_id;
                    
                    if (response.data.status === 'code_sent') {
                        // 显示验证码表单
                        $('#loginForm').hide();
                        $('#verifyForm').show();
                        showToast('验证码已发送', 'success');
                    } else if (response.data.status === 'success') {
                        // 直接登录成功
                        showToast('登录成功', 'success');
                        $('#addAccountModal').modal('hide');
                        loadAccounts();
                        resetForms();
                    }
                } else {
                    showToast(response.message || '登录失败', 'error');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showToast(response?.message || '登录失败', 'error');
            },
            complete: function() {
                submitBtn.prop('disabled', false).html('<i class="bi bi-box-arrow-in-right"></i> 发送验证码');
            }
        });
    });
    
    // 验证码表单提交
    $('#verifyForm').submit(function(e) {
        e.preventDefault();
        
        const code = $('#code').val();
        
        if (!code) {
            showToast('请输入验证码', 'warning');
            return;
        }
        
        if (!currentAccountId || !currentPhone) {
            showToast('会话已过期，请重新添加账号', 'error');
            $('#addAccountModal').modal('hide');
            resetForms();
            return;
        }
        
        // 禁用提交按钮
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> 验证中...');
        
        $.ajax({
            url: `/api/auth/accounts/${currentAccountId}/verify`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                phone: currentPhone,
                code: code
            }),
            success: function(response) {
                if (response.code === 200) {
                    if (response.data && response.data.password_required) {
                        // 需要两步验证密码
                        $('#verifyForm').hide();
                        $('#passwordForm').show();
                        showToast('请输入两步验证密码', 'info');
                    } else {
                        // 验证成功
                        showToast('登录成功', 'success');
                        $('#addAccountModal').modal('hide');
                        loadAccounts();
                        resetForms();
                    }
                } else {
                    showToast(response.message || '验证失败', 'error');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showToast(response?.message || '验证失败', 'error');
            },
            complete: function() {
                submitBtn.prop('disabled', false).html('<i class="bi bi-check-circle"></i> 验证');
            }
        });
    });
    
    // 密码表单提交
    $('#passwordForm').submit(function(e) {
        e.preventDefault();
        
        const password = $('#password').val();
        
        if (!password) {
            showToast('请输入密码', 'warning');
            return;
        }
        
        if (!currentAccountId || !currentPhone) {
            showToast('会话已过期，请重新添加账号', 'error');
            $('#addAccountModal').modal('hide');
            resetForms();
            return;
        }
        
        // 禁用提交按钮
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> 验证中...');
        
        $.ajax({
            url: `/api/auth/accounts/${currentAccountId}/verify`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                phone: currentPhone,
                password: password
            }),
            success: function(response) {
                if (response.code === 200) {
                    showToast('登录成功', 'success');
                    $('#addAccountModal').modal('hide');
                    loadAccounts();
                    resetForms();
                } else {
                    showToast(response.message || '验证失败', 'error');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showToast(response?.message || '验证失败', 'error');
            },
            complete: function() {
                submitBtn.prop('disabled', false).html('<i class="bi bi-check-circle"></i> 验证');
            }
        });
    });
    
    // 设为活跃按钮
    $(document).on('click', '.activate-btn', function() {
        const accountId = $(this).data('id');
        
        if (!confirm('确定要将此账号设为活跃账号吗？')) {
            return;
        }
        
        $.ajax({
            url: `/api/auth/accounts/${accountId}/activate`,
            method: 'POST',
            success: function(response) {
                if (response.code === 200) {
                    showToast('已设置为活跃账号', 'success');
                    loadAccounts();
                    checkLoginStatus(); // 更新导航栏状态
                } else {
                    showToast(response.message || '设置失败', 'error');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showToast(response?.message || '设置失败', 'error');
            }
        });
    });
    
    // 删除按钮
    $(document).on('click', '.delete-btn', function() {
        const accountId = $(this).data('id');
        
        if (!confirm('确定要删除此账号吗？此操作不可恢复！')) {
            return;
        }
        
        $.ajax({
            url: `/api/auth/accounts/${accountId}`,
            method: 'DELETE',
            success: function(response) {
                if (response.code === 200) {
                    showToast('账号已删除', 'success');
                    loadAccounts();
                    checkLoginStatus(); // 更新导航栏状态
                } else {
                    showToast(response.message || '删除失败', 'error');
                }
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showToast(response?.message || '删除失败', 'error');
            }
        });
    });
    
    // 重置表单
    function resetForms() {
        $('#loginForm')[0].reset();
        $('#verifyForm')[0].reset();
        $('#passwordForm')[0].reset();
        $('#loginForm').show();
        $('#verifyForm').hide();
        $('#passwordForm').hide();
        currentAccountId = null;
        currentPhone = null;
    }
    
    // 模态框关闭时重置表单
    $('#addAccountModal').on('hidden.bs.modal', function() {
        resetForms();
    });
    
    // 页面加载时加载账号列表
    loadAccounts();
});
