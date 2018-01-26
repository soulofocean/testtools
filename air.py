#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""air sim
by Kobe Gong. 2017-9-11
"""

import re
import sys
import time
import os
import shutil
import datetime
import threading
import random
import signal
import subprocess
import argparse
import logging
from cmd import Cmd
import decimal

from collections import defaultdict

from basic.log_tool import MyLogger
from basic.cprint import cprint
import APIs.common_APIs as common_APIs
from APIs.common_APIs import my_system_no_check, my_system, my_system_full_output, protocol_data_printB
from protocol.air_protocol import Air

# 命令行参数梳理， 目前仅有-p 指定串口端口号
class ArgHandle():
    def __init__(self):
        self.parser = self.build_option_parser("-" * 50)

    def build_option_parser(self, description):
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            '-l', '--cmdloop',
            action='store_true',
            help='whether go into cmd loop',
        )

        parser.add_argument(
            '-n', '--serial-number',
            dest='serial_number',
            action='store',
            default=8,
            type=int,
            help='Specify how many serial port will be listened',
        )

        parser.add_argument(
            '-p', '--serial-port',
            dest='port_list',
            action='append',
            # metavar='pattern',
            # required=True,
            default=[],
            help='Specify serial port',
        )
        return parser

    def get_args(self, attrname):
        return getattr(self.args, attrname)

    def check_args(self):
        pass

    def run(self):
        self.args = self.parser.parse_args()
        cprint.notice_p("CMD line: " + str(self.args))
        self.check_args()


# CMD loop, 可以查看各个串口的消息统计
class MyCmd(Cmd):
    def __init__(self, coms_list, logger=None):
        Cmd.__init__(self)
        self.prompt = "AIR>"
        self.coms_list = coms_list
        self.LOG = logger

    def help_send(self):
        cprint.notice_p("send sting to comx, 'all' mean to all")

    def do_send(self, arg, opts=None):
        args = arg.split()
        if len(args) > 1 and args[0] in (self.coms_list.keys() + ['all']):
            if args[0] == 'all':
                for com in self.coms_list:
                    self.coms_list[com].queue_out.put(' '.join(args[1:]))
            else:
                self.coms_list[args[0]].queue_out.put(' '.join(args[1:]))
        else:
            cprint.warn_p("unknow port: %s!" % (arg))

    def help_log(self):
        cprint.notice_p("change logger level: log {0:critical, 1:error, 2:warning, 3:info, 4:debug}")

    def do_log(self, arg, opts=None):
        level = {
            '0': logging.CRITICAL,
            '1': logging.ERROR,
            '2': logging.WARNING,
            '3': logging.INFO,
            '4': logging.DEBUG,
        }
        if int(arg) in range(5):
            self.LOG.set_level(level[arg])
        else:
            cprint.warn_p("unknow log level: %s!" % (arg))

    def help_st(self):
        cprint.notice_p("show air conditioner state")

    def do_st(self, arg, opts=None):
        if len(arg) and arg in self.coms_list:
            self.coms_list[arg].show_state()
        else:
            cprint.warn_p("unknow port: %s!" % (arg))

    def default(self, arg, opts=None):
        try:
            subprocess.call(arg, shell=True)
        except:
            pass

    def emptyline(self):
        pass

    def help_exit(self):
        print("Will exit")

    def do_exit(self, arg, opts=None):
        cprint.notice_p("Exit CLI, good luck!")
        sys_cleanup()
        sys.exit()


# 系统调度
def sys_proc(action="default"):
    global thread_ids
    thread_ids = []
    for th in thread_list:
        thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

    for th in thread_ids:
        th.setDaemon(True)
        th.start()
        # time.sleep(0.1)


def sys_join():
    for th in thread_ids:
        th.join()


# 系统初始化函数，在所有模块开始前调用
def sys_init():
    LOG.info("Let's go!!!")


# 系统清理函数，系统退出前调用
def sys_cleanup():
    LOG.info("Goodbye!!!")


# 主程序入口
if __name__ == '__main__':
    # sys log init
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)

    # sys init
    sys_init()

    # cmd arg init
    arg_handle = ArgHandle()
    arg_handle.run()

    # multi thread
    global thread_list
    thread_list = []

    # create serial objs
    global coms_list
    coms_list = {}
    for com_id in arg_handle.get_args('port_list'):
        coms_list[com_id] = Air('COM' + com_id, logger=LOG)
        thread_list.append([coms_list[com_id].schedule_loop])
        thread_list.append([coms_list[com_id].send_data_loop])
        thread_list.append([coms_list[com_id].recv_data_loop])



    # run threads
    sys_proc()

    if arg_handle.get_args('cmdloop') or True:
        # cmd loop
        signal.signal(signal.SIGINT, lambda signal, frame: cprint.notice_p('Exit SYSTEM: exit'))
        my_cmd = MyCmd(coms_list, logger=LOG)
        my_cmd.cmdloop()

    else:
        sys_join()

        # sys clean
        sys_cleanup()
        sys.exit()
