import re
import asyncio
import threading
from datetime import datetime
from database.models import Task, Group, Message
from services.telegram_service import telegram_service
from services.api_service import APIService
from config import Config

class TaskService:
    """任务管理服务"""
    
    def __init__(self):
        self.running_tasks = {}
        self.task_threads = {}
    
    def create_task(self, account_id, name, task_type='bot_search', bot_username=None,
                   search_keywords=None, target_groups=None, group_regex=None, message_regex=None, 
                   collect_mode='both', history_limit=1000, pagination_config=None, api_config=None):
        """创建任务"""
        return Task.create(
            account_id=account_id,
            name=name,
            task_type=task_type,
            bot_username=bot_username,
            search_keywords=search_keywords,
            target_groups=target_groups,
            group_regex=group_regex,
            message_regex=message_regex,
            collect_mode=collect_mode,
            history_limit=history_limit,
            pagination_config=pagination_config,
            api_config=api_config
        )
    
    def start_task(self, task_id):
        """启动任务"""
        if task_id in self.running_tasks:
            return {'status': 'error', 'message': '任务已在运行中'}
        
        task = Task.get_by_id(task_id)
        if not task:
            return {'status': 'error', 'message': '任务不存在'}
        
        # 更新任务状态
        Task.update(task_id, status='running')
        
        # 创建后台线程执行任务
        thread = threading.Thread(target=self._run_task_thread, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        self.task_threads[task_id] = thread
        self.running_tasks[task_id] = True
        
        return {'status': 'success', 'message': '任务已启动'}
    
    def stop_task(self, task_id):
        """停止任务"""
        if task_id not in self.running_tasks:
            return {'status': 'error', 'message': '任务未在运行'}
        
        self.running_tasks[task_id] = False
        Task.update(task_id, status='stopped')
        
        return {'status': 'success', 'message': '任务已停止'}
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        task = Task.get_by_id(task_id)
        if not task:
            return None
        
        return {
            'id': task['id'],
            'name': task['name'],
            'status': task['status'],
            'is_running': task_id in self.running_tasks
        }
    
    def _run_task_thread(self, task_id):
        """在线程中运行任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._execute_task(task_id))
        except Exception as e:
            print(f"任务执行错误: {str(e)}")
            Task.update(task_id, status='failed')
        finally:
            loop.close()
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            if task_id in self.task_threads:
                del self.task_threads[task_id]
    
    async def _execute_task(self, task_id):
        """执行任务"""
        task = Task.get_by_id(task_id)
        if not task:
            return
        
        # 获取任务关联的账号ID
        account_id = task.get('account_id')
        if not account_id:
            print(f"[任务{task_id}] 错误: 任务未关联账号")
            Task.update(task_id, status='failed')
            return
        
        try:
            # 检查账号登录状态
            if not await telegram_service.is_logged_in(account_id):
                print(f"[任务{task_id}] 错误: 账号{account_id}未登录")
                Task.update(task_id, status='failed')
                return
            
            print(f"[任务{task_id}] 使用账号ID: {account_id}")
            
            # 根据任务类型执行不同逻辑
            task_type = task.get('task_type', 'bot_search')
            
            if task_type == 'bot_search':
                # ========== 模式1: 机器人搜索 - 只搜索群组，不采集消息 ==========
                print(f"[任务{task_id}] 模式: 机器人搜索（只搜索群组列表）")
                
                # 获取搜索关键词
                import json
                search_keywords = task.get('search_keywords')
                if isinstance(search_keywords, str):
                    search_keywords = json.loads(search_keywords)
                
                search_keywords = search_keywords or []
                print(f"[任务{task_id}] 搜索关键词数: {len(search_keywords)}")
                
                all_links = []
                
                # 遍历每个关键词进行搜索
                for keyword in search_keywords:
                    if not self.running_tasks.get(task_id):
                        break
                    
                    print(f"[任务{task_id}] 搜索关键词: {keyword}")
                    
                    # 1. 发送关键词给机器人
                    await telegram_service.send_message_to_bot(
                        task['bot_username'], 
                        keyword,
                        account_id=account_id
                    )
                    await asyncio.sleep(2)  # 等待机器人响应
                    
                    # 2. 获取机器人返回的消息
                    messages = await telegram_service.search_bot_messages(
                        task['bot_username'],
                        limit=50,
                        account_id=account_id
                    )
                    
                    # 3. 提取群组链接
                    links = telegram_service.extract_group_links(messages)
                    print(f"[任务{task_id}] 关键词 '{keyword}' 找到 {len(links)} 个链接")
                    
                    # 4. 处理翻页（如果配置了）
                    if task['pagination_config'] and task['pagination_config'].get('next_button_text'):
                        print(f"[任务{task_id}] 处理翻页...")
                        page_links = await self._process_pagination(task, account_id)
                        links.extend(page_links)
                    
                    all_links.extend(links)
                
                # 去重
                links = list(set(all_links))
                print(f"[任务{task_id}] 去重后共 {len(links)} 个群组/频道")
                
                # 5. 正则过滤群组
                if task['group_regex']:
                    print(f"[任务{task_id}] 过滤群组...")
                    links = self._filter_by_regex(links, task['group_regex'])
                    print(f"[任务{task_id}] 过滤后剩余 {len(links)} 个群组/频道")
                
                # 5. 只保存群组信息，不采集消息
                for link in links:
                    if not self.running_tasks.get(task_id):
                        break
                    
                    try:
                        print(f"[任务{task_id}] 获取群组信息: {link}")
                        group_info = await telegram_service.join_group(link, account_id=account_id)
                        
                        # 保存群组信息
                        Group.create(
                            task_id=task['id'],
                            telegram_id=group_info['telegram_id'],
                            title=group_info['title'],
                            username=group_info['username'],
                            description=group_info['description'],
                            member_count=group_info['member_count']
                        )
                        print(f"[任务{task_id}] 群组信息已保存: {group_info['title']}")
                        
                    except Exception as e:
                        print(f"[任务{task_id}] 获取群组信息失败 {link}: {str(e)}")
                        continue
                
                # 任务完成
                Task.update(task_id, status='completed')
                print(f"[任务{task_id}] 群组搜索完成")
                
            else:
                # ========== 模式2: 直接采集 - 采集指定群组的消息 ==========
                print(f"[任务{task_id}] 模式: 直接采集消息")
                
                import json
                target_groups = task.get('target_groups')
                if isinstance(target_groups, str):
                    target_groups = json.loads(target_groups)
                
                links = target_groups or []
                print(f"[任务{task_id}] 目标群组数: {len(links)}")
                
                # 遍历每个群组并采集消息
                for link in links:
                    if not self.running_tasks.get(task_id):
                        print(f"[任务{task_id}] 任务已停止")
                        break
                    
                    try:
                        # 加入群组
                        print(f"[任务{task_id}] 加入群组: {link}")
                        group_info = await telegram_service.join_group(link, account_id=account_id)
                        
                        # 保存群组信息
                        group_id = Group.create(
                            task_id=task['id'],
                            telegram_id=group_info['telegram_id'],
                            title=group_info['title'],
                            username=group_info['username'],
                            description=group_info['description'],
                            member_count=group_info['member_count']
                        )
                        
                        if not group_id:
                            # 群组已存在，获取ID
                            existing_group = Group.get_by_telegram_id(group_info['telegram_id'])
                            group_id = existing_group['id'] if existing_group else None
                        
                        if not group_id:
                            continue
                        
                        # 获取采集模式
                        collect_mode = task.get('collect_mode', 'both')
                        history_limit = task.get('history_limit', 1000)
                        
                        # 6. 采集历史消息（如果需要）
                        if collect_mode in ['both', 'history_only']:
                            print(f"[任务{task_id}] 采集历史消息（最多{history_limit}条）...")
                            history = await telegram_service.get_history(
                                group_info['telegram_id'],
                                limit=history_limit,
                                account_id=account_id
                            )
                            
                            # 7. 过滤并保存消息
                            for msg in history:
                                if not self.running_tasks.get(task_id):
                                    break
                                
                                # 正则过滤消息内容
                                if task['message_regex']:
                                    if not re.search(task['message_regex'], msg['content']):
                                        continue
                                
                                # 保存消息
                                message_id = Message.create(
                                    group_id=group_id,
                                    telegram_message_id=msg['telegram_message_id'],
                                    sender_id=msg['sender_id'],
                                    sender_name=msg['sender_name'],
                                    content=msg['content'],
                                    media_type=msg['media_type'],
                                    message_date=msg['message_date']
                                )
                                
                                # 8. 推送到API
                                if task['api_config'] and message_id:
                                    APIService.push_data(
                                        msg,
                                        task['api_config'],
                                        task['id'],
                                        message_id
                                    )
                        
                        # 9. 启动实时监听（如果需要）
                        if collect_mode in ['both', 'realtime_only']:
                            print(f"[任务{task_id}] 启动实时监听...")
                            await self._start_realtime_listener(
                                task,
                                group_id,
                                group_info['telegram_id'],
                                account_id
                            )
                        
                    except Exception as e:
                        print(f"[任务{task_id}] 处理群组失败 {link}: {str(e)}")
                        continue
            
                # 任务完成
                if self.running_tasks.get(task_id):
                    collect_mode = task.get('collect_mode', 'both')
                    if collect_mode == 'history_only':
                        Task.update(task_id, status='completed')
                        print(f"[任务{task_id}] 历史消息采集完成")
                        # 停止任务
                        self.running_tasks[task_id] = False
                    else:
                        Task.update(task_id, status='completed')
                        print(f"[任务{task_id}] 采集完成，实时监听中...")
            
        except Exception as e:
            print(f"[任务{task_id}] 执行失败: {str(e)}")
            Task.update(task_id, status='failed')
    
    async def _process_pagination(self, task, account_id):
        """处理翻页"""
        links = []
        pagination_config = task['pagination_config']
        max_pages = pagination_config.get('max_pages', Config.MAX_PAGINATION_PAGES)
        next_button_text = pagination_config.get('next_button_text', '下一页')
        
        for page in range(max_pages):
            try:
                # 发送翻页命令
                response = await telegram_service.send_message_to_bot(
                    task['bot_username'],
                    next_button_text,
                    account_id=account_id
                )
                
                if response:
                    # 提取链接
                    page_links = telegram_service.extract_group_links([{'text': response}])
                    links.extend(page_links)
                    
                    # 等待一下避免频率限制
                    await asyncio.sleep(2)
                else:
                    break
                    
            except Exception as e:
                print(f"翻页失败: {str(e)}")
                break
        
        return links
    
    def _filter_by_regex(self, items, pattern):
        """正则过滤"""
        if not pattern:
            return items
        
        try:
            regex = re.compile(pattern)
            return [item for item in items if regex.search(item)]
        except re.error:
            print(f"正则表达式错误: {pattern}")
            return items
    
    async def _start_realtime_listener(self, task, group_id, telegram_group_id, account_id):
        """启动实时监听"""
        async def message_callback(msg):
            """消息回调函数"""
            # 正则过滤
            if task['message_regex']:
                if not re.search(task['message_regex'], msg['content']):
                    return
            
            # 保存消息
            message_id = Message.create(
                group_id=group_id,
                telegram_message_id=msg['telegram_message_id'],
                sender_id=msg['sender_id'],
                sender_name=msg['sender_name'],
                content=msg['content'],
                media_type=msg['media_type'],
                message_date=msg['message_date']
            )
            
            # 推送到API
            if task['api_config'] and message_id:
                APIService.push_data(
                    msg,
                    task['api_config'],
                    task['id'],
                    message_id
                )
        
        await telegram_service.start_listener(
            telegram_group_id, 
            message_callback,
            account_id=account_id
        )

# 全局实例
task_service = TaskService()
