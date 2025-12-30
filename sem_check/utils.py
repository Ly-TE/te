import os
import json
import psutil
import win32gui
import win32process
import Evtx.Evtx as evtx
import html
from xml.dom import minidom
import time
import subprocess
import win32con
import win32api
import win32com.client
import requests
import pyautogui
import ctypes
from ctypes import wintypes
from signify.authenticode.signed_pe import SignedPEFile
from Logger.Logger import baseLogger


# title leigod.exe
# class DUIWindowFrame
def is360_wnd():
    hwnd = win32gui.FindWindow('Q360HIPSClass', None)
    if hwnd and win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
        return hwnd
    hwnd = win32gui.FindWindow('360WDSingleRiskWnd', None)
    if hwnd and win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
        return hwnd
    hwnd = win32gui.FindWindow('360WDMultiRiskWnd', None)
    if hwnd and win32gui.IsWindowVisible(hwnd) and win32gui.IsWindow(hwnd):
        return hwnd
    return None


def ScreenShot(file_path):
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        return True
    except Exception as e:
        baseLogger.info(msg=("ScreenShot Crash: ", e.__str__()))
        return False


def top_window(hwnd):
    top_wnd = win32gui.GetForegroundWindow()
    if top_wnd == hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        return rect
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    win32gui.ShowWindow(hwnd, 1)
    win32gui.SetForegroundWindow(hwnd)
    rect = win32gui.GetWindowRect(hwnd)
    return rect


def get_upload_config(file_name):
    url = "http://staffapi.leigod.com/tools/bigfile/upload?filename=%s" % file_name
    rsp = requests.get(url, verify=False, timeout=5)
    if rsp.status_code != 200:
        baseLogger.info(msg=("get_upload_config error1: ", rsp.status_code))
        return False, {}

    config = json.loads(rsp.text)
    if config["code"] != 0:
        baseLogger.info(msg=("get_upload_config error2: ", config["code"]))
        return False, {}

    return True, config


def upload_file(url, req_header, file_path):
    ffile = open(file_path, "rb")
    file_data = ffile.read()
    ffile.close()

    rsp = requests.put(url, data=file_data, headers=req_header, timeout=10)

    if rsp.status_code != 200:
        baseLogger.info(msg=("upload_file error: ", rsp.status_code))
        return False

    return True


def upload_image(image_path):
    try:

        ret, upload_config = get_upload_config(image_path)
        if ret is False:
            return ""

        req_header = {"Content-Type": upload_config["data"]["ActualSignedRequestHeaders"]["Content-Type"],
                      "Host": upload_config["data"]["ActualSignedRequestHeaders"]["Host"]}

        url = upload_config["data"]["SignedUrl"]
        ret = upload_file(url, req_header, image_path)
        if ret is False:
            return ""
        return "/" + upload_config["data"]["path"]
    except Exception as e:
        baseLogger.info(msg=("UploadImage crash: ", e.__str__()))
        return ""


def kill_process_by_name(process_name):
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                proc.kill()
                print(f"Process {process_name} killed.")
                break
        else:
            print(f"Process {process_name} not found.")
    except Exception as e:
        baseLogger.info(msg=("kill_process_by_name crash: ", e.__str__()))


def has_proc(proc_name):
    proc_name = str.lower(proc_name)
    for proc in psutil.process_iter(['name']):
        temp_name = str.lower(proc.info['name'])
        if temp_name == proc_name:
            return True
    return False


def launch_process(proc_path, wnd_title, wnd_class):
    baseLogger.info(msg=("launch process:", proc_path))
    subprocess.run([proc_path])
    count = 0
    while count < 60:
        hwnd = win32gui.FindWindow(wnd_class, wnd_title)
        if hwnd and win32gui.IsWindowVisible(hwnd):
            # top_window(hwnd)
            time.sleep(2)
            baseLogger.info(msg="launch proc success!!")
            return hwnd
        count = count + 1
        time.sleep(1)

    baseLogger.info(msg="leigod proc failed!!")
    return None


# 雷神（武汉）网络技术有限公司
def get_file_sign(filename: str):
    try:
        with open(filename, "rb") as f:
            pe_file = SignedPEFile(f)
            sign_list = list(pe_file.signed_datas)
        if len(sign_list) == 0:
            baseLogger.info(msg="get_file_sign error1!!")
            return False

        for sign in sign_list:
            name = sign.certificates[-1].subject.rdns[0][1]
            if len(name) > 0:
                return True

        baseLogger.info(msg="get_file_sign error2!!")
        return False
    except Exception as e:
        baseLogger.info(msg="get_file_sign crash!!")
        return False


'''
def get_file_sign(filename: str):
    try:
        # cmd = f'signtool verify /pa /v "{filename}"'
        out = subprocess.check_output(['signtool.exe', 'verify', '/pa', '/v', filename])
        temp = str(out, encoding='utf-8')
        return True
    except subprocess.CalledProcessError as e:
        return False
    except FileNotFoundError:
        baseLogger.info("get_file_sign FileNotFoundError")
        return False
'''


def url_file_name(url):
    pos = url.rfind('/')
    result = url[pos + 1:]
    return result


def path_file_name(file_path):
    pos = file_path.rfind('/')
    if pos > 0:
        result = file_path[pos + 1:]
        return result
    pos = file_path.rfind('\\')
    if pos > 0:
        result = file_path[pos + 1:]
        return result
    return ""


def CleanDefenderEventLog():
    try:
        subprocess.run(['wevtutil', 'cl', 'Microsoft-Windows-Windows Defender/Operational'])
        return True
    except Exception as e:
        return False


def close_process(proc_name):
    proc_name = str.lower(proc_name)
    for proc in psutil.process_iter(['name']):
        temp_name = str.lower(proc.info['name'])
        if temp_name == proc_name:
            proc.kill()


def close_process_by_pid(pid):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == pid:
            proc.kill()


def get_proc_base_pid(proc_name):
    result_list = []
    proc_name = str.lower(proc_name)
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
        temp_name = str.lower(proc.info['name'])
        if temp_name == proc_name:
            result_list.append({
                'pid': proc.info['pid'],
                'create_time': proc.info['create_time']
            })
    result_list.sort(key=lambda x: x['create_time'])
    return result_list


def DefenderIsLimit(pack_name):
    system32_path = os.path.join(os.environ['systemroot'], 'system32')
    log_path = system32_path + "\\winevt\\Logs\\Microsoft-Windows-Windows Defender%4Operational.evtx"
    if os.path.exists(log_path) is False:
        baseLogger.info("DefenderIsLimit No File")
        return False
    # time.sleep(20)
    with evtx.Evtx(log_path) as log:
        for record in log.records():
            # print(record.xml())
            xml_doc = minidom.parseString(record.xml())
            data = xml_doc.getElementsByTagName('Data')
            for d in data:
                if len(d.childNodes) > 0:
                    value = html.unescape(d.childNodes[0].data)
                    if value.find(pack_name) > 0:
                        return True

    return False


def DownloadFile(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)

        return True
    else:
        return False


def UpdateDefender():
    cmd = f'"C:\\Program Files\\Windows Defender\\MpCmdRun.exe" -SignatureUpdate'
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        log = f"命令执行失败：{e}"
        baseLogger.info(log)


def mouse_click_ext(cx, cy, double_click=False):
    time.sleep(0.5)
    win32api.SetCursorPos((cx, cy))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, cx, cy, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, cx, cy, 0, 0)
    if double_click:
        time.sleep(0.5)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, cx, cy, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, cx, cy, 0, 0)


# print(get_file_sign("C:\\Program Files (x86)\\bepicjsq\\resources\\leishenSdk\\FixNetPP.sys"))
# print(get_file_sign("E:\\python\\sem_check\\dist\\222.exe"))

def CloseFirewallTips():
    hwnd = win32gui.FindWindow(None, 'Windows 安全中心警报')
    if hwnd:
        print("find window!")
        win32api.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    else:
        print("no find window!")


def list_process_windows(process_id):
    def callback(hwnd, wnd_list):
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if win32gui.IsWindowVisible(hwnd) and pid == process_id:
            data = {"wnd": hwnd, "wnd_title": win32gui.GetWindowText(hwnd), "wnd_class": win32gui.GetClassName(hwnd)}
            wnd_list.append(data)

    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows


def Is360Limit(limit_pic_path):
    hwnd = is360_wnd()
    if hwnd and win32gui.IsWindowVisible(hwnd):
        rect = win32gui.GetWindowRect(hwnd)
        if rect:
            ScreenShot(limit_pic_path)
            x = rect[2] - 20
            y = rect[1] + 15
            time.sleep(1)
            pyautogui.click(x, y)
            return True
        else:
            return False
    return False


def IsHuorongLimit(limit_pic_path):
    pid_list = get_proc_base_pid("HipsTray.exe")
    if len(pid_list) > 0:
        wnd_list = list_process_windows(pid_list[0]["pid"])
        for wnd_info in wnd_list:
            wnd_class = wnd_info["wnd_class"]
            hwnd = wnd_info["wnd"]
            if wnd_class.find("ATL:") >= 0 and win32gui.IsWindowVisible(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                if rect:
                    ScreenShot(limit_pic_path)
                    x = rect[2] - 45
                    y = rect[1] + 30
                    time.sleep(1)
                    pyautogui.click(x, y)
                    return True
                else:
                    return False

        return False
    else:
        baseLogger.info("no find huorong wnd!!")
        return False


# upload_url = 'https://static.leigod.com' + upload_url

def Test():
    while True:
        if IsHuorongLimit("123"):
            return
        time.sleep(1)
