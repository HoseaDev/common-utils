from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import logging
import subprocess
from datetime import datetime

from fangtang_push import sc_send

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'cmhk_buyer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

class CMHKBuyer:
    def __init__(self):
        self.driver = None
        self.target_url = "https://cmhk.io/cart.php?gid=1"  # CMHK NAT产品页面
        self.attempt_count = 0
        self.max_retries = 3  # 连续失败最大重试次数

    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        try:
            # 获取ChromeDriver路径
            chromedriver_path = subprocess.check_output(['which', 'chromedriver']).decode().strip()
            
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')  # 无头模式，取消注释以启用
            
            # 设置User-Agent
            options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36')
            
            # 添加其他请求头
            options.add_argument('accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7')
            options.add_argument('accept-language=zh-CN,zh;q=0.9')
            options.add_argument('sec-ch-ua="Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"')
            options.add_argument('sec-ch-ua-mobile=?0')
            options.add_argument('sec-ch-ua-platform="macOS"')
            
            # 创建Service对象
            service = Service(executable_path=chromedriver_path)
            
            # 使用Service对象创建driver
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            logging.info("Chrome浏览器启动成功")
            
        except Exception as e:
            logging.error(f"设置Chrome驱动失败: {str(e)}")
            raise

    def set_cookies(self):
        """设置cookies"""
        try:
            # 首先访问目标域名，这样才能设置cookie
            self.driver.get("https://cmhk.io")
            
            # 设置cookies
            cookies = [
                {
                    "name": "WHMCSy551iLvnhYt7",
                    "value": "7i2u34p73ospgjao58vni5ch9j"
                },
                {
                    "name": "WHMCSUser",
                    "value": "181%3A%3Aaedd68e8b937b208d304dc06260fc89b9efe28ed"
                }
            ]
            
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            
            logging.info("Cookies设置成功")
            return True
        except Exception as e:
            logging.error(f"设置Cookies失败: {str(e)}")
            return False

    def check_and_buy(self):
        """检查产品是否可购买并尝试购买"""
        try:
            self.attempt_count += 1
            logging.info(f"开始第 {self.attempt_count} 次尝试购买...")
            
            self.driver.get(self.target_url)
            
          
            
            # 查找"立即购买"按钮
            try:
                buy_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "product1-order-button"))
                )
            except TimeoutException:
                logging.error("未找到购买按钮")
                return False
            
            # 点击购买按钮
            try:
                buy_button.click()
                logging.info("已点击购买按钮")
            except Exception as e:
                logging.error(f"点击购买按钮失败: {str(e)}")
                return False
            
            # 等待页面加载，检查是否成功
            try:
                # 首先检查是否出现缺货页面
                try:
                    time.sleep(1)
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "header-lined"))
                    )
                    header_text = self.driver.find_element(By.CLASS_NAME, "header-lined").text
                    if "缺货" in header_text:
                        logging.info("产品缺货，准备点击返回按钮")
                        try:
                            # 查找并点击"返回并重试"按钮
                            retry_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '返回并重试')]"))
                            )
                            retry_button.click()
                            logging.info("已点击返回按钮")
                            time.sleep(3)
                        except Exception as e:
                            logging.error(f"点击返回按钮失败: {str(e)}")
                        return False
                except TimeoutException:
                    pass

                # 检查是否到了配置页面
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, "customfield6"))
                    )
                    # 勾选购买须知
                    purchase_notice = self.driver.find_element(By.ID, "customfield6")
                    # 检查是否已经勾选
                    if not purchase_notice.is_selected():
                        purchase_notice_label = purchase_notice.find_element(By.XPATH, "following-sibling::ins")
                        self.driver.execute_script("arguments[0].click();", purchase_notice_label)
                        logging.info("已勾选购买须知")
                    else:
                        logging.info("购买须知已经勾选")

                    # 勾选法律法规
                    legal_notice = self.driver.find_element(By.ID, "customfield7")
                    # 检查是否已经勾选
                    if not legal_notice.is_selected():
                        legal_notice_label = legal_notice.find_element(By.XPATH, "following-sibling::ins")
                        self.driver.execute_script("arguments[0].click();", legal_notice_label)
                        logging.info("已勾选法律法规")
                    else:
                        logging.info("法律法规已经勾选")

                    # 点击继续按钮
                    continue_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "btnCompleteProductConfig"))
                    )
                    continue_button.click()
                    logging.info("已点击继续按钮")

                    # 等待页面加载完成
                    time.sleep(1)

                    # 等待并点击结账按钮
                    try:
                        # 首先等待购物车页面加载
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "view-cart-items"))
                        )
                        
                        checkout_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, "checkout"))
                        )
                        self.driver.execute_script("arguments[0].click();", checkout_button)
                        logging.info("已点击结账按钮")
                        
                        # 等待结账页面加载
                        try:
                            # 等待结账页面标题加载
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "header-lined"))
                            )
                            
                            # 点击结账页面的提交按钮
                            submit_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.ID, "btnCompleteOrder"))
                            )
                            self.driver.execute_script("arguments[0].click();", submit_button)
                            logging.info("已点击提交订单按钮")
                            return True
                        except TimeoutException:
                            logging.error("未找到提交订单按钮")
                            return False
                        except Exception as e:
                            logging.error(f"点击提交订单按钮失败: {str(e)}")
                            return False

                    except TimeoutException:
                        logging.error("未找到结账按钮")
                        return False
                    except Exception as e:
                        logging.error(f"点击结账按钮失败: {str(e)}")
                        return False

                except TimeoutException:
                    logging.error("未找到配置页面元素")
                    return False
                except Exception as e:
                    logging.error(f"配置页面操作失败: {str(e)}")
                    return False

            except TimeoutException:
                logging.error("添加到购物车失败")
                return False
                
        except Exception as e:
            logging.error(f"购买过程出错: {str(e)}")
            return False

    def run(self, interval=1):
        """运行抢购程序"""
        try:
            self.setup_driver()
            if not self.set_cookies():
                raise Exception("设置Cookies失败")
            
            consecutive_errors = 0
            while True:
                logging.info("开始检查产品状态...")
                try:
                    if self.check_and_buy():
                        logging.info("成功加入购物车！")
                        # 成功后保持窗口打开，等待用户手动关闭
                        sc_send("cmhk下单成功。请登录支付")
                        input("请在完成操作后按回车键关闭浏览器...")
                        break
                    consecutive_errors = 0  # 重置连续错误计数
                except Exception as e:
                    consecutive_errors += 1
                    logging.error(f"发生错误: {str(e)}")
                    if consecutive_errors >= self.max_retries:
                        logging.error(f"连续失败{self.max_retries}次，程序退出")
                        # 失败后也保持窗口打开，等待用户手动关闭
                        input("请在检查错误后按回车键关闭浏览器...")
                        break
                
                time.sleep(interval)
                
        except Exception as e:
            logging.error(f"程序运行错误: {str(e)}")
            # 发生异常时也保持窗口打开，等待用户手动关闭
            input("请在检查错误后按回车键关闭浏览器...")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    buyer = CMHKBuyer()
    buyer.run()
