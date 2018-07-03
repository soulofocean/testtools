#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-6-28'
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
class AirCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180628"
        self.mac=str(hex(int(time.time())))[-8:]
        self.device_type = "Air"
        BasicCmd.__init__(self,logger=logger ,cprint=cprint,version=self.air_version
                          ,addr=rout_addr, mac=self.mac,d_type=self.device_type)
        self.onoff_kv = {"0": "off", "1": "on"}
        self.mode_kv = {"0": "auto", "1": "cold", "2": "heat", "3": "dehumidity", "4": "wind"}
        self.speed_kv = {"0": "low", "1": "overlow", "2": "normal", "3": "overnormal", "4": "high", "5": "auto"}

    def help_switch(self):
        self.cprint.notice_p("switch %s:switch %s" % (self.device_type, self.onoff_kv))
    def do_switch(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switchStatus", self.onoff_kv[args[0]])

    def help_mode(self):
        self.cprint.notice_p("set %s mode:mode %s" % (self.device_type, self.mode_kv))
    def do_mode(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.mode_kv):
            self.help_mode()
        else:
            self.sim_obj.set_item("_mode", self.mode_kv[args[0]])

    def help_speed(self):
        self.cprint.notice_p('set %s speed:speed %s' % (self.device_type, self.speed_kv))
    def do_speed(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.speed_kv):
            self.help_speed()
        else:
            self.sim_obj.set_item("_speed", self.speed_kv[args[0]])

    def help_wind_ud(self):
        self.cprint.notice_p("set %s wind_up_down:wind_ud %s" % (self.device_type, self.onoff_kv))
    def do_wind_ud(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_wind_ud()
        else:
            self.sim_obj.set_item("_wind_up_down", self.onoff_kv[args[0]])

    def help_wind_lr(self):
        self.cprint.notice_p("set %s wind_left_right:wind_lr %s" % (self.device_type, self.onoff_kv))
    def do_wind_lr(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_wind_ud()
        else:
            self.sim_obj.set_item("_wind_left_right", self.onoff_kv[args[0]])

    def help_tp(self):
        self.cprint.notice_p("set %s temperature:tp [160,300]" % (self.device_type,))
    def do_tp(self, arg):
        args = arg.split()
        if(len(args)!=1 or not args[0].isdigit() or int(args[0]) < 160 or int(args[0]) > 300):
            self.help_tp()
        else:
            self.sim_obj.set_item("_temperature", int(args[0]))

if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = AirCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()