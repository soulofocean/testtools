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
from protocol.wifi_devices import Air
from basic.cprint import cprint
from basic.log_tool import MyLogger
from basic.BasicSimuCmd import BasicCmd

# region const variates
onoff_kv = {"0": "off", "1": "on"}
mode_kv = {"0": "auto", "1": "cold", "2": "heat", "3": "dehumidity", "4": "wind"}
speed_kv = {"0": "low", "1": "overlow", "2": "normal", "3": "overnormal", "4": "high", "5": "auto"}
air_version = "20180628"
rout_addr = ('192.168.10.1', 65381)
mac=str(hex(int(time.time())))[-8:]
device_type = "Air"

class AirCmd(BasicCmd):
    def __init__(self, logger, cprint):
        BasicCmd.__init__(self,logger=logger ,cprint=cprint,version=air_version
                          ,addr=rout_addr, mac=mac,d_type=device_type)

    def help_switch(self):
        self.cprint.notice_p("switch air:switch %s" % (onoff_kv,))
    def do_switch(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switchStatus", onoff_kv[args[0]])

    def help_mode(self):
        self.cprint.notice_p("set air mode:mode %s" % (mode_kv,))
    def do_mode(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in mode_kv):
            self.help_mode()
        else:
            self.sim_obj.set_item("_mode", mode_kv[args[0]])

    def help_speed(self):
        self.cprint.notice_p('set air mode:mode %s' % (speed_kv,))
    def do_speed(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in speed_kv):
            self.help_speed()
        else:
            self.sim_obj.set_item("_speed", speed_kv[args[0]])

    def help_wind_ud(self):
        self.cprint.notice_p("set air wind_up_down:wind_ud %s" % (onoff_kv,))
    def do_wind_ud(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in onoff_kv):
            self.help_wind_ud()
        else:
            self.sim_obj.set_item("_wind_up_down", onoff_kv[args[0]])

    def help_wind_lr(self):
        self.cprint.notice_p("set air wind_left_right:wind_lr %s" % (onoff_kv,))
    def do_wind_lr(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in onoff_kv):
            self.help_wind_ud()
        else:
            self.sim_obj.set_item("_wind_left_right", onoff_kv[args[0]])

    def help_tp(self):
        self.cprint.notice_p("set air temperature:tp [160,300]")
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
    sim = Air(LOG,mac=mac,addr=rout_addr)
    airCmd = AirCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (mac,))
    airCmd.cmdloop()