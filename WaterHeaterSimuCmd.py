#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-4'
"""
import json
from basic.BasicCommon import *
from basic.BasicSimuCmd import BasicCmd, BaseWifiSim

# region const variates
rout_addr = ('192.168.10.1', 65381)

class WaterHeaterCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180703"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "WaterHeater"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version, d_type=self.device_type)
        self.sim_obj = eval(self.device_type)(logger, mac=self.mac, addr=rout_addr)
        self.do_start()
        self.onoff_kv = {"0": "off", "1": "on"}

    def help_clean(self):
        self.cprint.notice_p("clean the waterfilter:clean")

    def do_clean(self, arg):
        self.sim_obj.set_item('_status', 'clean')
        self.sim_obj.task_obj.add_task(
            'change WaterFilter to filter', self.sim_obj.set_item, 1, 100, '_status', 'standby')

    def help_rsf(self):
        self.cprint.notice_p("reset filter : rsf [id[1-2]] 0 for all")

    def do_rsf(self, arg):
        args = arg.split()
        if (len(args)!=1 or not args[0].isdigit() or int(args[0]) > 2):
            self.help_rsf()
        else:
            if(int(args[0])==0):
                self.sim_obj.reset_filter_time(1)
                self.sim_obj.reset_filter_time(2)
            else:
                self.sim_obj.reset_filter_time(int(args[0]))

class WaterHeater(BaseWifiSim):
    def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
        super(WaterHeater, self).__init__(logger, addr=addr, mac=mac, time_delay=time_delay, self_addr=self_addr,
                                          deviceCategory='water_heater.main.')
        # self.LOG = logger
        # self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='oven.main', self_addr=self_addr)
        # self.sdk_obj.sim_obj = self

        # state data:
        self._switch = 'off'
        self._remaining = 30
        self._control = 'stop'
        self._mode = 'tub'
        self._bath_fill = 990
        self._temperature = 35
        self._reserve = 1440

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "switch": self._switch,
                "remaining": self._remaining,
                "control": self._control,
                "mode": self._mode,
                "bath_fill": self._bath_fill,
                "temperature": self._temperature,
                "reserve": self._reserve
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"water_heater.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "switch": self._switch,
                        "remaining": self._remaining,
                        "control": self._control,
                        "mode": self._mode,
                        "bath_fill": self._bath_fill,
                        "temperature": self._temperature,
                        "reserve": self._reserve
                    }
                }
                return json.dumps(rsp_msg)

            else:
                self.LOG.warn('Unknow msg!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"water_heater.main.switch":
                self.LOG.warn(
                    ("开/关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
                self.set_item(
                    '_switch', msg['params']["attribute"]["switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"water_heater.main.control":
                self.LOG.warn(
                    ("启动暂停: %s" % (msg['params']["attribute"]["control"])).encode(coding))
                self.set_item(
                    '_control', msg['params']["attribute"]["control"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"water_heater.main.mode":
                self.LOG.warn(
                    ("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
                self.set_item(
                    '_mode', msg['params']["attribute"]["mode"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"water_heater.main.bath_fill":
                self.LOG.warn(
                    ("设置定时: %s" % (msg['params']["attribute"]["bath_fill"])).encode(coding))
                self.set_item(
                    '_bath_fill', msg['params']["attribute"]["bath_fill"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"water_heater.main.temperature":
                self.LOG.warn(
                    ("设置热风对流: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
                self.set_item(
                    '_temperature', msg['params']["attribute"]["temperature"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"water_heater.main.reserve":
                self.LOG.warn(
                    ("设置转叉: %s" % (msg['params']["attribute"]["reserve"])).encode(coding))
                self.set_item(
                    '_reserve', msg['params']["attribute"]["reserve"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wifi.main.alarm_confirm":
                return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

            else:
                self.LOG.warn('Unknow msg %s!' % (msg['nodeid'],))

        else:
            self.LOG.error('Msg wrong!')

if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = WaterHeaterCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()