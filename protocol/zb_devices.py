#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""devices sim
by Kobe Gong. 2018-1-15
"""

import copy
import datetime
import decimal
import json
import logging
import os
import random
import re
import shutil
import struct
import sys
import threading
import time
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from importlib import import_module

import APIs.common_APIs as common_APIs
from APIs.common_APIs import bit_clear, bit_get, bit_set, protocol_data_printB
from basic.log_tool import MyLogger
from basic.task import Task
from protocol.light_protocol import SDK
from protocol.wifi_protocol import Wifi

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

coding = sys.getfilesystemencoding()


class BaseSim():
    __metaclass__ = ABCMeta
    status_lock = threading.Lock()

    def __init__(self, logger):
        self.LOG = logger
        self.sdk_obj = None

        # state data:
        self.task_obj = None

    @common_APIs.need_add_lock(status_lock)
    def set_item(self, item, value):
        if item in self.__dict__:
            self.__dict__[item] = value
        else:
            self.LOG.error("Unknow item: %s" % (item))

    @common_APIs.need_add_lock(status_lock)
    def add_item(self, item, value):
        try:
            setattr(self, item, value)
        except:
            self.LOG.error("add item fail: %s" % (item))

    def status_show(self):
        for item in sorted(self.__dict__):
            if item.startswith('_'):
                self.LOG.warn("%s: %s" % (item, str(self.__dict__[item])))

    def send_msg(self, msg):
        return self.sdk_obj.add_send_data(self.sdk_obj.msg_build(msg))

    @abstractmethod
    def protocol_handler(self, msg, ack=False):
        pass

    def stop(self):
        self.need_stop = True
        self.sdk_obj.stop()
        if self.task_obj:
            self.task_obj.stop()
        self.LOG.warn('Thread %s stoped!' % (__name__))

    def run_forever(self):
        thread_list = []
        thread_list.append([self.sdk_obj.schedule_loop])
        thread_list.append([self.sdk_obj.send_data_loop])
        thread_list.append([self.sdk_obj.recv_data_loop])
        thread_list.append([self.sdk_obj.heartbeat_loop])
        thread_list.append([self.task_obj.task_proc])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def status_maintain(self):
        pass

    def status_report_monitor(self):
        need_send_report = False
        if not hasattr(self, 'old_status'):
            self.old_status = defaultdict(lambda: {})
            for item in self.__dict__:
                if item.startswith('_'):
                    self.LOG.yinfo("need check item: %s" % (item))
                    self.old_status[item] = copy.deepcopy(self.__dict__[item])

        for item in self.old_status:
            if self.old_status[item] != self.__dict__[item]:
                need_send_report = True
                self.old_status[item] = copy.deepcopy(self.__dict__[item])

        if need_send_report:
            self.send_msg(self.get_event_report())

    def get_cmd(self, cmd):
        cmds = {
            b'\x41': b'\x42',
            'default': b'\x0B',
        }
        return cmds.get(cmd, b'\x0B')


class Led(BaseSim):
    def __init__(self, logger):
        self.LOG = logger
        self.sdk_obj = None
        self.need_stop = False

        # state data:
        self.task_obj = Task('Washer-task', self.LOG)
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 60)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def run_forever(self):
        thread_list = []
        thread_list.append([self.task_obj.task_proc])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def protocol_handler(self, datas):
        need_ASP_response = False
        need_default_response = False
        rsp_datas = {
            'control': datas['control'],
            'seq': datas['seq'],
            'addr': datas['addr'],
            'cmd': datas['cmd'],
            'reserve': datas['reserve'],
            'data': b'\x88\x88',
        }
        if bit_get(datas['control'], 7):
            self.LOG.debug('ACK msg!')
            return

        if bit_get(datas['control'], 6):
            self.LOG.info('Device: %s, disable default Response!' %
                          (struct.unpack('3s', datas['addr'])))
        else:
            need_default_response = True
            self.LOG.info('Device: %s, enable default Response!' %
                          (struct.unpack('3s', datas['addr'])))

        if bit_get(datas['control'], 5):
            self.LOG.info('Device: %s, disable ASP Response!' %
                          (struct.unpack('3s', datas['addr'])))
        else:
            need_ASP_response = True
            self.LOG.INFO('Device: %s, enable ASP Response!' %
                          (struct.unpack('3s', datas['addr'])))

        req_cmd_type = datas['cmd'][0:0 + 1]
        req_cmd_domain = datas['cmd'][1:1 + 2]
        req_cmd_word = datas['cmd'][3:3 + 2]

        rsp_cmd_type = self.get_cmd(req_cmd_type)

        return rsp_datas


if __name__ == '__main__':

    pass
