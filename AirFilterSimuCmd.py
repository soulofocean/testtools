#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-3'
"""
import json
from basic.BasicCommon import *
from basic.BasicSimuCmd import BasicCmd, BaseWifiSim

# region const variates
rout_addr = ('192.168.10.1', 65381)


class AirFilterCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180703"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "AirFilter"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version, d_type=self.device_type)
        self.sim_obj = eval(self.device_type)(logger, mac=self.mac, addr=rout_addr)
        self.do_start()
        self.onoff_kv = {"0": "off", "1": "on"}
        self.ctl_kv = {"0": "auto", "1": "manual", "2": "sleep"}
        self.speed_kv = {"0": "low", "1": "middle", "2": "high", "3": "very_high", "4": "super_high", "5": "sleep"}

    def help_switch(self):
        self.cprint.notice_p("switch %s:switch %s" % (self.device_type, self.onoff_kv))

    def do_switch(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switch_status", self.onoff_kv[args[0]])

    def help_cls(self):
        self.cprint.notice_p("switch %s child_lock_switch_status :cls %s" % (self.device_type, self.onoff_kv))

    def do_cls(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_cls()
        else:
            self.sim_obj.set_item("_child_lock_switch_status", self.onoff_kv[args[0]])

    def help_nis(self):
        self.cprint.notice_p("switch %s negative_ion_switch_status:nis %s" % (self.device_type, self.onoff_kv))

    def do_nis(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_nis()
        else:
            self.sim_obj.set_item("_negative_ion_switch_status", self.onoff_kv[args[0]])

    def help_ctl(self):
        self.cprint.notice_p("set %s control:ctl %s" % (self.device_type, self.ctl_kv))

    def do_ctl(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.ctl_kv):
            self.help_ctl()
        else:
            self.sim_obj.set_item("_control_status", self.ctl_kv[args[0]])

    def help_speed(self):
        self.cprint.notice_p('set %s speed:speed %s' % (self.device_type, self.speed_kv))

    def do_speed(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.speed_kv):
            self.help_speed()
        else:
            self.sim_obj.set_item("_speed", self.speed_kv[args[0]])


class AirFilter(BaseWifiSim):
    def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
        super(AirFilter, self).__init__(logger, addr=addr, mac=mac, time_delay=time_delay, self_addr=self_addr,
                                        deviceCategory='air_filter.main')
        # self.LOG = logger
        # self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='air_filter.main', self_addr=self_addr)
        # self.sdk_obj.sim_obj = self

        # state data:
        self._air_filter_result = {
            "air_quality": [
                "good"
            ],
            "PM25": [
                100
            ]
        }
        self._switch_status = 'off'
        self._child_lock_switch_status = "off"
        self._negative_ion_switch_status = "off"
        self._speed = "low"
        self._control_status = 'auto'
        self._filter_time_used = '101'
        self._filter_time_remaining = '1899'
        self._temperature = "1888"
        self._humidity = "5666"
        self._replace_filter = "false"

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "air_filter_result": self._air_filter_result,
                "switch_status": self._switch_status,
                "child_lock_switch_status": self._child_lock_switch_status,
                "negative_ion_switch_status": self._negative_ion_switch_status,
                "speed": self._speed,
                "control": self._control_status,
                "filter_time_used": self._filter_time_used,
                "filter_time_remaining": self._filter_time_remaining,
                "temperature": self._temperature,
                "humidity": self._humidity,
                "replace_filter": self._replace_filter
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"air_filter.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "air_filter_result": self._air_filter_result,
                        "switch_status": self._switch_status,
                        "child_lock_switch_status": self._child_lock_switch_status,
                        "negative_ion_switch_status": self._negative_ion_switch_status,
                        "speed": self._speed,
                        "control": self._control_status,
                        "filter_time_used": self._filter_time_used,
                        "filter_time_remaining": self._filter_time_remaining,
                        "temperature": self._temperature,
                        "humidity": self._humidity,
                        "replace_filter": self._replace_filter
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('Unknow msg!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"air_filter.main.switch":
                self.LOG.warn(
                    ("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
                self.set_item('_switch_status',
                              msg['params']["attribute"]["switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"air_filter.main.child_lock_switch":
                self.LOG.warn(
                    ("童锁开关: %s" % (msg['params']["attribute"]["child_lock_switch"])).encode(coding))
                self.set_item('_child_lock_switch_status',
                              msg['params']["attribute"]["child_lock_switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"air_filter.main.negative_ion_switch":
                self.LOG.warn(
                    ("负离子开关: %s" % (msg['params']["attribute"]["negative_ion_switch"])).encode(coding))
                self.set_item('_negative_ion_switch_status',
                              msg['params']["attribute"]["negative_ion_switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"air_filter.main.control":
                self.LOG.warn(
                    ("设置模式切换: %s" % (msg['params']["attribute"]["control"])).encode(coding))
                self.set_item('_control_status',
                              msg['params']["attribute"]["control"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"air_filter.main.speed":
                self.LOG.warn(
                    ("设置风量调节: %s" % (msg['params']["attribute"]["speed"])).encode(coding))
                self.set_item('_speed', msg['params']["attribute"]["speed"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wifi.main.alarm_confirm":
                return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

            else:
                self.LOG.warn('Unknow msg!')

        else:
            self.LOG.error('Msg wrong!')


if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = AirFilterCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()
