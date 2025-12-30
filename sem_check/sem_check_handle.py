# -*- coding: utf-8 -*-
import os
import glob
import utils
import json
import time
import requests
import configparser
import ctypes
import shutil
import subprocess
import zipfile
import win32gui
from selenium import webdriver
from selenium.webdriver.edge.options import Options as edge_op
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from Logger.Logger import baseLogger
from global_config import *


class PackCheckBase(object):
    def __init__(self, pack_info, download_path, report_url, pass_file_list, security_type):
        self.pack_info_ = pack_info
        self.download_path_ = download_path
        self.pack_name_ = ''
        self.pack_path_ = ''
        self.install_dir_ = ''
        self.pass_file_list_ = pass_file_list
        self.report_url_ = report_url
        self.security_type_ = security_type
        self.limit_pic_path_ = "limit_pic\\" + self.pack_info_['batch_no'] + ".png"
        if not os.path.exists("limit_pic\\"):
            os.makedirs("limit_pic\\")
        self.error_code_ = {ERROR_CODE_SUCCESS: "成功",
                            ERROR_CODE_BROWSER_LIMIT: "EDGE浏览器拦截",
                            ERROR_CODE_DEFENDER_LIMIT: "微软报毒",
                            ERROR_CODE_PACK_SIGN_ERROR: "安装包没有签名",
                            ERROR_CODE_DOWNLOAD_ERROR: "渠道包下载失败",
                            ERROR_CODE_INSTALL_ERROR: "渠道包安装失败",
                            ERROR_CODE_SIGN_ERROR: "部分文件签名校验失败",
                            ERROR_CODE_LAUNCH_ERROR: "下载器安装失败",
                            ERROR_CODE_LAUNCH_TIMEOUT: "程序启动超时",
                            ERROR_CODE_DATA_ERROR: "接口请求失败",
                            ERROR_CODE_CODE_CRASH: "代码异常",
                            ERROR_CODE_360_LIMIT: "360拦截",
                            ERROR_CODE_HUORONG_LIMIT: "火绒拦截",
                            ERROR_CODE_TENCENT_LIMIT: "腾讯拦截",
                            }

    def InitInstallDir(self):
        raise NotImplementedError

    def DownloadPack(self):
        raise NotImplementedError

    def MonitorPackInstall(self):
        raise NotImplementedError

    def CleanDownloadCache(self):
        raise NotImplementedError

    def CheckSecurityLimit(self, jump_microsoft):
        if self.security_type_ == SECURITY_TYPE_MICROSOFT:
            if jump_microsoft:
                return False
            else:
                return utils.DefenderIsLimit(self.pack_name_)
        if self.security_type_ == SECURITY_TYPE_360:
            if utils.Is360Limit(self.limit_pic_path_):
                return True
            else:
                return False
        if self.security_type_ == SECURITY_TYPE_HUORONG:
            if utils.IsHuorongLimit(self.limit_pic_path_):
                return True
            else:
                return False
        return False

    def TransLimitErrorCode(self):
        if self.security_type_ == SECURITY_TYPE_MICROSOFT:
            return ERROR_CODE_DEFENDER_LIMIT
        if self.security_type_ == SECURITY_TYPE_360:
            return ERROR_CODE_360_LIMIT
        if self.security_type_ == SECURITY_TYPE_TENCENT:
            return ERROR_CODE_TENCENT_LIMIT
        if self.security_type_ == SECURITY_TYPE_HUORONG:
            return ERROR_CODE_HUORONG_LIMIT

    def CloseLeigod(self):
        try:
            pid_list = utils.get_proc_base_pid('leigod.exe')
            if len(pid_list) > 0:
                utils.close_process_by_pid(pid_list[0]["pid"])

            time.sleep(2)
            proc_list = ["leigod.exe", "leishenSdk.exe", self.pack_name_]
            for proc in proc_list:
                utils.close_process(proc)
            baseLogger.info(msg="CloseLeigod Success!!!")

        except Exception as e:
            baseLogger.info(msg=("CloseLeigod Crash: ", e.__str__()))
            return False

    @staticmethod
    def RefreshTray():
        hwnd = win32gui.FindWindow('Shell_TrayWnd', None)
        if hwnd:
            win32gui.SendMessage(hwnd, 0x001F, 0, 0)
            win32gui.UpdateWindow(hwnd)

    def CleanPackCache(self):
        self.CloseLeigod()
        try:
            if os.path.exists(self.pack_path_):
                os.remove(self.pack_path_)
            if os.path.exists(self.install_dir_):
                shutil.rmtree(self.install_dir_)
        except Exception as e:
            baseLogger.info(msg=("CleanPackCache Crash: ", e.__str__()))
            return False

    def IsPassFile(self, file_path):
        if file_path.find("tool_") > 0:
            return True
        for pass_file in self.pass_file_list_:
            if file_path.find(pass_file) > 0:
                return True
        return False

    def VerifyFileSign(self):
        miss_sign_file = []
        temp_dir = self.install_dir_ + "\\**\*"
        for file_path in glob.glob(temp_dir, recursive=True):
            if self.IsPassFile(file_path):
                baseLogger.info(msg=("pass sign check : ", file_path))
                continue
            if os.path.isfile(file_path) and (
                    file_path.find(".dll") > 0 or file_path.find(".sys") > 0 or file_path.find(".exe") > 0):

                if utils.get_file_sign(file_path) is False:
                    baseLogger.info(msg=("VerifyFileSign error: ", file_path))
                    pos = file_path.rfind(self.install_dir_)
                    file_name = file_path[pos + len(self.install_dir_):]
                    # file_name = utils.path_file_name(file_path)
                    miss_sign_file.append(file_name)
        if len(miss_sign_file) > 0:
            no_sign_list = []
            for file_name in miss_sign_file:
                if utils.DefenderIsLimit(file_name):
                    file_name = file_name.replace('\\', '/')
                    self.ReportResult(CHECK_RESULT_FAILED, STEP_DEFENDER_CHECK, file_name)
                else:
                    no_sign_list.append(file_name)
            if len(no_sign_list) > 0:
                string = ','.join(file_info for file_info in no_sign_list)
                string = string.replace('\\', '/')
                self.ReportResult(CHECK_RESULT_WARRING, STEP_CHECK_ALL_SIGN, string)
            else:
                self.ReportResult(CHECK_RESULT_SUCCESS, STEP_CHECK_ALL_SIGN, '成功')
        else:
            self.ReportResult(CHECK_RESULT_SUCCESS, STEP_CHECK_ALL_SIGN, '成功')
        return miss_sign_file

    def DefenderLimitCheck(self):
        time.sleep(15)
        check_result = self.CheckSecurityLimit(False)
        baseLogger.info(msg=("DefenderLimitCheck: ", self.pack_name_))
        if check_result:
            baseLogger.info(msg=("security soft limit 1: ", self.pack_name_))
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[self.TransLimitErrorCode()]
            next_step = False
            baseLogger.info(msg=("windows defender limit: ", self.pack_name_))
        else:
            result_type = CHECK_RESULT_SUCCESS
            desc = self.error_code_[ERROR_CODE_SUCCESS]
            next_step = True

        self.ReportResult(result_type, STEP_DEFENDER_CHECK, desc)
        return next_step

    def PackSignCheck(self):
        if os.path.exists(self.pack_path_) is False:
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[ERROR_CODE_PACK_SIGN_ERROR]
            next_step = False
            baseLogger.info(msg=("PackSignCheck error 1: ", self.pack_name_))
        else:
            check_result = utils.get_file_sign(self.pack_path_)
            if check_result is False:
                result_type = CHECK_RESULT_FAILED
                desc = self.error_code_[ERROR_CODE_PACK_SIGN_ERROR]
                next_step = False
                baseLogger.info(msg=("PackSignCheck error 2: ", self.pack_name_))
            else:
                result_type = CHECK_RESULT_SUCCESS
                desc = self.error_code_[ERROR_CODE_SUCCESS]
                next_step = True

        if result_type != CHECK_RESULT_SUCCESS:
            time.sleep(10)
            baseLogger.info(msg=("PackSignCheck error: ", self.pack_name_))
            if self.CheckSecurityLimit(False) or os.path.exists(self.pack_path_) is False:
                result_type = CHECK_RESULT_FAILED
                desc = self.error_code_[self.TransLimitErrorCode()]
                next_step = False
                baseLogger.info(msg=("security soft limit 2: ", self.pack_name_))
                self.ReportResult(result_type, STEP_DEFENDER_CHECK, desc)
                return next_step

        self.ReportResult(result_type, STEP_CHECK_PACK_SIGN, desc)
        return next_step

    def ReportMonitorResult(self, check_result):
        if check_result == ERROR_CODE_LAUNCH_ERROR:
            desc = self.error_code_[ERROR_CODE_LAUNCH_ERROR]
            result_type = CHECK_RESULT_FAILED
            next_step = False
        elif check_result == ERROR_CODE_LAUNCH_TIMEOUT:
            desc = self.error_code_[ERROR_CODE_LAUNCH_ERROR]
            result_type = CHECK_RESULT_FAILED
            next_step = False
        elif check_result == ERROR_CODE_360_LIMIT:
            desc = self.error_code_[ERROR_CODE_360_LIMIT]
            result_type = CHECK_RESULT_FAILED
            next_step = False
        elif check_result == ERROR_CODE_HUORONG_LIMIT:
            desc = self.error_code_[ERROR_CODE_HUORONG_LIMIT]
            result_type = CHECK_RESULT_FAILED
            next_step = False
        elif check_result == ERROR_CODE_TENCENT_LIMIT:
            desc = self.error_code_[ERROR_CODE_TENCENT_LIMIT]
            result_type = CHECK_RESULT_FAILED
            next_step = False
        elif check_result == ERROR_CODE_CODE_CRASH:
            desc = self.error_code_[ERROR_CODE_CODE_CRASH]
            result_type = CHECK_RESULT_FAILED
            next_step = False
        else:
            desc = self.error_code_[ERROR_CODE_SUCCESS]
            result_type = CHECK_RESULT_SUCCESS
            next_step = True

        self.ReportResult(result_type, STEP_INSTALL, desc)
        if check_result == ERROR_CODE_SUCCESS:
            self.ReportResult(result_type, STEP_LAUNCH, desc)

        self.CloseLeigod()
        return next_step

    def ReportDownloadPackResult(self, result):
        step = STEP_DOWNLOAD
        if result == ERROR_CODE_BROWSER_LIMIT:
            result_type = CHECK_RESULT_WARRING
            desc = self.error_code_[ERROR_CODE_BROWSER_LIMIT]
            next_step = True
        elif result == ERROR_CODE_DOWNLOAD_ERROR:
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[ERROR_CODE_DOWNLOAD_ERROR]
            next_step = False
        elif result == ERROR_CODE_CODE_CRASH:
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[ERROR_CODE_CODE_CRASH]
            next_step = False
        elif result == ERROR_CODE_DEFENDER_LIMIT:
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[ERROR_CODE_DEFENDER_LIMIT]
            next_step = False
            step = STEP_DEFENDER_CHECK
        elif result == ERROR_CODE_360_LIMIT:
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[ERROR_CODE_360_LIMIT]
            next_step = False
            step = STEP_DEFENDER_CHECK
        elif result == ERROR_CODE_HUORONG_LIMIT:
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[ERROR_CODE_HUORONG_LIMIT]
            next_step = False
            step = STEP_DEFENDER_CHECK
        elif result == ERROR_CODE_TENCENT_LIMIT:
            result_type = CHECK_RESULT_FAILED
            desc = self.error_code_[ERROR_CODE_TENCENT_LIMIT]
            next_step = False
            step = STEP_DEFENDER_CHECK
        else:
            result_type = CHECK_RESULT_SUCCESS
            desc = self.error_code_[ERROR_CODE_SUCCESS]
            next_step = True

        self.ReportResult(result_type, step, desc)
        return next_step

    def ReportResult(self, check_result, check_result_type, check_desc):
        report_data = {"package_id": self.pack_info_['id'], "test_result": check_result, "test_type": check_result_type,
                       "desc": check_desc, "batch_no": self.pack_info_['batch_no'],
                       "antivirus_type": self.security_type_}

        if self.CheckSecurityLimit(True):
            report_data["desc"] = self.error_code_[self.TransLimitErrorCode()]
            report_data["test_result"] = 0

        baseLogger.info(msg=("ReportResult param: ", report_data))
        if report_data["test_result"] == 0 and os.path.exists(self.limit_pic_path_):
            with open(self.limit_pic_path_, "rb") as f:
                files = {"image_source": ("limit.png", f, 'image/png')}
                rsp = requests.post(self.report_url_, data=report_data, files=files)
                baseLogger.info(msg=("ReportResult Result1: ", rsp.content))
            os.remove(self.limit_pic_path_)
        else:
            headers = {
                'Content-Type': 'application/json'
            }
            send_data = json.dumps(report_data)
            rsp = requests.post(self.report_url_, data=send_data, headers=headers)
            baseLogger.info(msg=("ReportResult Result2: ", rsp.content))


class ZipPackCheck(PackCheckBase):
    def __init__(self, pack_info, download_path, report_url, pass_file_list, security_type):
        super().__init__(pack_info, download_path, report_url, pass_file_list, security_type)

    def InitInstallDir(self):
        return 'C:\\Program Files (x86)\\leigod'

    def DownloadPack(self):
        ret = ERROR_CODE_SUCCESS
        need_check_defender = False
        try:
            url = self.pack_info_['url']
            self.pack_name_ = utils.url_file_name(url)
            self.pack_path_ = self.download_path_ + "\\" + self.pack_name_
            if utils.DownloadFile(url, self.pack_path_) is False:
                baseLogger.info(msg=("ZipPackCheck DownloadPack Error1: ", url))
                ret = ERROR_CODE_DOWNLOAD_ERROR
                return ret, need_check_defender

            if os.path.exists(self.pack_path_) is False:
                baseLogger.info(msg=("ZipPackCheck DownloadPack Error2: ", url))
                ret = ERROR_CODE_DOWNLOAD_ERROR
                need_check_defender = True
                return ret, need_check_defender
            need_check_defender = True
            return ret, need_check_defender
        except Exception as e:
            baseLogger.info(msg=("ZipPackCheck DownloadPack crash: ", e.__str__()))
            return ERROR_CODE_CODE_CRASH, False

    def PackSignCheck(self):
        result_type = CHECK_RESULT_SUCCESS
        desc = self.error_code_[ERROR_CODE_SUCCESS]
        next_step = True
        self.ReportResult(result_type, STEP_CHECK_PACK_SIGN, desc)
        return next_step

    def MonitorPackInstall(self):
        self.install_dir_ = self.InitInstallDir()
        if os.path.exists(self.install_dir_) is False:
            os.makedirs(self.install_dir_)
        with zipfile.ZipFile(self.pack_path_, 'r') as zip_ref:
            zip_ref.extractall(self.install_dir_)
        launch_path = self.install_dir_ + "\\leigod_launcher.exe"
        baseLogger.info(msg=("MonitorPackInstall InstallDir: ", launch_path))
        if os.path.exists(launch_path) is False:
            return ERROR_CODE_INSTALL_ERROR
        subprocess.run([launch_path])
        count = 0
        while count < 600:
            if self.CheckSecurityLimit(True):
                baseLogger.info(msg=("security soft limit 3: ", launch_path))
                return self.TransLimitErrorCode()
            if utils.has_proc('leigod.exe') and utils.has_proc('leishenSdk.exe'):
                return ERROR_CODE_SUCCESS
            count = count + 1
            time.sleep(1)

        return ERROR_CODE_LAUNCH_TIMEOUT

    def CleanDownloadCache(self):
        return


class OfficialPackCheck(PackCheckBase):
    def __init__(self, pack_info, download_path, report_url, pass_file_list, security_type):
        super().__init__(pack_info, download_path, report_url, pass_file_list, security_type)

    def InitInstallDir(self):
        return 'C:\\Program Files (x86)\\LeiGod_Acc'

    def DownloadPack(self):
        ret = ERROR_CODE_SUCCESS
        need_check_defender = False
        try:
            url = self.pack_info_['url']
            self.pack_name_ = utils.url_file_name(url)
            self.pack_path_ = self.download_path_ + "\\" + self.pack_name_
            if utils.DownloadFile(url, self.pack_path_) is False:
                baseLogger.info(msg=("OfficialPackCheck DownloadPack Error1: ", url))
                ret = ERROR_CODE_DOWNLOAD_ERROR
                return ret, need_check_defender

            if os.path.exists(self.pack_path_) is False:
                baseLogger.info(msg=("OfficialPackCheck DownloadPack Error2: ", url))
                ret = ERROR_CODE_DOWNLOAD_ERROR
                need_check_defender = True
                return ret, need_check_defender
            need_check_defender = True
            return ret, need_check_defender
        except Exception as e:
            baseLogger.info(msg=("OfficialPackCheck DownloadPack crash: ", e.__str__()))
            return ERROR_CODE_CODE_CRASH, False

    def MonitorPackInstall(self):
        try:
            cmd = f'{self.pack_path_} /VERYSILENT'
            subprocess.run(cmd, shell=True, check=True)
            self.install_dir_ = self.InitInstallDir()
            launch_path = self.install_dir_ + "\\leigod_launcher.exe"
            baseLogger.info(msg=("MonitorPackInstall InstallDir: ", launch_path))
            subprocess.run([launch_path])

            count = 0
            while count < 600:
                if self.CheckSecurityLimit(True):
                    baseLogger.info(msg=("security soft limit 4: ", launch_path))
                    return self.TransLimitErrorCode()
                if utils.has_proc('leigod.exe') and utils.has_proc('leishenSdk.exe'):
                    return ERROR_CODE_SUCCESS
                count = count + 1
                time.sleep(1)

            return ERROR_CODE_LAUNCH_TIMEOUT
        except Exception as e:
            baseLogger.info(msg=("MonitorPackInstall crash: ", e.__str__()))
            return ERROR_CODE_CODE_CRASH

    def CleanDownloadCache(self):
        return


class SemPackCheck(PackCheckBase):
    def __init__(self, pack_info, download_path, report_url, pass_file_list, security_type):
        super().__init__(pack_info, download_path, report_url, pass_file_list, security_type)

    @staticmethod
    def GetElementByClass(browser, tag_name, time_out=5):
        element = None
        try:
            locator = (By.CLASS_NAME, tag_name)
            element = WebDriverWait(browser, time_out, 0.5).until(EC.presence_of_element_located(locator))
        finally:
            return element

    @staticmethod
    def GetElementByCSS(browser, tag_name, time_out=5):
        element = None
        try:
            locator = (By.CSS_SELECTOR, tag_name)
            element = WebDriverWait(browser, time_out, 0.5).until(EC.presence_of_element_located(locator))
        finally:
            return element

    @staticmethod
    def GetElementByXpath(browser, tag_name, time_out=5):
        element = None
        try:
            locator = (By.XPATH, tag_name)
            element = WebDriverWait(browser, time_out, 0.5).until(EC.presence_of_element_located(locator))
        finally:
            return element

    @staticmethod
    def GetElementByName(browser, tag_name, time_out=5):
        element = None
        try:
            locator = (By.NAME, tag_name)
            element = WebDriverWait(browser, time_out, 0.5).until(EC.presence_of_element_located(locator))
        finally:
            return element

    @staticmethod
    def GetElementByID(browser, tag_name, time_out=5):
        element = None
        try:
            locator = (By.ID, tag_name)
            element = WebDriverWait(browser, time_out, 0.5).until(EC.presence_of_element_located(locator))
        finally:
            return element

    def InitInstallDir(self):
        config_file = os.environ.get('TEMP') + '\\newdownloader\\newdownloader.ini'
        if os.path.exists(config_file):
            con = configparser.ConfigParser()
            con.read(config_file, 'utf8')
            base_url = con.get('download', 'instlpath')
            return base_url
        else:
            pos1 = self.pack_name_.rfind('_')
            pos2 = self.pack_name_.rfind('.')
            dir_name = self.pack_name_[pos1 + 1:pos2]
            return os.environ.get('PROGRAMFILES(X86)') + '\\' + dir_name

    def DownloadPack(self):
        edge_options = edge_op()
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument("InPrivate")
        edge_options.add_argument('--ignore-certificate-errors')
        edge_options.add_argument('--disable-dev-shm-usage')

        edge_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_path_,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.plugins_disabled": ["Chrome PDF Viewer"]
        })
        browser = webdriver.Edge(options=edge_options)
        ret = ERROR_CODE_SUCCESS
        need_check_defender = False

        try:
            url = self.pack_info_['url']
            self.pack_name_ = utils.url_file_name(url)
            self.pack_path_ = self.download_path_ + "\\" + self.pack_name_
            browser.get(url)
            time.sleep(5)
            if os.path.exists(self.pack_path_):
                baseLogger.info(msg=("download pack success1: ", self.pack_name_))
                utils.close_process('msedge.exe')
                return ret, need_check_defender
            browser.get("edge://downloads/all")

            action_list = ['//*[@id="save1"]', '//*[@id="urlRepModalKeepButton"]', '//*[@id="save1"]',
                           '//*[@id="app-rep-modal"]/div/button', '//*[@id="app-rep-modal"]/div[2]/button[1]']

            max_action = len(action_list)
            index = 0
            while index < max_action:
                element = self.GetElementByXpath(browser, action_list[index])
                if element:
                    need_check_defender = True
                    element.click()
                    time.sleep(2)
                    if os.path.exists(self.pack_path_):
                        ret = ERROR_CODE_BROWSER_LIMIT
                        break
                # 有些包浏览器不拦截 但是杀软拦截 需要特殊处理一下
                if element is None and action_list[index] == '//*[@id="urlRepModalKeepButton"]':
                    index = index + 2
                else:
                    index = index + 1
            if need_check_defender:
                time.sleep(10)
            else:
                time.sleep(20)
            if os.path.exists(self.pack_path_):
                baseLogger.info(msg=("download pack success2: ", self.pack_name_))
            else:
                element = self.GetElementByXpath(browser, '//*[@id="downloads-item-1"]/div[2]/div[2]/div[1]/span')
                if element:
                    text = element.text
                    if text.find('检测到病毒') > 0:
                        baseLogger.info(msg=("defender limit: ", url))
                        ret = ERROR_CODE_DEFENDER_LIMIT
                        need_check_defender = False
                    else:
                        baseLogger.info(msg=("download pack error1: ", url))
                        ret = ERROR_CODE_DOWNLOAD_ERROR
                else:
                    # print('no element !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    baseLogger.info(msg=("download pack error2: ", url))
                    ret = ERROR_CODE_CODE_NO_ELEMENT
            time.sleep(1)
            utils.close_process('msedge.exe')
            if ret == ERROR_CODE_CODE_NO_ELEMENT:
                if self.security_type_ == SECURITY_TYPE_MICROSOFT:
                    utils.DownloadFile(url, self.pack_path_)
                if os.path.exists(self.pack_path_):
                    baseLogger.info(msg=("download pack error 3: ", need_check_defender))
                    return ERROR_CODE_SUCCESS, need_check_defender
                else:
                    baseLogger.info(msg=("download pack error 4: ", need_check_defender))
                    return ERROR_CODE_DOWNLOAD_ERROR, need_check_defender
            else:
                return ret, need_check_defender
        except Exception as e:
            baseLogger.info(msg=("DownloadPack crash: ", e.__str__()))
            utils.close_process('msedge.exe')
            return ERROR_CODE_CODE_CRASH, False

    def LaunchProgress(self, wnd_title, wnd_class):
        baseLogger.info(msg=("launch process:", self.pack_path_))
        subprocess.run([self.pack_path_])
        count = 0
        while count < 60:
            if self.CheckSecurityLimit(True):
                baseLogger.info(msg=("security soft limit 5: ", self.pack_name_))
                return False, None
            hwnd = win32gui.FindWindow(wnd_class, wnd_title)
            if hwnd and win32gui.IsWindowVisible(hwnd):
                time.sleep(2)
                baseLogger.info(msg="launch proc success!!")
                return True, hwnd
            count = count + 1
            time.sleep(1)

        baseLogger.info(msg="leigod proc failed!!")
        return True, None

    def MonitorPackInstall(self):
        try:
            # time.sleep(5)
            check_result, pack_proc_wnd = self.LaunchProgress("leigod.exe", "DUIWindowFrame")

            if check_result is False:
                return self.TransLimitErrorCode()
            if pack_proc_wnd is None:
                return ERROR_CODE_LAUNCH_ERROR
            # utils.mouse_click_ext(pack_proc_wnd, 400, 300)
            ctypes.windll.user32.SendMessageW(pack_proc_wnd, 0x100, 0x0D, 0)  # WM_KEYDOWN
            ctypes.windll.user32.SendMessageW(pack_proc_wnd, 0x101, 0x0D, 0)  # WM_KEYUP
            time.sleep(2)
            ctypes.windll.user32.SendMessageW(pack_proc_wnd, 0x100, 0x0D, 0)  # WM_KEYDOWN
            ctypes.windll.user32.SendMessageW(pack_proc_wnd, 0x101, 0x0D, 0)  # WM_KEYUP
            count = 0
            self.install_dir_ = self.InitInstallDir()
            baseLogger.info(msg=("MonitorPackInstall InstallDir: ", self.install_dir_))
            while count < 600:
                if self.CheckSecurityLimit(True):
                    baseLogger.info(msg=("security soft limit 6: ", self.pack_name_))
                    return self.TransLimitErrorCode()
                if utils.has_proc('leigod.exe') and utils.has_proc('leishenSdk.exe'):
                    return ERROR_CODE_SUCCESS
                count = count + 1
                time.sleep(1)

            return ERROR_CODE_LAUNCH_TIMEOUT
        except Exception as e:
            baseLogger.info(msg=("MonitorPackInstall crash: ", e.__str__()))
            return ERROR_CODE_CODE_CRASH

    def CleanPackCache(self):
        # time.sleep(5)
        self.CloseLeigod()
        config_file = os.environ.get('TEMP') + '\\newdownloader'
        try:
            if os.path.exists(config_file):
                shutil.rmtree(config_file)
            if os.path.exists(self.pack_path_):
                os.remove(self.pack_path_)
            if os.path.exists(self.install_dir_):
                shutil.rmtree(self.install_dir_)
        except Exception as e:
            baseLogger.info(msg=("CleanPackCache Crash: ", e.__str__()))
            return False

    def CleanDownloadCache(self):
        suffix = '.crdownload'
        files = glob.glob(os.path.join(self.download_path_, f'*{suffix}'))
        for file in files:
            try:
                os.remove(file)
            except Exception as e:
                log = f'删除失败：{file}，错误：{e}'
                baseLogger.info(log)

    def CloseLeigod(self):
        try:
            pid_list = utils.get_proc_base_pid('leigod.exe')
            if len(pid_list) > 0:
                utils.close_process_by_pid(pid_list[0]["pid"])

            time.sleep(2)
            proc_list = ["leigod.exe", "newdownloader.exe", "leishenSdk.exe", self.pack_name_]
            for proc in proc_list:
                utils.close_process(proc)
            baseLogger.info(msg="CloseLeigod Success!!!")

        except Exception as e:
            baseLogger.info(msg=("CloseLeigod Crash: ", e.__str__()))
            return False


def test():
    pass
