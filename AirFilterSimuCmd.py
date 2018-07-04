#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-3'
"""
import sys
import os
import logging
import time
from basic.cprint import cprint
from basic.log_tool import MyLogger
from basic.BasicSimuCmd import BasicCmd

# region const variates
rout_addr = ('192.168.10.1', 65381)

class AirFilterCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180703"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "AirFilter"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version
                          , addr=rout_addr, mac=self.mac, d_type=self.device_type)
        self.onoff_kv = {"0": "off", "1": "on"}
        self.ctl_kv = {"0": "auto", "1": "manual", "2": "sleep"}
        self.speed_kv = {"0": "low", "1": "middle", "2": "high", "3": "very_high", "4": "super_high", "5": "sleep"}

    def help_switch(self):
        self.cprint.notice_p("switch %s:switch %s" % (self.device_type, self.onoff_kv))
    def do_switch(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switch_status", self.onoff_kv[args[0]])

    def help_cls(self):
        self.cprint.notice_p("switch %s child_lock_switch_status :cls %s" % (self.device_type, self.onoff_kv))
    def do_cls(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_cls()
        else:
            self.sim_obj.set_item("_child_lock_switch_status", self.onoff_kv[args[0]])

    def help_nis(self):
        self.cprint.notice_p("switch %s negative_ion_switch_status:nis %s" % (self.device_type, self.onoff_kv))
    def do_nis(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_nis()
        else:
            self.sim_obj.set_item("_negative_ion_switch_status", self.onoff_kv[args[0]])

    def help_ctl(self):
        self.cprint.notice_p("set %s control:ctl %s" % (self.device_type, self.ctl_kv))
    def do_ctl(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.ctl_kv):
            self.help_ctl()
        else:
            self.sim_obj.set_item("_control_status", self.ctl_kv[args[0]])

    def help_speed(self):
        self.cprint.notice_p('set %s speed:speed %s' % (self.device_type, self.speed_kv))
    def do_speed(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.speed_kv):
            self.help_speed()
        else:
            self.sim_obj.set_item("_speed", self.speed_kv[args[0]])

if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = AirFilterCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()