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


class WasherCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180704"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "Washer"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version, d_type=self.device_type)
        self.sim_obj = eval(self.device_type)(logger, mac=self.mac, addr=rout_addr)
        self.do_start()
        self.onoff_kv = {"0": "off", "1": "on"}

    def help_switch(self):
        self.cprint.notice_p("switch %s:switch %s" % (self.device_type, self.onoff_kv))

    def do_switch(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switch", self.onoff_kv[args[0]])

class Washer(BaseWifiSim):
    def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
        super(Washer, self).__init__(logger, addr=addr, mac=mac, time_delay=time_delay, self_addr=self_addr,
                                     deviceCategory='wash_machine.main')
        # self.LOG = logger
        # self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='wash_machine.main', self_addr=self_addr)
        # self.sdk_obj.sim_obj = self

        # state data:
        self._status = 'standby'  #
        self._auto_detergent_switch = 'off'  ##
        self._child_lock_switch_status = "off"  ##
        self._add_laundry_switch = "off"  #
        self._sterilization = "off"  #
        self._spin = 0  #
        self._temperature = 28  #
        self._reserve_wash = 24  #
        self._mode = "mix"  #
        self._time_left = 10  #
        self._drying = "no_drying"  #
        self._operation = "spin"  #
        self._drying_duration = 15  #
        self._switch = "on"  #

    def status_maintain(self):
        if self._status == 'start':
            if self._time_left > 0:
                self.set_item('_time_left',
                              self._time_left - 1)
                if self._time_left <= 0:
                    self.set_item('_status', 'halt')
            else:
                self.set_item('_status', 'halt')

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "child_lock_switch": self._child_lock_switch_status,
                "auto_detergent_switch": self._auto_detergent_switch,
                "add_laundry_switch": self._add_laundry_switch,
                "sterilization": self._sterilization,
                "spin": self._spin,
                "temperature": self._temperature,
                "reserve_wash": self._reserve_wash,
                "mode": self._mode,
                "status": self._status,
                "time_left": self._time_left,
                "drying": self._drying,
                "operation": self._operation,
                "drying_duration": self._drying_duration,
                "switch": self._switch
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"wash_machine.main.all_properties":
                self.LOG.warn("[%s]获取所有属性main".encode(coding) % self)
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "child_lock_switch": self._child_lock_switch_status,
                        "auto_detergent_switch": self._auto_detergent_switch,
                        "add_laundry_switch": self._add_laundry_switch,
                        "sterilization": self._sterilization,
                        "spin": self._spin,
                        "temperature": self._temperature,
                        "reserve_wash": self._reserve_wash,
                        "mode": self._mode,
                        "status": self._status,
                        "time_left": self._time_left,
                        "drying": self._drying,
                        "operation": self._operation,
                        "drying_duration": self._drying_duration,
                        "switch": self._switch
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('Unknow msg!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"wash_machine.main.control":
                self.LOG.warn(
                    ("启动暂停: %s" % (msg['params']["attribute"]["control"])).encode(coding))
                self.set_item('_status', msg['params']["attribute"]["control"])
                self.set_item('_time_left', 10)
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.child_lock_switch":
                self.LOG.warn(
                    ("童锁开关: %s" % (msg['params']["attribute"]["child_lock_switch"])).encode(coding))
                self.set_item('_child_lock_switch_status',
                              msg['params']["attribute"]["child_lock_switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.auto_detergent_switch":
                self.LOG.warn(
                    ("设置智能投放: %s" % (msg['params']["attribute"]["auto_detergent_switch"])).encode(coding))
                self.set_item('_auto_detergent_switch',
                              msg['params']["attribute"]["auto_detergent_switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.add_laundry_switch":
                self.LOG.warn(
                    ("设置中途添衣: %s" % (msg['params']["attribute"]["add_laundry_switch"])).encode(coding))
                self.set_item('_add_laundry_switch',
                              msg['params']["attribute"]["add_laundry_switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.sterilization":
                self.LOG.warn(
                    ("一键除菌: %s" % (msg['params']["attribute"]["sterilization"])).encode(coding))
                self.set_item('_sterilization',
                              msg['params']["attribute"]["sterilization"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.mode":
                self.LOG.warn(
                    ("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
                self.set_item('_mode', msg['params']["attribute"]["mode"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.spin":
                self.LOG.warn(
                    ("设置脱水: %s" % (msg['params']["attribute"]["spin"])).encode(coding))
                self.set_item('_spin', msg['params']["attribute"]["spin"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.temperature":
                self.LOG.warn(
                    ("设置温度: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
                self.set_item('_temperature',
                              msg['params']["attribute"]["temperature"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"wash_machine.main.reserve_wash":
                self.LOG.warn(
                    ("设置预约功能: %s" % (msg['params']["attribute"]["reserve_wash"])).encode(coding))
                self.set_item('_reserve_wash',
                              msg['params']["attribute"]["reserve_wash"])
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
    airCmd = WasherCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()
