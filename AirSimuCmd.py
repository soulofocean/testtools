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
from cmd import Cmd
from protocol.wifi_devices import Air
from basic.cprint import cprint
from basic.log_tool import MyLogger

# region const variates
log_kv = {'0': "logging.CRITICAL",'1': "logging.ERROR",'2': "logging.WARNING",'3': "logging.INFO",'4': "logging.DEBUG"}
onoff_kv = {"0": "off", "1": "on"}
mode_kv = {"0": "auto", "1": "cold", "2": "heat", "3": "dehumidity", "4": "wind"}
speed_kv = {"0": "low", "1": "overlow", "2": "normal", "3": "overnormal", "4": "high", "5": "auto"}
air_version = "20180628"
rout_addr = ('192.168.10.1', 65381)

class AirCmd(Cmd):
    def __init__(self, logger, sim, cprint):
        Cmd.__init__(self)
        self.Log = logger
        self.cprint = cprint
        self.SimObj = sim
        self.prompt = "Air>>"
        self.intro = "Welcome from AirCmd(%s)!" % (air_version,)

    def emptyline(self):
        pass

    def help_set(self):
        cprint.notice_p("set state")

    def do_set(self, arg, opts=None):
        args = arg.split()
        self.SimObj.set_item(args[0], args[1])

    def help_start(self):
        self.cprint.common_p("start simulator")

    def help_exit(self):
        self.cprint.common_p("exit console")

    def do_start(self, arg=None):
        self.SimObj.run_forever()

    def do_exit(self, arg=None):
        self.cprint.common_p("Exit simulator, good bye!")
        sys.exit(0)

    def help_log(self):
        self.cprint.notice_p(
            "change logger level: log %s" % (log_kv,))
    def do_log(self, arg):
        args = arg.split()
        if (len(args)!=1 or args[0] not in log_kv):
            self.cprint.warn_p("unknow log level: %s!" % (arg))
            self.help_log()
        else:
            self.Log.set_level(eval(log_kv[args[0]]))

    def help_show(self):
        self.cprint.notice_p("show simulator state")
    def do_show(self, arg=None):
        if not self.SimObj == None:
            self.SimObj.status_show()
        else:
            self.cprint.warn_p("Simulator is not started ...")

    def help_alarm(self):
        self.cprint.notice_p("send alarm:")
        self.cprint.notice_p("alarm error_code error_status error_level error_msg")
    def do_alarm(self, arg, opts=None):
        args = arg.split()
        if len(args) >= 2:
            if len(args) == 3:
                args.append('Test alarm')
            else:
                args.append(1)
                args.append('Test alarm')
            self.SimObj.add_alarm(error_code=args[0], error_status=args[1], error_level=int(
                args[2]), error_msg=args[3])
        else:
            self.help_alarm()

    def help_switch(self):
        self.cprint.notice_p("switch air:switch %s" % (onoff_kv,))
    def do_switch(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in onoff_kv):
            self.help_switch()
        else:
            self.SimObj.set_item("_switchStatus",onoff_kv[args[0]])

    def help_mode(self):
        self.cprint.notice_p("set air mode:mode %s" % (mode_kv,))
    def do_mode(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in mode_kv):
            self.help_mode()
        else:
            self.SimObj.set_item("_mode", mode_kv[args[0]])

    def help_speed(self):
        self.cprint.notice_p('set air mode:mode %s' % (speed_kv,))
    def do_speed(self,arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in speed_kv):
            self.help_speed()
        else:
            self.SimObj.set_item("_speed", speed_kv[args[0]])

    def help_wind_ud(self):
        self.cprint.notice_p("set air wind_up_down:wind_ud %s" % (onoff_kv,))
    def do_wind_ud(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in onoff_kv):
            self.help_wind_ud()
        else:
            self.SimObj.set_item("_wind_up_down",onoff_kv[args[0]])

    def help_wind_lr(self):
        self.cprint.notice_p("set air wind_left_right:wind_lr %s" % (onoff_kv,))
    def do_wind_lr(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in onoff_kv):
            self.help_wind_ud()
        else:
            self.SimObj.set_item("_wind_left_right",onoff_kv[args[0]])

    def help_tp(self):
        self.cprint.notice_p("set air temperature:tp [160,300]")
    def do_tp(self, arg):
        args = arg.split()
        if(len(args)!=1 or not args[0].isdigit() or int(args[0]) < 160 or int(args[0]) > 300):
            self.help_tp()
        else:
            self.SimObj.set_item("_temperature",int(args[0]))

if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.DEBUG)
    cprint = cprint(__name__)
    mac=str(hex(int(time.time())))[-8:]
    sim = Air(LOG,mac=mac,addr=rout_addr)
    airCmd = AirCmd(logger=LOG, cprint=cprint, sim=sim)
    airCmd.do_start()
    LOG.warn("start simu mac [%s]" % (mac,))
    airCmd.cmdloop()