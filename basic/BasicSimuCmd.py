#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-6-29'
"""
import copy
from abc import ABCMeta
from BasicProtocol import *
from cmd import Cmd
from BasicCommon import *

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')
coding = sys.getfilesystemencoding()


class BasicCmd(Cmd):
    def __init__(self, logger, cprint, version="20180628", d_type="Air"):
        Cmd.__init__(self)
        self.log_kv = [("0", "logging.CRITICAL"), ("1", "logging.ERROR"),
                       ("2", "logging.WARNING"), ("3", "logging.INFO"), ("4", "logging.DEBUG")]
        self.Log = logger
        self.cprint = cprint
        self.sim_obj = None
        # self.sim_obj = eval(d_type)(logger,mac=mac,addr=addr)
        self.prompt = "%s>>" % (d_type,)
        self.intro = "Welcome from %sCmd (Version:%s)!" % (d_type, version,)
        # self.do_log("3")
        # self.do_start()

    def emptyline(self):
        pass

    def help_set(self):
        self.cprint.notice_p("set state: set [key] [value]")

    def do_set(self, arg, opts=None):
        args = arg.split()
        self.sim_obj.set_item(args[0], args[1])

    def help_start(self):
        self.cprint.common_p("start simulator runforever")

    def help_exit(self):
        self.cprint.common_p("exit console")

    def do_start(self, arg=None):
        if self.sim_obj:
            self.sim_obj.run_forever()

    def do_exit(self, arg=None):
        self.cprint.common_p("Exit simulator, good bye!")
        sys.exit(0)

    def help_log(self):
        self.cprint.notice_p(
            "change logger level: log %s" % (self.log_kv,))

    def do_log(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) > (len(self.log_kv) - 1)):
            self.cprint.warn_p("unknow log level: %s!" % (arg))
            self.help_log()
        else:
            self.Log.set_level(eval(self.log_kv[int(args[0])][1]))

    def help_show(self):
        self.cprint.notice_p("show simulator state")

    def do_show(self, arg=None):
        if not self.sim_obj == None:
            self.sim_obj.status_show()
        else:
            self.cprint.warn_p("Simulator is not started ...")

    def help_alarm(self):
        self.cprint.notice_p("send alarm:")
        self.cprint.notice_p("alarm error_code error_status error_level error_msg")

    def do_alarm(self, arg, opts=None):
        args = arg.split()
        if len(args) >= 2:
            if len(args) == 3:
                args.append('Test alarm')
            else:
                args.append(1)
                args.append('Test alarm')
            self.sim_obj.add_alarm(error_code=args[0], error_status=args[1], error_level=int(
                args[2]), error_msg=args[3])
        else:
            self.help_alarm()


alarm_lock = threading.Lock()


class BaseWifiSim():
    __metaclass__ = ABCMeta
    status_lock = threading.Lock()

    def __init__(self, logger, addr=('192.168.10.1', 65381), mac='123456', time_delay=500
                 , self_addr=None, deviceCategory='airconditioner.new'):
        self.LOG = logger
        self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,
                            mac=mac, deviceCategory=deviceCategory, self_addr=self_addr, addr=addr)
        self.sdk_obj.sim_obj = self
        self.need_stop = False

        # state data:
        self.task_obj = Task('Washer-task', self.LOG)
        self.create_tasks()
        self.alarm_dict = defaultdict(dict)
        self.attr_dict = defaultdict(dict)  # add by zx 20180524

    @need_add_lock(status_lock)
    def set_item(self, item, value):
        if item in self.__dict__:
            self.__dict__[item] = value
        else:
            self.LOG.error("Unknow item: %s" % (item))

    # add by zx 20180524
    @need_add_lock(status_lock)
    def get_item(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            self.LOG.error("get_item Unknown item: %s" % (item))

    @need_add_lock(status_lock)
    def add_item(self, item, value):
        try:
            setattr(self, item, value)
        except:
            self.LOG.error("add item fail: %s" % (item))

    def status_show(self):
        for item in sorted(self.__dict__):
            if item.startswith('_'):
                self.LOG.warn("%s: %s" % (item, str(self.__dict__[item])))

    def send_msg(self, msg):
        return self.sdk_obj.add_send_data(self.sdk_obj.msg_build(msg))

    @abstractmethod
    def protocol_handler(self, msg):
        pass

    def stop(self):
        self.need_stop = True
        self.sdk_obj.stop()
        if self.task_obj:
            self.task_obj.stop()
        self.LOG.warn('Thread %s stoped!' % (__name__))

    def run_forever(self):
        thread_list = []
        thread_list.append([self.sdk_obj.schedule_loop])
        thread_list.append([self.sdk_obj.send_data_loop])
        thread_list.append([self.sdk_obj.recv_data_loop])
        thread_list.append([self.sdk_obj.heartbeat_loop, False])
        thread_list.append([self.task_obj.task_proc])
        thread_list.append([self.alarm_proc])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 100)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def status_maintain(self):
        pass

    def status_report_monitor(self):
        need_send_report = False
        if not hasattr(self, 'old_status'):
            self.old_status = defaultdict(lambda: {})
            for item in self.__dict__:
                if item.startswith('_'):
                    self.LOG.yinfo("need check item: %s" % (item))
                    self.old_status[item] = copy.deepcopy(self.__dict__[item])

        for item in self.old_status:
            if self.old_status[item] != self.__dict__[item]:
                need_send_report = True
                self.old_status[item] = copy.deepcopy(self.__dict__[item])

        if need_send_report:
            self.send_msg(self.get_event_report())

    def alarm_proc(self):
        while self.need_stop == False:
            alarm_lock.acquire()
            for alarm in self.alarm_dict:
                if self.alarm_dict[alarm]['status'] == 'ready':
                    self.alarm_dict[alarm]['status'] = "over"
                    self.send_msg(self.alarm_report(self.alarm_dict[alarm]['error_code'], self.alarm_dict[alarm]
                    ['error_status'], self.alarm_dict[alarm]['error_level'], self.alarm_dict[alarm]['error_msg']))

                elif self.alarm_dict[alarm]['status'] == 'over':
                    pass

            alarm_lock.release()
            time.sleep(3)

    def alarm_report(self, error_code, error_status, error_level=1, error_msg="test alarm"):
        report_msg = {
            "method": "alarm",
            "attribute": {
                "error_code": error_code,
                "error_msg": error_msg,
                "error_level": error_level,
                "error_status": error_status,
            }
        }
        return json.dumps(report_msg)

    @need_add_lock(alarm_lock)
    def add_alarm(self, error_code, error_status, error_level=1, error_msg="test alarm"):
        if error_code in self.alarm_dict and self.alarm_dict[error_code]['status'] != 'over':
            pass
        else:
            self.alarm_dict[error_code]['error_code'] = error_code
            self.alarm_dict[error_code]['error_status'] = error_status
            self.alarm_dict[error_code]['error_level'] = error_level
            self.alarm_dict[error_code]['error_msg'] = error_msg
            self.alarm_dict[error_code]['status'] = 'ready'

    @need_add_lock(alarm_lock)
    def set_alarm(self, error_code, status):
        if error_code in self.alarm_dict:
            self.alarm_dict[error_code]['status'] = status
        else:
            self.LOG.error('error code not exist!')

    def alarm_confirm_rsp(self, req, error_code):
        self.LOG.warn(("故障(解除)上报确认:").encode(coding))
        self.set_alarm(error_code, 'over')
        rsp_msg = {
            "method": "dm_set",
            "req_id": req,
            "msg": "success",
            "code": 0,
            "attribute": {
                "error_code": error_code,
                "error_status": self.alarm_dict[error_code]["error_status"]
            }
        }
        return json.dumps(rsp_msg)

    def dm_set_rsp(self, req):
        rsp_msg = {
            "method": "dm_set",
            "req_id": req,
            "msg": "success",
            "code": 0
        }
        return json.dumps(rsp_msg)

    # add by zx-20180524
    def initAttrAndDict(self, initAttr=True, initDict=True):
        dictTmp = defaultdict(dict)
        sourceDict = self.attr_dict
        if sourceDict:
            for key, value in sourceDict.items():
                item_name = "_" + key
                if (initAttr):
                    self.add_item(item_name, value)
                # setattr(self, "_" + key, value)
                if (initDict):
                    dictTmp[key] = self.get_item(item_name)
        return dictTmp


if __name__ == '__main__':
    pass
