#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-4'
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

class WasherCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180704"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "Washer"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version
                          , addr=rout_addr, mac=self.mac, d_type=self.device_type)
        self.onoff_kv = {"0": "off", "1": "on"}

    def help_switch(self):
        self.cprint.notice_p("switch %s:switch %s" % (self.device_type, self.onoff_kv))
    def do_switch(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switch", self.onoff_kv[args[0]])

if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = WasherCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()