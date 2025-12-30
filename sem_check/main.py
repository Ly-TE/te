# -*- coding: utf-8 -*-
# import sem_check
import argparse
import time

from sem_check_handle import *
import utils


class LeigodPackCheck(object):
    def __init__(self, op_type):
        self.pack_list_ = []
        self.pass_file_list_ = []
        self.query_url_ = ''
        self.report_url_ = ''
        self.time_sleep_ = 3600
        self.op_type_ = op_type
        self.pack_download_path_ = ''
        self.security_type_ = 0

    def InitModule(self):
        current_dir = os.getcwd()
        self.pack_download_path_ = current_dir + '\\download'
        if os.path.exists(self.pack_download_path_) is False:
            os.makedirs(self.pack_download_path_)

        con = configparser.ConfigParser()
        con.read("config.ini", 'utf8')
        base_url = con.get('config', 'base_url')
        self.time_sleep_ = int(con.get('config', 'time_sleep'))
        temp = con.get('config', 'pass_file_list')
        self.pass_file_list_ = temp.split(',')
        self.report_url_ = base_url + 'tools/install/package/result/report'
        self.query_url_ = base_url + 'tools/install/package/list'
        self.security_type_ = int(con.get('config', 'security_type'))

    def QueryPackList(self):
        self.pack_list_ = []
        report_data = {"is_immediately_test": self.op_type_}
        send_data = json.dumps(report_data)
        headers = {
            'Content-Type': 'application/json'
        }

        rsp = requests.post(self.query_url_, data=send_data, headers=headers)

        baseLogger.info(msg=("QueryPackList result: ", rsp.content))
        result_data = json.loads(rsp.content)
        code = result_data["code"]
        if code != 0:
            baseLogger.info(msg=("QueryPackList error: ", result_data))
            return ERROR_CODE_DATA_ERROR
        base_url = result_data["data"]["base_download_url"]
        pack_list = result_data["data"]["package_list"]
        for pack_info in pack_list:
            temp_info = {"url": base_url + pack_info["package_url"], "id": pack_info["id"],
                         "batch_no": pack_info["batch_no"], "package_type": pack_info["package_type"]}
            self.pack_list_.append(temp_info)
        # print(self.pack_list_)
        return ERROR_CODE_SUCCESS

    def Work(self):
        while True:
            result = self.QueryPackList()
            if result != ERROR_CODE_SUCCESS:
                break
            if len(self.pack_list_) > 0:
                utils.UpdateDefender()

            for pack_data in self.pack_list_:
                package_type = pack_data['package_type']
                pack_id = pack_data["id"]
                # if pack_id != 20 and pack_id != 21 and pack_id != 22 and pack_id != 23 and pack_id != 24 and pack_id != 25:
                #    continue
                check_handle = None
                utils.CloseFirewallTips()
                if package_type == PACK_TYPE_OFFICIAL:
                    check_handle = OfficialPackCheck(pack_data, self.pack_download_path_, self.report_url_,
                                                     self.pass_file_list_, self.security_type_)
                elif package_type == PACK_TYPE_SEM:
                    check_handle = SemPackCheck(pack_data, self.pack_download_path_, self.report_url_,
                                                self.pass_file_list_, self.security_type_)
                elif package_type == PACK_TYPE_ZIP:
                    check_handle = ZipPackCheck(pack_data, self.pack_download_path_, self.report_url_,
                                                self.pass_file_list_, self.security_type_)

                if check_handle is None:
                    continue

                check_handle.CleanDownloadCache()
                result, need_check_defender = check_handle.DownloadPack()
                next_step = check_handle.ReportDownloadPackResult(result)
                if next_step is False and need_check_defender is False:
                    check_handle.CleanPackCache()
                    continue
                next_step = check_handle.DefenderLimitCheck()
                if next_step is False:
                    check_handle.CleanPackCache()
                    continue

                next_step = check_handle.PackSignCheck()
                if next_step is False:
                    check_handle.CleanPackCache()
                    continue

                result = check_handle.MonitorPackInstall()
                next_step = check_handle.ReportMonitorResult(result)
                if next_step:
                    time.sleep(10)
                    check_handle.VerifyFileSign()

                check_handle.CleanPackCache()
                check_handle.RefreshTray()

            # 清理安全中心拦截日志
            if len(self.pack_list_) > 0:
                utils.CleanDefenderEventLog()
            baseLogger.info("wait next work!!!!")
            time.sleep(self.time_sleep_)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--op', type=int, default=0, help='0 自动列表 1即时列表')
    arg = parser.parse_args()

    handler = LeigodPackCheck(arg.op)
    handler.InitModule()
    handler.Work()
    # utils.CleanDefenderEventLog()
    # result = utils.DefenderIsLimit('leigod_by96.exe')
    # print(result)
    # time.sleep(60)
    # handler.QueryPackList()
    # handler.UpdateDefender()
    # handler.CleanDefenderEventLog()
    # print("111")
