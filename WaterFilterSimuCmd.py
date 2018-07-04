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

class WaterFilterCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180703"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "Waterfilter"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version
                          , addr=rout_addr, mac=self.mac, d_type=self.device_type)
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


if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = WaterFilterCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()