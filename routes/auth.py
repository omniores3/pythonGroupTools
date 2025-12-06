from flask import Blueprint, request, jsonify
import asyncio
from database.models import Account
from services.telegram_service import telegram_service

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """获取所有账号列表"""
    try:
        accounts = Account.get_all()
        
        # 检查每个账号的登录状态
        for account in accounts:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                is_logged_in = loop.run_until_complete(
                    telegram_service.is_logged_in(account['id'])
                )
                account['is_logged_in'] = is_logged_in
            finally:
                loop.close()
        
        return jsonify({
            'code': 200,
            'data': accounts
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'获取账号列表失败: {str(e)}'}), 500

@auth_bp.route('/accounts', methods=['POST'])
def add_account():
    """添加新账号（开始登录流程）"""
    try:
        from config import Config
        
        data = request.json
        phone = data.get('phone')
        
        if not phone:
            return jsonify({'code': 400, 'message': '手机号不能为空'}), 400
        
        # 从配置文件读取API ID和API Hash
        api_id = Config.TELEGRAM_API_ID
        api_hash = Config.TELEGRAM_API_HASH
        
        if not api_id or not api_hash:
            return jsonify({'code': 400, 'message': '请先在.env文件中配置TELEGRAM_API_ID和TELEGRAM_API_HASH'}), 400
        
        # 创建账号记录（不设置为活跃）
        account_id = Account.create(api_id, api_hash, phone)
        
        # 异步登录 - 不关闭loop，让后续验证使用
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 保存loop到telegram_service，供后续使用
        telegram_service._loops[account_id] = loop
        
        result = loop.run_until_complete(
            telegram_service.login(account_id, api_id, api_hash, phone)
        )
        
        if result['status'] == 'success' or result['status'] == 'code_sent':
            result['account_id'] = account_id
            return jsonify({'code': 200, 'message': result['message'], 'data': result})
        else:
            # 登录失败，关闭loop并删除账号
            loop.close()
            if account_id in telegram_service._loops:
                del telegram_service._loops[account_id]
            Account.delete(account_id)
            return jsonify({'code': 500, 'message': result['message']}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 出错时清理
        if 'account_id' in locals() and account_id in telegram_service._loops:
            telegram_service._loops[account_id].close()
            del telegram_service._loops[account_id]
        return jsonify({'code': 500, 'message': f'添加账号失败: {str(e)}'}), 500

@auth_bp.route('/accounts/<int:account_id>/verify', methods=['POST'])
def verify_account(account_id):
    """验证账号登录码或密码"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = request.json
        logger.info(f"收到账号 {account_id} 的验证请求: {data.keys()}")
        
        phone = data.get('phone')
        code = data.get('code')
        password = data.get('password')
        
        if not phone:
            logger.error("手机号为空")
            return jsonify({'code': 400, 'message': '手机号不能为空'}), 400
        
        logger.info(f"账号ID: {account_id}, 手机号: {phone}, 验证码: {'有' if code else '无'}, 密码: {'有' if password else '无'}")
        
        # 使用login时创建的同一个loop
        if account_id not in telegram_service._loops:
            logger.error("event loop不存在，请重新登录")
            return jsonify({'code': 400, 'message': '会话已过期，请重新添加账号'}), 400
        
        loop = telegram_service._loops[account_id]
        asyncio.set_event_loop(loop)
        
        if password:
            # 验证两步验证密码
            logger.info("开始验证两步验证密码")
            result = loop.run_until_complete(
                telegram_service.verify_password(account_id, password)
            )
            logger.info(f"密码验证结果: {result}")
        elif code:
            # 验证登录码
            logger.info("开始验证登录码")
            result = loop.run_until_complete(
                telegram_service.verify_code(account_id, phone, code)
            )
            logger.info(f"验证码验证结果: {result}")
        else:
            logger.error("验证码和密码都为空")
            return jsonify({'code': 400, 'message': '验证码或密码不能为空'}), 400
        
        if result['status'] == 'success':
            logger.info("验证成功，关闭loop")
            # 验证成功，关闭loop
            loop.close()
            del telegram_service._loops[account_id]
            return jsonify({'code': 200, 'message': result['message']})
        elif result['status'] == 'password_required':
            logger.info("需要两步验证密码，保持loop")
            # 需要密码，保持loop不关闭
            return jsonify({'code': 200, 'message': result['message'], 'data': {'password_required': True}})
        else:
            logger.error(f"验证失败: {result['message']}")
            # 验证失败，关闭loop并删除账号
            loop.close()
            del telegram_service._loops[account_id]
            Account.delete(account_id)
            return jsonify({'code': 500, 'message': result['message']}), 500
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"验证异常: {error_trace}")
        print(f"验证异常详情:\n{error_trace}")
        # 出错时关闭loop并删除账号
        if account_id in telegram_service._loops:
            telegram_service._loops[account_id].close()
            del telegram_service._loops[account_id]
        Account.delete(account_id)
        return jsonify({'code': 500, 'message': f'验证失败: {str(e)}'}), 500

@auth_bp.route('/accounts/<int:account_id>/activate', methods=['POST'])
def activate_account(account_id):
    """设置为活跃账号"""
    try:
        account = Account.get_by_id(account_id)
        if not account:
            return jsonify({'code': 404, 'message': '账号不存在'}), 404
        
        # 检查是否已登录
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            is_logged_in = loop.run_until_complete(
                telegram_service.is_logged_in(account_id)
            )
        finally:
            loop.close()
        
        if not is_logged_in:
            return jsonify({'code': 400, 'message': '账号未登录，无法设置为活跃'}), 400
        
        Account.set_active(account_id)
        
        return jsonify({'code': 200, 'message': '已设置为活跃账号'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'设置活跃账号失败: {str(e)}'}), 500

@auth_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """删除账号"""
    try:
        account = Account.get_by_id(account_id)
        if not account:
            return jsonify({'code': 404, 'message': '账号不存在'}), 404
        
        # 如果有保存的loop，先关闭
        if account_id in telegram_service._loops:
            telegram_service._loops[account_id].close()
            del telegram_service._loops[account_id]
        
        # 登出并删除client
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(telegram_service.logout(account_id))
        except:
            pass
        finally:
            loop.close()
        
        # 删除账号记录
        Account.delete(account_id)
        
        return jsonify({'code': 200, 'message': '账号已删除'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'删除账号失败: {str(e)}'}), 500

@auth_bp.route('/status', methods=['GET'])
def status():
    """获取当前活跃账号状态"""
    try:
        account = Account.get_active()
        
        if account:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                is_logged_in = loop.run_until_complete(
                    telegram_service.is_logged_in(account['id'])
                )
            finally:
                loop.close()
        else:
            is_logged_in = False
        
        return jsonify({
            'code': 200,
            'data': {
                'is_logged_in': is_logged_in,
                'account': account
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'获取状态失败: {str(e)}'}), 500
