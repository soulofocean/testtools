#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-2'
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

class HangerCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180702"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "Hanger"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version
                          , addr=rout_addr, mac=self.mac, d_type=self.device_type)
        self.onoff_kv = {"0": "off", "1": "on"}
        self.ctl_kv = {"0": "up", "1": "down", "2": "pause"}
        self.ster_d_list = [10, 20]
        self.dry_d_list = [30, 60, 90, 120]
        self.air_dry_d_list = [30, 60, 90, 120]

    def help_light(self):
        self.cprint.notice_p("%s light control:light %s" % (self.device_type, self.onoff_kv))

    def do_light(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_light()
        else:
            self.sim_obj.set_item("_light", self.onoff_kv[args[0]])

    def help_ctl(self):
        self.cprint.notice_p("%s up/down/pause control:ctl %s" % (self.device_type, self.ctl_kv))

    def do_ctl(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.ctl_kv):
            self.help_ctl()
        else:
            ctl_status = self.ctl_kv[args[0]]
            self.sim_obj.set_item("_status", ctl_status)
            if ctl_status == 'up':
                self.sim_obj.task_obj.del_task('change_status_bottom')
                self.sim_obj.task_obj.add_task(
                    'change_status_top', self.sim_obj.set_item, 1, 1000, '_status', 'top')

            elif ctl_status == 'down':
                self.sim_obj.task_obj.del_task('change_status_top')
                self.sim_obj.task_obj.add_task(
                    'change_status_bottom', self.sim_obj.set_item, 1, 1000, '_status', 'bottom')

            elif ctl_status == 'pause':
                self.sim_obj.task_obj.del_task('change_status_top')
                self.sim_obj.task_obj.del_task('change_status_bottom')

    def help_ster(self):
        self.cprint.notice_p("%s sterilization switch:ster %s" % (self.device_type, self.onoff_kv))

    def do_ster(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_ster()
        else:
            self.sim_obj.set_item("_sterilization", self.onoff_kv[args[0]])
            self.sim_obj.set_item("_sterilization_remain", self.sim_obj.get_item("_sterilization_duration"))

    def help_ster_d(self):
        self.cprint.notice_p("set %s sterilization duration:ster_d %s" % (self.device_type, self.ster_d_list))

    def do_ster_d(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) not in self.ster_d_list):
            self.help_ster_d()
        else:
            self.sim_obj.set_item("_sterilization_duration", int(args[0]))
            self.sim_obj.set_item("_sterilization_remain", self.sim_obj.get_item("_sterilization_duration"))

    def help_dry(self):
        self.cprint.notice_p("%s drying switch:dry %s" % (self.device_type, self.onoff_kv))

    def do_dry(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_dry()
        else:
            self.sim_obj.set_item("_drying", self.onoff_kv[args[0]])
            self.sim_obj.set_item("_drying_remain", self.sim_obj.get_item("_drying_duration"))

    def help_dry_d(self):
        self.cprint.notice_p("set %s drying duration:dry_d %s" % (self.device_type, self.dry_d_list))

    def do_dry_d(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) not in self.dry_d_list):
            self.help_dry_d()
        else:
            self.sim_obj.set_item("_drying_duration", int(args[0]))
            self.sim_obj.set_item("_drying_remain", self.sim_obj.get_item("_drying_duration"))

    def help_air_dry(self):
        self.cprint.notice_p("%s air drying switch:air_dry %s" % (self.device_type, self.onoff_kv))

    def do_air_dry(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_air_dry()
        else:
            self.sim_obj.set_item("_air_drying", self.onoff_kv[args[0]])
            self.sim_obj.set_item("_air_drying_remain", self.sim_obj.get_item("_drying_duration"))

    def help_air_dry_d(self):
        self.cprint.notice_p("set %s air drying duration:air_dry_d %s" % (self.device_type, self.air_dry_d_list))

    def do_air_dry_d(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) not in self.air_dry_d_list):
            self.help_air_dry_d()
        else:
            self.sim_obj.set_item("_air_drying_duration", int(args[0]))
            self.sim_obj.set_item("_air_drying_remain", self.sim_obj.get_item("_air_drying_duration"))


if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = HangerCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()
