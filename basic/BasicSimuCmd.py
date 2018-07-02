#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-6-29'
"""
import sys
from cmd import Cmd
from basic.cprint import cprint
from protocol.wifi_devices import *

# region const variates
log_kv = [("0","logging.CRITICAL"),("1","logging.ERROR"),("2","logging.WARNING"),("3","logging.INFO"),("4","logging.DEBUG")]

class BasicCmd(Cmd):
    def __init__(self, logger, cprint, addr,version="20180628", d_type="Air", mac="666666"):
        Cmd.__init__(self)
        self.Log = logger
        self.cprint = cprint
        self.sim_obj = eval(d_type)(logger,mac=mac,addr=addr)
        self.prompt = "%s>>" % (d_type,)
        self.intro = "Welcome from %sCmd (Version:%s)!" % (d_type, version,)
        self.do_log("3")
        self.do_start()

    def emptyline(self):
        pass

    def help_set(self):
        cprint.notice_p("set state: set key value")
    def do_set(self, arg, opts=None):
        args = arg.split()
        self.sim_obj.set_item(args[0], args[1])

    def help_start(self):
        self.cprint.common_p("start simulator runforever")

    def help_exit(self):
        self.cprint.common_p("exit console")

    def do_start(self, arg=None):
        self.sim_obj.run_forever()

    def do_exit(self, arg=None):
        self.cprint.common_p("Exit simulator, good bye!")
        sys.exit(0)

    def help_log(self):
        self.cprint.notice_p(
            "change logger level: log %s" % (log_kv,))
    def do_log(self, arg):
        args = arg.split()
        if (len(args)!=1 or not args[0].isdigit() or int(args[0]) > (len(log_kv)-1)):
            self.cprint.warn_p("unknow log level: %s!" % (arg))
            self.help_log()
        else:
            self.Log.set_level(eval(log_kv[int(args[0])][1]))

    def help_show(self):
        self.cprint.notice_p("show simulator state")
    def do_show(self, arg=None):
        if not self.sim_obj == None:
            self.sim_obj.status_show()
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
            self.sim_obj.add_alarm(error_code=args[0], error_status=args[1], error_level=int(
                args[2]), error_msg=args[3])
        else:
            self.help_alarm()

if __name__ == '__main__':
    pass