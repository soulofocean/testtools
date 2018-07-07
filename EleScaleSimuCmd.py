#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-7'
"""
import json
from basic.BasicCommon import *
from basic.BasicSimuCmd import BasicCmd, BaseWifiSim

# region const variates
rout_addr = ('192.168.10.1', 65381)

class EleScaleCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180706"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "EleScale"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version, d_type=self.device_type)
        self.sim_obj = eval(self.device_type)(logger, mac=self.mac, addr=rout_addr)
        self.do_start()
        self.onoff_kv = {"0": "off", "1": "on"}
        self.unit_kv = {"0":"kg", "1":"jin", "2":"pound"}
        self.unitv_kv = {"kg":100.0, "jin":50.0, "pound":45.36}

    def help_sw(self):
        self.cprint.notice_p("set the weight:sw [0-600]")

    def do_sw(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) < 0 or int(args[0]) > 600):
            self.help_sw()
        self.sim_obj.set_item('_weight', round(float(args[0]),1))

    def help_su(self):
        self.cprint.notice_p("set weight unit %s: su " % (self.unit_kv, ))

    def do_su(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.unit_kv):
            self.help_su()
        else:
            old_unit = self.sim_obj.get_item("_unit")
            new_w =round(self.sim_obj.get_item("_weight") *
                         self.unitv_kv[old_unit]
                         / self.unitv_kv[self.unit_kv[args[0]]],1)
            self.sim_obj.set_item("_unit", self.unit_kv[args[0]])
            self.sim_obj.set_item('_weight', float(new_w))


class EleScale(BaseWifiSim):
    def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
        super(EleScale, self).__init__(logger, addr=addr, mac=mac, time_delay=time_delay, self_addr=self_addr,
                                       deviceCategory='electronicscale.main')
        # self.LOG = logger
        # self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='water_filter.main', self_addr=self_addr)
        # self.sdk_obj.sim_obj = self

        # state data:
        self._weight = 0
        self._unit = "kg"


    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "weight": self._weight,
                "unit": self._unit
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"electronicscale.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "weight": self._weight,
                        "unit": self._unit
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('Unknow msg!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"electronicscale.main.weight":
                self.LOG.warn(
                    ("设置开关/切换: %s" % (msg['params']["attribute"]["weight"])).encode(coding))
                self.set_item('_switch', msg['params']["attribute"]["weight"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"electronicscale.main.unit":
                self.LOG.warn(
                    ("对讲控制: %s" % (msg['params']["attribute"]["unit"])).encode(coding))
                self.set_item('_switch', msg['params']["attribute"]["unit"])
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
    eleSalCmd = EleScaleCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (eleSalCmd.mac,))
    eleSalCmd.cmdloop()