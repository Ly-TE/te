from DrissionPage import ChromiumPage, SessionPage, ChromiumOptions
from DrissionPage.common import Actions
from CloudflareBypasser import CloudflareBypasser
import WalletTools
from OkxTools import OkxTools
import os
import pyautogui
import time
from loguru import logger
from ProxyExtension import ProxyExtension
from Models import ProxyParam, WalletOption
from CFBypassTools import CFBypassTools
from CommonHelper import CommonHelper
import random, requests, time
from Web3Tools.Tools import Tools, Excel, is_list
from Config import ips, kParticleXlsPath
from decimal import Decimal
from fake_useragent import UserAgent
import subprocess
from CommonHelper import CommonHelper, ParticleDB

kWaitTime = 3
kWaitTimeMiddle = 5
kWaitTimeLong = 10

checkInUrl = "https://pioneer.particle.network/zh-CN/point"
buyNFTUrl = "https://pioneer.particle.network/zh-CN/crossChainNFT"
depostEthUrl = "https://pioneer.particle.network/zh-CN/universalGas"


class Particle:
    def start_browser(self, serial_number):
        open_url = f"http://localhost:50325/api/v1/browser/start?serial_number={serial_number}"
        for attempt in range(5):
            try:
                resp = requests.get(open_url, timeout=10).json()
                if resp.get("code") == 0:
                    debug_port = int(resp["data"]["debug_port"])
                    return debug_port
                else:
                    print(f"\033[0;31m浏览器[{serial_number}]打开出错,正在重试...错误信息:[{resp}]\033[0m")
            except requests.RequestException as e:
                print(f"\033[0;31m请求失败: {e}\033[0m")
            time.sleep(1)

        raise Exception(f"无法启动浏览器 {serial_number}，已达到最大重试次数")

    def __init__(self, option):
        try:
            # adsPort = self.start_browser(option.serial_number)
            self.option = option
            chromePath = CommonHelper.getNewComputerChromePath() + option.name
            co = ChromiumOptions().set_paths(local_port=option.port, user_data_path=chromePath)
            # 设置启动时最大化
            co.set_argument('--start-maximized')
            # 设置初始窗口大小
            # co.set_argument('--window-size', '800,600')
            # change this to the path of the folder containing the extension
            # 判断是否配置代理
            if option.proxyParam != None:
                proxyExtension = ProxyExtension()
                proxyTmpPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "proxyPatch"))
                proxyParam = option.proxyParam
                path = proxyExtension.create_proxy_auth_extension(proxyParam.proxy_host, proxyParam.proxy_port,
                                                                  proxyParam.proxy_username, proxyParam.proxy_password,
                                                                  plugin_path=proxyTmpPath)
                logger.info("proxypath:%s" % (path))
                co.add_extension(path)
            else:
                logger.info("无代理设置")
                # 已安装的代理，取消改插件代码，才能重新联网
                proxyExtension = ProxyExtension()
                proxyTmpPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "removeProxyPatch"))
                path = proxyExtension.remove_proxy_auth_extension(plugin_path=proxyTmpPath)
                logger.info("proxypath:%s" % (path))
                co.add_extension(path)
            EXTENSION_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "turnstilePatch"))
            logger.info("EXTENSION_PATH:%s" % (EXTENSION_PATH))
            co.add_extension(EXTENSION_PATH)
            self.dp = ChromiumPage(co)
            if option.ua != None:
                logger.info("设置user-agent:%s" % (option.ua))
                self.dp.set.user_agent(option.ua)
            self.db = ParticleDB()
            # 获取当日成功的次数，默认0
            self.successCount = self.db.queryWalletCount(option.name)
            self.errorCount = 0
            self.option = option
            self.buyNFTErrorCount = 0
            self.checkInErrorCount = 0
            self.errorMsg = ""
            # 初始化excel表格
            self.excel = Excel(file=kParticleXlsPath)
            # 異常中斷標識位，如果有異常，则不再重複執行
            self.breakFlag = False
            self.aaAddress = None
            # 因為ip中斷
            self.ipLimitFlag = False
        except Exception as e:
            raise Exception(f"启动浏览器失败: {e}")

    def printWalletInfo(self):
        logger.info("初始化钱包:%s, port:%s" % (self.option.name, self.option.port))

    def run(self):
        logger.info("*****签到流程开始*****")
        self.checkIn()
        time.sleep(2)
        logger.info("*****buy nft流程开始*****")
        self.buyNFT()
        # 觸發ip限制，換個ip繼續跑
        if self.ipLimitFlag == True:
            return False
        return True

    # ping
    def ping(self, host):
        try:
            # Use the ping command with -c 1 to send only one packet
            output = subprocess.check_output(["ping", "-c", "1", host], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False

    # 一直ping失败，就跳出这个钱包
    def checkNetworkNormal(self):
        for i in range(5):
            host = "google.com"
            if self.ping(host):
                return True
            else:
                logger.error("网络异常, ping失败")
                time.sleep(3)
        return False

    def checkFaucetSufficient(self):
        logger.info("*****查询usdg开始*****")
        # 有时候usdg获取失败，需要重试
        for i in range(3):
            usdg = self.queryUsdgByAPI()
            if usdg >= 0:
                break
            self.dp.wait(kWaitTimeMiddle)
        # 排除获取失败usdg为0的情况
        if usdg >= 0:
            # 余额存到xls文件中
            self.excel.setValueByColNameAndWalletName(wallet_name=self.option.name, col_name="usdg", value=usdg)
            self.excel.setValueByColNameAndWalletName(wallet_name=self.option.name, col_name="usdg_update_time",
                                                      value=time.strftime("%Y-%m-%d %H:%M", time.localtime()))
            self.excel.save()
        else:
            self.saveErrorMsg("usdg获取失败")
            logger.error("usdg获取失败，跳过")
            return
        # 判断余额是否小于1000
        if float(usdg) < 1000:
            # 执行eth换usdg操作
            self.depositEth()

    def quit(self):
        self.dp.quit()

    # 查詢usdg餘額，通過api
    def queryUsdgByAPI(self):
        self.dp.get(checkInUrl)
        self.dp.wait(kWaitTime)
        # 是否进行了登录操作
        for i in range(3):
            loginOp = self.loginIfNeed(checkInUrl)
            # 登錄失敗重試
            if loginOp == False:
                self.queryUsdgByAPI()
                return
            else:
                self.dp.wait(kWaitTimeMiddle)
                break
        # 0.判断aaAddress是否已经获取到
        if self.aaAddress == None:
            # 1.获取通用地址
            self.dp.listen.start('pioneer-api.particle.network/users?timestamp')
            self.dp.get(checkInUrl)
            res = self.dp.listen.wait(timeout=10)  # 等待并获取一个数据包
            resBody = res.response.body
            print('res.url:%s' % (res.url))
            print('res.response.body:%s' % (resBody))
            if resBody != None and is_list(resBody) and len(resBody) > 0:
                first = resBody[0]
                self.aaAddress = first.get('aaAddress')
                print('aaAddress:', self.aaAddress)
            elif resBody != None and resBody.get('aaAddress') != None:
                self.aaAddress = resBody.get('aaAddress')
                print('aaAddress:', self.aaAddress)
            else:
                logger.error("获取aa地址失败")
                return -1
        # for packet in self.dp.listen.steps():
        #     print('packet:%s'%(packet))
        url = 'https://universal-api.particle.network/'
        data = {
            "jsonrpc": "2.0",
            "chainId": 11155111,
            "method": "universal_getTokens",
            "params": [self.aaAddress, ["usdg"]]
        }
        # 生成随机User-Agent
        ua = UserAgent()
        random_user_agent = ua.random
        # 定义请求头
        headers = {
            "User-Agent": random_user_agent
        }
        # 设置代理
        proxies = {
            "http": "http://127.0.0.1:42022",
            "https": "http://127.0.0.1:42022",
        }
        response = requests.post(url, json=data, headers=headers, proxies=proxies)
        print(response.json())
        # 提取totalBalance的值
        total_balance_str = response.json()['result'][0]['totalBalance']
        logger.info("total_balance_str:%s" % (total_balance_str))
        # 将字符串转换为十进制数值
        total_balance_decimal = Decimal(total_balance_str) / Decimal(10 ** 18)
        # 打印结果
        print(f"totalBalance: {total_balance_decimal}")
        print('-------------')
        return total_balance_decimal

    # 查詢usdg餘額
    def queryUsdg(self):
        self.dp.get(checkInUrl)
        self.dp.wait(kWaitTime)
        # 是否进行了登录操作
        for i in range(3):
            loginOp = self.loginIfNeed(checkInUrl)
            # 登錄失敗重試
            if loginOp == False:
                self.queryUsdgByAPI()
                return
            else:
                break
        self.dp.wait(kWaitTimeMiddle)
        navBar = self.dp.ele('#navbar')
        # 点击查看usdg按钮
        if navBar.eles('@class=polygon-btn-text', timeout=10):
            eles = navBar.eles('@class=polygon-btn-text')
            if eles != None and len(eles) > 0:
                eles[0].click()
        # 獲取usdg餘額
        dataSlot = self.dp.ele('@data-slot=content')
        if dataSlot.eles('@class=text-[1.125rem]', timeout=10):
            eles = dataSlot.eles('@class=text-[1.125rem]')
            if eles != None and len(eles) > 1:
                ele = eles[1]
                logger.info("els[1]=%s" % (ele.text))
                usdgBalance = Tools.getNumFromStr(ele.text)
                logger.info("usdgBalance:%s" % (usdgBalance))
                return usdgBalance

    # ETH换usdg
    def depositEth(self):
        logger.info("*****eth换usdg开始*****")
        self.dp.get(depostEthUrl)
        # 等待页面加载完成
        self.dp.wait.ele_displayed('How to get Testnet tokens')
        self.dp.wait(kWaitTimeMiddle)
        eleTag = '@class=mt-[0.7rem] flex flex-wrap gap-3 text-[0.9rem]'
        if self.dp.ele(eleTag):
            # TODO: 重復獲取，Balance很有可能為0
            for i in range(5):
                ele = self.dp.ele(eleTag)
                div_list = ele.eles('tag:div')
                div = div_list[0]
                logger.info("Balance:%s" % (div.text))
                ethBanlance = Tools.getNumFromEthStr(div.text)
                # 大于0，说明查询到余额
                if ethBanlance > 0:
                    break
                self.dp.wait(kWaitTimeMiddle)
            ethBanlanceFloat = float(ethBanlance)
            depoistValue = 0.2
            if ethBanlanceFloat > 1.01:
                depoistValue = 1.0
            else:
                # 预留0.05eth作为gas
                depoistValue = ethBanlance - 0.05
            if self.dp.ele('@class=input h-[3.4rem] flex-1 pr-[10rem]'):
                if depoistValue < 0:
                    depoistValue = 0.1
                formatNum = "{:.2f}".format(depoistValue)
                logger.info("输入eth数量:%s" % (str(formatNum)))
                div = self.dp.ele('@class=input h-[3.4rem] flex-1 pr-[10rem]')
                input = div.eles('tag:input')[0]
                input.input(str(formatNum))
            # 查到deposit按钮
            if self.dp.eles('@class=polygon-btn-text'):
                eles = self.dp.eles('@class=polygon-btn-text')
                for ele in eles:
                    logger.info("ele:%s" % (ele.text))
                    if ele.ele('text=Deposit Universal Gas'):
                        logger.info("tap Deposit btn")
                        ele.ele('text=Deposit Universal Gas').click()
                        for i in range(3):
                            result = OkxTools.signWallet(self.dp)
                            if result == True:
                                logger.info("Deposit成功")
                                self.dp.wait(kWaitTimeLong)
                                # 再次查询usdg余额,更新到xls文件中
                                usdg = self.queryUsdgByAPI()
                                self.excel.setValueByColNameAndWalletName(wallet_name=self.option.name, col_name="usdg",
                                                                          value=usdg)
                                self.excel.setValueByColNameAndWalletName(wallet_name=self.option.name,
                                                                          col_name="usdg_update_time",
                                                                          value=time.strftime("%Y-%m-%d %H:%M",
                                                                                              time.localtime()))
                                self.excel.save()
                                break
                            else:
                                logger.error("质押失败")
                            self.dp.wait(kWaitTimeLong)
        logger.info("*****eth换usdg end*****")

    # 执行签到
    def checkIn(self):
        # 检查网络状态
        # if self.checkNetworkNormal() == False:
        #     self.saveErrorMsg("网络异常，跳过")
        #     return
        self.dp.get(checkInUrl)
        self.dp.wait(kWaitTime)
        # 是否进行了登录操作
        try:
            loginOp = self.loginIfNeed(checkInUrl)
            if loginOp == False:
                self._checkInRetry()
                return
            result = self.checkinAction()
            if result != None:
                return result
        except Exception as e:
            logger.error("签到失败:%s" % (e))
            self._checkInRetry()

    # 执行购买NFT
    def buyNFT(self):
        if self.breakFlag:
            return
        self.dp.get(buyNFTUrl)
        self.dp.wait.doc_loaded()
        self.dp.wait(5.0)
        # 是否进行了登录操作
        loginOp = self.loginIfNeed(buyNFTUrl)
        if loginOp == False:
            self._buyNFTRetry()
            return
        self.excutePurchaseBtn()

    # 未登录请先登录
    def loginIfNeed(self, reloadHtml):
        # 判断是否存在start按钮
        if self.dp.ele('text=start', timeout=3):
            logger.info("存在start按钮")
            self.dp.ele('text=start').click()
        self.dp.wait(kWaitTime)
        # 显示了Lanuch按钮
        isShow = self.isShowLaunchBtn()
        if isShow:
            logger.info("Jumpout Lanuch Page")
            self.jumpOutLuanchPage()
            return True
        elif self.dp.ele('JOIN'):
            logger.info("JOIN")
            self.dp.ele('JOIN').click()
            self.dp.wait(kWaitTimeMiddle)
            # 搜索text为okx wallet的按钮
            if self.dp.ele('text=okx Wallet'):
                logger.info("OKX WALLET")
                self.dp.ele('text=okx Wallet').click()
            # 判断是否显示了WalletConnect窗口，需要重新走刷新流程重试
            reuslt = self.checkShowedWalletConnect()
            if reuslt == False:
                return False
            OkxTools.connect(self.dp, reloadHtml)
            return True
        else:
            return True

    # 判断是否显示了WalletConnect窗口，并返回False
    def checkShowedWalletConnect(self):
        self.dp.wait(kWaitTimeMiddle)
        # TODO: 判断是否弹出了选择walletconnect钱包界面，此时需要重新刷新。
        eles = self.dp.eles('tag=wcm-modal', timeout=5)
        # 大于2个说明 WalletConnect弹窗
        if len(eles) > 1:
            logger.info("WalletConnect弹窗，需要重新刷新页面")
            return False
        return True

    # 是否显示了Launch按钮，如果显示了表明钱包已连接，不需要连接钱包
    def isShowLaunchBtn(self):
        btn = self.dp.ele('@class=polygon-btn-text', timeout=5)
        if btn != None and btn.text == "Launch":
            return True
        else:
            return False

    # 签到
    def checkinAction(self):
        logger.info("checkinAction")
        self.dp.wait(kWaitTime)
        # 判断用户是否已经签到
        if self.dp.ele('text=Checked in', timeout=5):
            logger.info("已经签到，进入购买流程")
            return
        if self.dp.ele('@class=polygon-btn-text', timeout=5):
            self.dp.ele('text=Check-in').click()
            self.dp.wait(kWaitTime)
            self.dp.ele('text=Check-in').click()
        self.dp.wait(kWaitTimeLong)
        if self.dp.ele('text=Confirm'):
            logger.info("Confirm")
            self.dp.ele('text=Confirm').click()
        self.dp.wait(10.0)
        logger.info("cf签名验证")
        # 判断是否需要cf签名验证
        if self.dp.ele('#cf-turnstile', timeout=5):
            # 绕过cf验证
            result = CFBypassTools.bypassCFV3(self.dp)
            if result == False:
                self.saveErrorMsg("cf验证组件加载失败，可能是ip问题")
                return
        else:
            logger.info("未获取到cf元素，确认按钮重点击")
            result = self.tapCheckConfirmBtn()
            if result == False:
                logger.info("签到失败，调重试方法")
                self._checkInRetry()
                return
        # 钱包签名
        result = OkxTools.signWallet(self.dp)
        # 用弹窗方式判断是否成功
        self.dp.wait.eles_loaded('@class=Toastify__toast-body', timeout=10)
        alertEle = self.dp.ele('@class=Toastify__toast-body', timeout=10)
        if alertEle != None:
            print(alertEle)
            logger.info(alertEle.text)
            # 超过ip限制中断程序
            if 'ip' in alertEle.text:
                logger.info("超过ip限制，换账号")
                self.breakFlag = True
                # 保存ip超过限制次数到数据库
                self.db.saveIPPortExceedMaxCount(self.option.proxyParam.proxy_port)
                self.ipLimitFlag = True
                return
        if result == False:
            self._checkInRetry()
        else:
            logger.info("签到成功")
            self.db.appendFinishCount(self.option.name)

    def tapCheckConfirmBtn(self):
        if self.dp.ele('text=Confirm'):
            logger.info("tap Confirm Btn")
            self.dp.ele('text=Confirm').click()
        self.dp.wait(5.0)
        logger.info("再次请求cf签名验证")
        # 判断是否需要cf签名验证
        if self.dp.ele('#cf-turnstile', timeout=5):
            # 绕过cf验证
            CFBypassTools.bypassCFV3(self.dp)
            return True
        else:
            logger.info("再次尝试未获取到cf元素")
            return False

    # 在购买页，点击Purchase按钮操作
    def excutePurchaseBtn(self):
        logger.info("excutePurchaseBtn")
        self.dp.wait(2.0)
        chains = ['Arbitrum Sepolia']
        # 获取下拉列表，选择链
        if self.dp.ele('@aria-haspopup=listbox'):
            # chains里面随机取值
            chainText = random.choice(chains)
            self.dp.ele('@aria-haspopup=listbox').click()
            chainEle = ('text=%s' % (chainText))
            if self.dp.ele(chainEle):
                logger.info("Select chains:%s" % (chainEle))
                self.dp.ele(chainEle).click()
                self.dp.wait(2.0)
        # Purchase需要多匹配来实现
        purchaseRule = '@@class=group-data-[disabled=true]:opacity-70@@text()=Purchase'
        if self.dp.ele(purchaseRule):
            self.dp.ele(purchaseRule).click()
        self.dp.wait(2.0)
        usdgSelectRule = '@class=flex items-center gap-5 max-sm:gap-2'
        if self.dp.ele(usdgSelectRule):
            self.dp.ele(usdgSelectRule).click()
        self.dp.wait(2.0)
        if self.dp.ele('Next'):
            logger.info("Next")
            self.dp.ele('Next').click()
        self.dp.wait(5.0)
        purchaseAgainRule = '@class=polygon-btn group mx-auto mt-14 w-[18rem] max-lg:text-sm max-md:scale-75 max-md:text-xl max-md:hover:scale-75 max-md:active:scale-[0.7] data-[disabled=true]:pointer-events-none data-[disabled=true]:saturate-50'
        if self.dp.ele(purchaseAgainRule, timeout=25):
            logger.info("Purchase")
            self.dp.ele(purchaseAgainRule).click()
        self.dp.wait(5.0)
        # 绕过cf验证
        CFBypassTools.bypassCFV3(self.dp)
        self.dp.wait(kWaitTimeMiddle)
        # TODO: 用代理ip，可能会出现没弹出cf验证，直接提示trunstile失败，这种需要重新刷新网页重试。
        # TODO: 报错是wallet窗口拿不到，直接崩溃，signWallet加一个try catch处理这种异常。
        # 钱包签名
        result = OkxTools.signWallet(self.dp)
        # okx钱包没拉起来，重试
        if result == False:
            self._buyNFTRetry()
            return
        # 用弹窗方式判断是否成功
        self.dp.wait.eles_loaded('@class=Toastify__toast-body', timeout=5)
        alertEle = self.dp.ele('@class=Toastify__toast-body', timeout=5)
        if alertEle != None:
            print(alertEle)
            logger.info(alertEle.text)
            # 超过ip限制中断程序
            if 'ip' in alertEle.text:
                logger.info("超过ip限制，换账号")
                self.ipLimitFlag = True
                self.db.saveIPPortExceedMaxCount(self.option.proxyParam.proxy_port)
                return
            if 'uncompleted transaction' in alertEle.text:
                logger.info("未完成交易，sleep xx秒重试")
                self.dp.wait(150.0)
                self.excutePurchaseBtn()
                return
        self.dp.wait(kWaitTimeMiddle)
        if self.dp.ele('SUCCESSFULLY！', timeout=5):
            logger.info("购买成功，取消成功弹窗")
            self.db.appendFinishCount(self.option.name)
            self.successCount += 1
            logger.info("成功次数：%d" % (self.successCount))
            if self.successCount > 8:
                logger.info("超出日限制9次")
                return
            # 执行下一次购买操作
            self.dp.get(buyNFTUrl)
            self.dp.wait.doc_loaded()
            self.dp.wait(5.0)
            self.excutePurchaseBtn()
        else:
            logger.info("购买失败")
            self.errorCount += 1
            if self.errorCount > 4:
                logger.info("错误次数过多，换另一个钱包")
                return
            # 执行下一次购买操作
            self.dp.wait(10)
            self.excutePurchaseBtn()

    # 跳过Luanch等三个欢迎页面
    def jumpOutLuanchPage(self):
        if self.dp.ele('LAUNCH'):
            logger.info("点击LAUNCH按钮")
            self.dp.ele('LAUNCH').click()
        else:
            # 点击页面任意位置
            logger.info("点击页面任意位置")
            self.dp.actions.move(200, 200).click()
            self.dp.wait(kWaitTime)
            logger.info("再次点击")
            self.dp.actions.move(200, 200).click()
            if self.dp.ele('Click to launch'):
                logger.info("Click to launch")
                self.dp.ele('Click to launch').click()
            self.dp.wait(kWaitTime)
            logger.info("再次点击")
            self.dp.actions.move(200, 200).click()
            if self.dp.ele('LAUNCH'):
                logger.info("LAUNCH")
                self.dp.ele('LAUNCH').click()

    def testTapOkxBtn(self):
        self.dp.get('https://pioneer.particle.network/zh-CN/signup')
        self.dp.wait(3.0)
        if self.dp.ele('okx Wallet'):
            logger.info("OKX WALLET")
            logger.info("ele text:%s" % (self.dp.ele('okx Wallet').text))
            self.dp.ele('okx Wallet').click()

    # 购买nft从0开始重试，添加失败次数限制，防止死循环
    def _buyNFTRetry(self):
        logger.info("购买nft重试, 失败次数：%d" % (self.buyNFTErrorCount))
        self.buyNFTErrorCount += 1
        if self.buyNFTErrorCount > 4:
            logger.info("buynft错误次数过多，换另一个钱包")
            return False
        logger.info("再次执行buyNFT()")
        self.buyNFT()

    # 签到从0开始重试，添加失败次数限制，防止死循环
    def _checkInRetry(self):
        logger.info("签到重试, 失败次数：%d" % (self.checkInErrorCount))
        self.checkInErrorCount += 1
        if self.checkInErrorCount > 4:
            logger.info("checkin错误次数过多，换另一个钱包")
            self.breakFlag = True
            return
        self.checkIn()

    def saveErrorMsg(self, msg):
        self.errorMsg += msg + "\n"
        logger.error(self.errorMsg)
        self.excel.setValueByColNameAndWalletName(wallet_name=self.option.name, col_name="error_msg",
                                                  value=self.errorMsg)
        self.excel.save()

# if __name__ == '__main__':
# wallet3 = WalletOption("Account3", "10003")
# demo = Particle(wallet3)
# demo.run()
# demo.buyNFT()
# demo.testTapOkxBtn()