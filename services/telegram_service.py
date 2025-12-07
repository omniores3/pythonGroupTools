import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import User, Channel, Chat
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import SessionPasswordNeededError
from config import Config
from database.models import Account

class TelegramService:
    """Telegram客户端服务 - 支持多账号"""
    
    def __init__(self):
        self.clients = {}  # {account_id: client}
        self.session_names = {}  # {account_id: session_name}
        self.listeners = {}  # {account_id: {group_id: handler}}
        self._loops = {}  # {account_id: loop} 每个账号的专用event loop
        self._loop_threads = {}  # {account_id: thread} 每个账号的loop线程
    
    async def login(self, account_id, api_id, api_hash, phone):
        """登录Telegram"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"开始登录流程 - 账号ID: {account_id}, 手机号: {phone}")
            
            # 创建会话文件名
            session_name = os.path.join(Config.SESSION_DIR, f'session_{phone}')
            self.session_names[account_id] = session_name
            logger.info(f"会话文件: {session_name}")
            
            # 删除旧的会话文件（如果存在）
            session_file = session_name + '.session'
            if os.path.exists(session_file):
                logger.info(f"删除旧会话文件: {session_file}")
                try:
                    os.remove(session_file)
                except Exception as e:
                    logger.warning(f"删除会话文件失败: {e}")
            
            # 创建客户端
            logger.info(f"创建Telegram客户端 - API ID: {api_id}")
            client = TelegramClient(session_name, int(api_id), api_hash)
            self.clients[account_id] = client
            
            logger.info("连接到Telegram服务器...")
            await client.connect()
            logger.info("连接成功")
            
            # 检查是否已登录
            logger.info("检查是否已授权...")
            if await client.is_user_authorized():
                logger.info("用户已授权")
                return {'status': 'success', 'message': '已登录'}
            
            # 发送验证码
            logger.info(f"发送验证码到: {phone}")
            sent_code = await client.send_code_request(phone)
            logger.info(f"验证码请求结果: {sent_code}")
            logger.info(f"验证码类型: {type(sent_code)}")
            
            # 检查验证码发送方式
            if hasattr(sent_code, 'type'):
                logger.info(f"验证码发送方式: {sent_code.type}")
            
            return {
                'status': 'code_sent', 
                'message': '验证码已发送到您的Telegram',
                'phone_code_hash': sent_code.phone_code_hash if hasattr(sent_code, 'phone_code_hash') else None
            }
            
        except Exception as e:
            logger.error(f"登录失败: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'error', 'message': f'{type(e).__name__}: {str(e)}'}
    
    async def verify_code(self, account_id, phone, code):
        """验证登录码"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"验证码验证开始 - 账号ID: {account_id}, 手机号: {phone}")
            
            # 确保client已连接
            client = self.clients.get(account_id)
            if not client:
                logger.error("client对象为None")
                return {'status': 'error', 'message': '客户端未初始化，请重新登录'}
            
            if not client.is_connected():
                logger.error("client未连接")
                return {'status': 'error', 'message': '客户端未连接，请重新登录'}
            
            logger.info("开始调用sign_in")
            await client.sign_in(phone, code)
            logger.info("sign_in成功")
            
            # 保存账号信息
            session_path = self.session_names[account_id] + '.session'
            logger.info(f"保存会话到: {session_path}")
            Account.update_session(account_id, session_path)
            
            return {'status': 'success', 'message': '登录成功'}
            
        except SessionPasswordNeededError as e:
            # 需要两步验证密码，但client仍然保持连接
            logger.info("需要两步验证密码")
            return {'status': 'password_required', 'message': '需要两步验证密码'}
        except Exception as e:
            logger.error(f"验证码验证失败: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'error', 'message': f'{type(e).__name__}: {str(e)}'}
    
    async def verify_password(self, account_id, password):
        """验证两步验证密码"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"两步验证密码验证开始 - 账号ID: {account_id}")
            
            # 确保client已连接
            client = self.clients.get(account_id)
            if not client:
                logger.error("client对象为None")
                return {'status': 'error', 'message': '客户端未初始化，请重新登录'}
            
            if not client.is_connected():
                logger.error("client未连接")
                return {'status': 'error', 'message': '客户端未连接，请重新登录'}
            
            logger.info("开始调用sign_in(password=...)")
            await client.sign_in(password=password)
            logger.info("密码验证成功")
            
            # 保存账号信息
            session_path = self.session_names[account_id] + '.session'
            logger.info(f"保存会话到: {session_path}")
            Account.update_session(account_id, session_path)
            
            return {'status': 'success', 'message': '登录成功'}
        except Exception as e:
            logger.error(f"密码验证失败: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'error', 'message': f'密码验证失败: {type(e).__name__}: {str(e)}'}
    
    async def is_logged_in(self, account_id):
        """检查指定账号是否已登录"""
        client = self.clients.get(account_id)
        
        if not client:
            # 尝试从数据库加载会话
            account = Account.get_by_id(account_id)
            if account and account['session_file']:
                session_path = account['session_file'].replace('.session', '')
                if os.path.exists(account['session_file']):
                    client = TelegramClient(
                        session_path,
                        account['api_id'],
                        account['api_hash']
                    )
                    await client.connect()
                    self.clients[account_id] = client
                    self.session_names[account_id] = session_path
        
        if client:
            return await client.is_user_authorized()
        return False
    
    async def logout(self, account_id):
        """登出指定账号"""
        client = self.clients.get(account_id)
        if client:
            await client.log_out()
            del self.clients[account_id]
            if account_id in self.session_names:
                del self.session_names[account_id]
            if account_id in self._loops:
                del self._loops[account_id]
    
    async def get_client(self, account_id=None):
        """获取客户端实例，如果不存在则创建"""
        if not account_id:
            # 如果没有指定account_id，使用活跃账号
            account = Account.get_active()
            if account:
                account_id = account['id']
            else:
                return None
        
        # 如果client已存在且已连接，直接返回
        if account_id in self.clients:
            client = self.clients[account_id]
            if client.is_connected():
                return client
        
        # 否则，从session文件重新创建client
        account = Account.get_by_id(account_id)
        if not account or not account['session_file']:
            return None
        
        session_path = account['session_file'].replace('.session', '')
        if not os.path.exists(account['session_file']):
            return None
        
        # 创建新的client实例
        client = TelegramClient(
            session_path,
            account['api_id'],
            account['api_hash']
        )
        
        # 连接
        await client.connect()
        
        # 检查是否已授权
        if not await client.is_user_authorized():
            await client.disconnect()
            return None
        
        # 保存client
        self.clients[account_id] = client
        self.session_names[account_id] = session_path
        
        return client
    
    async def search_bot_messages(self, bot_username, keyword=None, limit=100, account_id=None):
        """搜索机器人消息"""
        try:
            client = await self.get_client(account_id)
            if not client:
                raise Exception("客户端未初始化")
            
            # 获取机器人实体
            bot = await client.get_entity(bot_username)
            
            # 获取对话消息
            messages = []
            async for message in client.iter_messages(bot, limit=limit):
                if message.text:
                    if keyword is None or keyword in message.text:
                        messages.append({
                            'id': message.id,
                            'text': message.text,
                            'date': message.date
                        })
            
            return messages
            
        except Exception as e:
            raise Exception(f"搜索机器人消息失败: {str(e)}")
    
    async def send_message_to_bot(self, bot_username, message, account_id=None):
        """向机器人发送消息"""
        try:
            client = await self.get_client(account_id)
            if not client:
                raise Exception("客户端未初始化")
            
            bot = await client.get_entity(bot_username)
            await client.send_message(bot, message)
            
            # 等待响应
            await asyncio.sleep(2)
            
            # 获取最新消息
            messages = await client.get_messages(bot, limit=1)
            if messages:
                return messages[0].text
            return None
            
        except Exception as e:
            raise Exception(f"发送消息失败: {str(e)}")
    
    def extract_group_links(self, messages):
        """从消息中提取群组/频道链接"""
        links = []
        patterns = [
            r'https?://t\.me/([a-zA-Z0-9_]+)',
            r'@([a-zA-Z0-9_]+)',
            r't\.me/joinchat/([a-zA-Z0-9_-]+)'
        ]
        
        for msg in messages:
            text = msg.get('text', '')
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if match not in links:
                        links.append(match)
        
        return links
    
    async def join_group(self, link, account_id=None):
        """加入群组/频道"""
        try:
            client = await self.get_client(account_id)
            if not client:
                raise Exception("客户端未初始化")
            
            # 处理不同格式的链接
            if link.startswith('http'):
                entity = await client.get_entity(link)
            elif link.startswith('@'):
                entity = await client.get_entity(link)
            else:
                entity = await client.get_entity(f'@{link}')
            
            # 尝试加入
            if isinstance(entity, Channel):
                if not entity.left:
                    # 已经是成员
                    pass
                else:
                    await client(JoinChannelRequest(entity))
            
            # 获取群组信息
            group_info = {
                'telegram_id': entity.id,
                'title': entity.title if hasattr(entity, 'title') else link,
                'username': entity.username if hasattr(entity, 'username') else None,
                'description': entity.about if hasattr(entity, 'about') else None,
                'member_count': entity.participants_count if hasattr(entity, 'participants_count') else 0
            }
            
            return group_info
            
        except Exception as e:
            raise Exception(f"加入群组失败 {link}: {str(e)}")
    
    async def get_history(self, group_id, limit=1000, account_id=None):
        """获取群组历史消息"""
        try:
            client = await self.get_client(account_id)
            if not client:
                raise Exception("客户端未初始化")
            
            messages = []
            async for message in client.iter_messages(group_id, limit=limit):
                if message.text or message.media:
                    msg_data = {
                        'telegram_message_id': message.id,
                        'sender_id': message.sender_id,
                        'sender_name': '',
                        'content': message.text or '',
                        'media_type': 'text',
                        'message_date': message.date
                    }
                    
                    # 获取发送者名称
                    if message.sender:
                        if isinstance(message.sender, User):
                            msg_data['sender_name'] = message.sender.first_name or ''
                            if message.sender.last_name:
                                msg_data['sender_name'] += ' ' + message.sender.last_name
                    
                    # 检测媒体类型
                    if message.media:
                        if message.photo:
                            msg_data['media_type'] = 'photo'
                        elif message.video:
                            msg_data['media_type'] = 'video'
                        elif message.document:
                            msg_data['media_type'] = 'document'
                        elif message.audio:
                            msg_data['media_type'] = 'audio'
                        else:
                            msg_data['media_type'] = 'other'
                    
                    messages.append(msg_data)
            
            return messages
            
        except Exception as e:
            raise Exception(f"获取历史消息失败: {str(e)}")
    
    async def start_listener(self, group_id, callback, account_id=None):
        """启动实时监听"""
        try:
            client = await self.get_client(account_id)
            if not client:
                raise Exception("客户端未初始化")
            
            @client.on(events.NewMessage(chats=group_id))
            async def handler(event):
                msg_data = {
                    'telegram_message_id': event.message.id,
                    'sender_id': event.sender_id,
                    'sender_name': '',
                    'content': event.message.text or '',
                    'media_type': 'text',
                    'message_date': event.message.date
                }
                
                # 获取发送者名称
                sender = await event.get_sender()
                if isinstance(sender, User):
                    msg_data['sender_name'] = sender.first_name or ''
                    if sender.last_name:
                        msg_data['sender_name'] += ' ' + sender.last_name
                
                # 检测媒体类型
                if event.message.media:
                    if event.message.photo:
                        msg_data['media_type'] = 'photo'
                    elif event.message.video:
                        msg_data['media_type'] = 'video'
                    elif event.message.document:
                        msg_data['media_type'] = 'document'
                    elif event.message.audio:
                        msg_data['media_type'] = 'audio'
                    else:
                        msg_data['media_type'] = 'other'
                
                # 调用回调函数
                await callback(msg_data)
            
            # 保存监听器
            if account_id not in self.listeners:
                self.listeners[account_id] = {}
            self.listeners[account_id][group_id] = handler
            
        except Exception as e:
            raise Exception(f"启动监听失败: {str(e)}")
    
    async def stop_listener(self, group_id, account_id=None):
        """停止监听"""
        if account_id and account_id in self.listeners:
            if group_id in self.listeners[account_id]:
                client = await self.get_client(account_id)
                if client:
                    client.remove_event_handler(self.listeners[account_id][group_id])
                del self.listeners[account_id][group_id]
    
    async def run_until_disconnected(self, account_id=None):
        """保持客户端运行"""
        client = await self.get_client(account_id)
        if client:
            await client.run_until_disconnected()

# 全局实例
telegram_service = TelegramService()
