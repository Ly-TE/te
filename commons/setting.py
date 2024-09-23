import os
import sys

DIR_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(DIR_PATH)

FILE_PATH = {
    "log": os.path.join(DIR_PATH, 'logs')
}
is_qiwei_msg = False
