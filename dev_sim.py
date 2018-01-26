#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""sim
by Kobe Gong. 2018-1-15
"""


import argparse
import copy
import datetime
import decimal
import json
import logging
import os
import random
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import threading
import time
from cmd import Cmd
from collections import defaultdict

import APIs.common_APIs as common_APIs
from APIs.common_APIs import (my_system, my_system_full_output,
                              my_system_no_check, protocol_data_printB)
from basic.cprint import cprint
from basic.log_tool import MyLogger
from basic.task import Task
from protocol.devices import Door

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class ArgHandle():
    def __init__(self):
        self.parser = self.build_option_parser("-" * 50)

    def build_option_parser(self, description):
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            '-d', '--debug',
            dest='debug',
            action='store_true',
            help='debug switch',
        )
        parser.add_argument(
            '-t', '--time-delay',
            dest='time_delay',
            action='store',
            default=500,
            type=int,
            help='time delay(ms) for msg send to server, default time is 500(ms)',
        )
        parser.add_argument(
            '-p', '--server-port',
            dest='server_port',
            action='store',
            default=20001,
            type=int,
            help='Specify TCP server port, default is 20001',
        )
        parser.add_argument(
            '-i', '--server-IP',
            dest='server_IP',
            action='store',
            default='192.168.10.12',
            help='Specify TCP server IP address',
        )
        parser.add_argument(
            '--self_IP',
            dest='self_IP',
            action='store',
            default='',
            help='Specify TCP client IP address',
        )
        parser.add_argument(
            '--config',
            dest='config_file',
            action='store',
            default="door_conf",
            help='Specify device type',
        )
        parser.add_argument(
            '-c', '--count',
            dest='device_count',
            action='store',
            default=1,
            type=int,
            help='Specify how many devices to start, default is only 1',
        )
        return parser

    def get_args(self, attrname):
        return getattr(self.args, attrname)

    def check_args(self):
        global ipv4_list
        if arg_handle.get_args('device_count') > 1 and not arg_handle.get_args('self_IP'):
            cprint.error_p(
                "if device count big than 1, self_IP start must assign")
            sys.exit()
        elif arg_handle.get_args('device_count') > 1:
            ipv4s = common_APIs.get_local_ipv4()
            ip_prefix = '.'.join(arg_handle.get_args(
                'self_IP').split('.')[0:-1])
            ip_start = arg_handle.get_args('self_IP').split('.')[-1]
            ipv4s = [ip for ip in ipv4s if re.search(r'%s' % (ip_prefix), ip) and arg_handle.get_args(
                'self_IP').split('.')[-1] >= ip_start]
            if len(ipv4s) < arg_handle.get_args('device_count'):
                cprint.error_p("Local ips: %d not enough" % (len(ipv4s)))
                sys.exit()
            else:
                ipv4_list = ipv4s
        else:
            ip = ''
            if arg_handle.get_args('self_IP'):
                ip = arg_handle.get_args('self_IP')
            ipv4_list = [ip]

    def run(self):
        self.args = self.parser.parse_args()
        cprint.notice_p("CMD line: " + str(self.args))
        self.check_args()


class MyCmd(Cmd):
    def __init__(self, logger, sim_objs=None):
        Cmd.__init__(self)
        self.prompt = "SIM>"
        self.sim_objs = sim_objs
        self.LOG = logger

    def help_log(self):
        cprint.notice_p(
            "change logger level: log {0:critical, 1:error, 2:warning, 3:info, 4:debug}")

    def do_log(self, arg, opts=None):
        level = {
            '0': logging.CRITICAL,
            '1': logging.ERROR,
            '2': logging.WARNING,
            '3': logging.INFO,
            '4': logging.DEBUG,
        }
        if int(arg) in range(5):
            for i in self.sim_objs:
                cprint.notice_p("-" * 20)
                self.sim_objs[i].LOG.set_level(level[arg])
        else:
            cprint.warn_p("unknow log level: %s!" % (arg))

    def help_st(self):
        cprint.notice_p("show state")

    def do_st(self, arg, opts=None):
        for i in self.sim_objs:
            cprint.notice_p("-" * 20)
            self.sim_objs[i].status_show()

    def help_record(self):
        cprint.notice_p("send record:")
        for item in sorted(self.sim_objs[0].get_record_list()):
            cprint.yinfo_p("%s" % item)

    def do_record(self, arg, opts=None):
        if arg in self.sim_objs[0].get_record_list():
            for i in self.sim_objs:
                self.sim_objs[i].send_msg(
                    self.sim_objs[i].get_upload_record(arg))
        else:
            cprint.error_p("Unknow record: %s" % arg)

    def help_event(self):
        cprint.notice_p("send event")
        for item in sorted(self.sim_objs[0].get_event_list()):
            cprint.yinfo_p("%s" % item)

    def do_event(self, arg, opts=None):
        if arg in self.sim_objs[0].get_event_list():
            for i in self.sim_objs:
                self.sim_objs[i].send_msg(
                    self.sim_objs[i].get_upload_event(arg))
        else:
            cprint.error_p("Unknow event: %s" % arg)

    def help_set(self):
        cprint.notice_p("set state")

    def do_set(self, arg, opts=None):
        args = arg.split()
        for i in self.sim_objs:
            self.sim_objs[i].set_item(args[0], args[1])

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


def sys_init():
    LOG.info("Let's go!!!")


def sys_cleanup():
    LOG.info("Goodbye!!!")


if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.INFO,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)

    sys_init()

    arg_handle = ArgHandle()
    arg_handle.run()

    global thread_list
    thread_list = []

    sims = {}
    if arg_handle.get_args('device_count') > 1:
        log_level = logging.WARN
    else:
        log_level = logging.INFO
    for i in range(arg_handle.get_args('device_count')):
        dev_LOG = MyLogger('dev_sim_%d.log' % (i), clevel=log_level)

        self_addr = (ipv4_list[i], random.randint(
            arg_handle.get_args('server_port'), 65535))
        sim = Door(logger=dev_LOG, config_file=arg_handle.get_args('config_file'), server_addr=(
            arg_handle.get_args('server_IP'), arg_handle.get_args('server_port')), self_addr=self_addr)
        # thread_list.append([sim.run_forever])
        sim.run_forever()
        sims[i] = sim

    sys_proc()

    if arg_handle.get_args('debug'):
        dmsg = b''
        time.sleep(1)
        sim.sdk_obj.queue_in.put(dmsg)

    if True:
        # signal.signal(signal.SIGINT, lambda signal,
        #              frame: cprint.notice_p('Exit SYSTEM: exit'))
        my_cmd = MyCmd(logger=LOG, sim_objs=sims)
        my_cmd.cmdloop()

    else:
        sys_join()
        sys_cleanup()
        sys.exit()
