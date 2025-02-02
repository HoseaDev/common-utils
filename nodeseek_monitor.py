import requests
from bs4 import BeautifulSoup
import time
import schedule
from fangtang_push import sc_send
import logging
import os
from datetime import datetime

class NodeseekMonitor:
    def __init__(self, keyword_groups, check_interval=30):
        """
        初始化监控器
        :param keyword_groups: 要监控的关键词组列表，每组关键词都需要同时出现才触发通知
                           例如: [['出', 'akile'], ['收', 'acck', '0.18']]
        :param check_interval: 检查间隔（秒）
        """
        self.url = "https://www.nodeseek.com/categories/trade"
        self.keyword_groups = keyword_groups
        self.check_interval = check_interval
        self.seen_posts = set()  # 用于存储已经看过的帖子
        
        # 设置日志
        self.setup_logging()
        self.logger.info(f"初始化监控器 - 检查间隔: {check_interval}秒")
        self.logger.info(f"监控关键词组: {keyword_groups}")

    def setup_logging(self):
        """设置日志记录"""
        # 创建logs目录（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 生成日志文件名，包含时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join('logs', f'nodeseek_monitor_{timestamp}.log')
        
        # 配置日志记录器
        self.logger = logging.getLogger('NodeseekMonitor')
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def check_posts(self):
        try:
            self.logger.info("开始检查新帖子...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            post_titles = soup.find_all(class_='post-title')
            self.logger.debug(f"获取到 {len(post_titles)} 个帖子标题")
            
            for post in post_titles:
                link = post.find('a')
                if not link:
                    continue
                    
                title = link.text.strip()
                href = link.get('href')
                post_id = href  # 使用帖子链接作为唯一标识
                
                self.logger.debug(f"检查帖子: {title}")
                
                # 如果已经处理过这个帖子，跳过
                if post_id in self.seen_posts:
                    self.logger.debug(f"帖子已处理过，跳过: {title}")
                    continue
                
                # 检查每组关键词
                for keywords in self.keyword_groups:
                    # 检查这组关键词中的所有词是否都在标题中
                    if all(keyword.lower() in title.lower() for keyword in keywords):
                        full_url = f"https://www.nodeseek.com{href}" if href.startswith('/') else href
                        keywords_str = '-'.join(keywords)
                        message = f"发现匹配帖子！\n匹配关键词组：{keywords_str}\n标题: {title}\n链接: {full_url}"
                        
                        self.logger.info(f"找到匹配！关键词组: {keywords_str}, 标题: {title}")
                        self.logger.info(f"发送通知: {message}")
                        
                        sc_send(f"Nodeseek监控：匹配到「{keywords_str}」", message)
                        self.seen_posts.add(post_id)
                        break
                        
            # 保持已见帖子列表在合理大小
            if len(self.seen_posts) > 1000:
                self.logger.info("清理已处理帖子列表...")
                self.seen_posts = set(list(self.seen_posts)[-500:])
                self.logger.info(f"清理完成，当前记录数: {len(self.seen_posts)}")
                
        except Exception as e:
            error_message = f"监控过程中出现错误: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            sc_send("Nodeseek监控错误", error_message)

    def start(self):
        """启动监控"""
        self.logger.info("启动 Nodeseek 监控服务")
        schedule.every(self.check_interval).seconds.do(self.check_posts)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("收到停止信号，监控服务停止")
        except Exception as e:
            self.logger.error(f"监控服务异常退出: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    # 设置要监控的关键词组
    keyword_groups_to_monitor = [
        ['出', 'acck'],  
        ['出','cmhk']
    ]
    
    # 创建监控器实例并启动（默认5分钟检查一次）
    monitor = NodeseekMonitor(keyword_groups_to_monitor)
    monitor.start()
