#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-6-28'
"""
import json
from basic.BasicCommon import *
from basic.BasicSimuCmd import BasicCmd, BaseWifiSim
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')
coding = sys.getfilesystemencoding()
# region const variates
rout_addr = ('192.168.10.1', 65381)


class AirCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180628"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "Air"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version)
        self.sim_obj = eval(self.device_type)(logger, mac=self.mac, addr=rout_addr)
        self.do_start()
        self.onoff_kv = {"0": "off", "1": "on"}
        self.mode_kv = {"0": "auto", "1": "cold", "2": "heat", "3": "dehumidity", "4": "wind"}
        self.speed_kv = {"0": "low", "1": "overlow", "2": "normal", "3": "overnormal", "4": "high", "5": "auto"}

    def help_switch(self):
        self.cprint.notice_p("switch %s:switch %s" % (self.device_type, self.onoff_kv))

    def do_switch(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switchStatus", self.onoff_kv[args[0]])

    def help_mode(self):
        self.cprint.notice_p("set %s mode:mode %s" % (self.device_type, self.mode_kv))

    def do_mode(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.mode_kv):
            self.help_mode()
        else:
            self.sim_obj.set_item("_mode", self.mode_kv[args[0]])

    def help_speed(self):
        self.cprint.notice_p('set %s speed:speed %s' % (self.device_type, self.speed_kv))

    def do_speed(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.speed_kv):
            self.help_speed()
        else:
            self.sim_obj.set_item("_speed", self.speed_kv[args[0]])

    def help_wind_ud(self):
        self.cprint.notice_p("set %s wind_up_down:wind_ud %s" % (self.device_type, self.onoff_kv))

    def do_wind_ud(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_wind_ud()
        else:
            self.sim_obj.set_item("_wind_up_down", self.onoff_kv[args[0]])

    def help_wind_lr(self):
        self.cprint.notice_p("set %s wind_left_right:wind_lr %s" % (self.device_type, self.onoff_kv))

    def do_wind_lr(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_wind_ud()
        else:
            self.sim_obj.set_item("_wind_left_right", self.onoff_kv[args[0]])

    def help_tp(self):
        self.cprint.notice_p("set %s temperature:tp [160,300]" % (self.device_type,))

    def do_tp(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) < 160 or int(args[0]) > 300):
            self.help_tp()
        else:
            self.sim_obj.set_item("_temperature", int(args[0]))


class Air(BaseWifiSim):
    def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
        super(Air, self).__init__(logger, addr=addr, mac=mac, time_delay=time_delay
                                  , self_addr=self_addr, deviceCategory='airconditioner.new')
        # self.LOG = logger
        # self.sdk_obj = Wifi(logger=logger, time_delay=time_delay
        # , mac=mac, deviceCategory='airconditioner.new', self_addr=self_addr)
        # self.sdk_obj.sim_obj = self

        # state data:
        # self._switchStatus = 'off'
        # self._temperature = 16
        # self._mode = "cold"
        # self._speed = "low"
        # self._wind_up_down = 'off'
        # self._wind_left_right = 'off'
        # add by zx 20180524
        self.attr_dict = {
            "switchStatus": 'off',
            "temperature": 16,
            "mode": 'cold',
            "speed": 'low',
            "wind_up_down": 'off',
            "wind_left_right": 'off',
            "env_temperature": 205
        }
        self.initAttrAndDict(initDict=False)

    def get_event_report(self):
        self.LOG.warn("get_event_report".encode(coding))
        report_msg = {
            "method": "report",
            # "attribute": {
            # "switchStatus": self._switchStatus,
            # "temperature": self._temperature,
            # "mode": self._mode,
            # "speed": self._speed,
            # "wind_up_down": self._wind_up_down,
            # "wind_left_right": self._wind_left_right
            # }
            "attribute": self.initAttrAndDict(initAttr=False)
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"airconditioner.new.all_properties":
                self.LOG.warn("获取所有属性new".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    # "attribute": {
                    # "switchStatus": self._switchStatus,
                    # "temperature": self._temperature,
                    # "mode": self._mode,
                    # "speed": self._speed,
                    # "wind_up_down": self._wind_up_down,
                    # "wind_left_right": self._wind_left_right
                    # }
                    "attribute": self.initAttrAndDict(initAttr=False)
                }
                return json.dumps(rsp_msg)
            if msg['nodeid'] == u"airconditioner.main.all_properties":
                self.LOG.warn("获取所有属性main".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    # "attribute": {
                    # "switchStatus": self._switchStatus,
                    # "temperature": self._temperature,
                    # "mode": self._mode,
                    # "speed": self._speed,
                    # "wind_up_down": self._wind_up_down,
                    # "wind_left_right": self._wind_left_right
                    # }
                    "attribute": self.initAttrAndDict(initAttr=False)
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('Unknow msg!')

        elif msg['method'] == 'dm_set':

            if msg['nodeid'] == u"condition.main.switch":
                self.LOG.warn(
                    ("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
                self.set_item('_switchStatus',
                              msg['params']["attribute"]["switch"])
                return self.dm_set_rsp(msg['req_id'])
            elif msg['nodeid'] == u"airconditioner.main.switch":
                self.LOG.warn(
                    ("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
                self.set_item('_switchStatus',
                              msg['params']["attribute"]["switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"airconditioner.main.mode":
                self.LOG.warn(
                    ("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
                self.set_item('_mode', msg['params']["attribute"]["mode"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"airconditioner.main.temperature":
                self.LOG.warn(
                    ("设置温度: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
                self.set_item('_temperature',
                              msg['params']["attribute"]["temperature"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"airconditioner.main.speed":
                self.LOG.warn(
                    ("设置风速: %s" % (msg['params']["attribute"]["speed"])).encode(coding))
                self.set_item('_speed', msg['params']["attribute"]["speed"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"airconditioner.main.wind_up_down":
                self.LOG.warn(
                    ("设置上下摆风: %s" % (msg['params']["attribute"]["wind_up_down"])).encode(coding))
                self.set_item('_wind_up_down',
                              msg['params']["attribute"]["wind_up_down"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"airconditioner.main.wind_left_right":
                self.LOG.warn(
                    ("设置左右摆风: %s" % (msg['params']["attribute"]["wind_left_right"])).encode(coding))
                self.set_item('_wind_left_right',
                              msg['params']["attribute"]["wind_left_right"])
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
    airCmd = AirCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()
