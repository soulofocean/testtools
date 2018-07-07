#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-6'
"""
import json
from basic.BasicCommon import *
from basic.BasicSimuCmd import BasicCmd, BaseWifiSim

# region const variates
rout_addr = ('192.168.10.1', 65381)

class TVCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180706"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "TV"
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
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) > 2):
            self.help_rsf()
        else:
            if (int(args[0]) == 0):
                self.sim_obj.reset_filter_time(1)
                self.sim_obj.reset_filter_time(2)
            else:
                self.sim_obj.reset_filter_time(int(args[0]))


class TV(BaseWifiSim):
    def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
        super(TV, self).__init__(logger, addr=addr, mac=mac, time_delay=time_delay, self_addr=self_addr,
                                 deviceCategory='tv.main')
        # self.LOG = logger
        # self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='water_filter.main', self_addr=self_addr)
        # self.sdk_obj.sim_obj = self

        # state data:
        self._switch = 'off'
        self._change = "off"
        self._voice_offset = 27


    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "switch": self._switch,
                "change": self._change
                # "_voice_offset": self._voice_offset,
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"tv.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "switch": self._switch,
                        "change": self._change
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('Unknow msg!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"tv.main.switch":
                self.LOG.warn(
                    ("设置开关/切换: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
                self.set_item('_switch', msg['params']["attribute"]["switch"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"tv.main.change":
                self.LOG.warn(
                    ("对讲控制: %s" % (msg['params']["attribute"]["change"])).encode(coding))
                self.set_item('_switch', msg['params']["attribute"]["change"])
                return self.dm_set_rsp(msg['req_id'])

            elif msg['nodeid'] == u"tv.main.set":
                self.LOG.warn(
                    ("音量调整: %s" % (msg['params']["attribute"]["voice"])).encode(coding))
                vof = int((msg['params']["attribute"]["voice"]).encode(coding))
                tmpof = self.get_item("_voice_offset")
                if(msg['params']["attribute"]["voice"] == u"increase"):
                    self.set_item("_voice_offset", min(255, tmpof + vof))
                elif (msg['params']["attribute"]["voice"] == u"decrease"):
                    self.set_item("_voice_offset", max(0, tmpof - vof))
                elif (msg['params']["attribute"]["voice"] == u"mute"):
                    self.set_item("_voice_offset", 0)
                else:
                    self.LOG.error(
                        ("unkown voice: %s" % (msg['params']["attribute"]["voice"])).encode(coding))
                self.set_item('_switch', msg['params']["attribute"]["change"])
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
    airCmd = TVCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()