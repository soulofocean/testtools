#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-4'
"""
import sys
import threading
import json
from wifi_devices import BaseSim

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

coding = sys.getfilesystemencoding()

alarm_lock = threading.Lock()


class WaterHeater(BaseSim):
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
    pass