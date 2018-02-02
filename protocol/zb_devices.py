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
        self.LOG.warn("xxoo")
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
            'Device Announce': {
                'cmd': b'\x40\x13\x00\x00\x00',
                'data': self.Short_id + self.mac + self.Capability,
            },

            'Active Endpoint Response': {
                'cmd': b'\x40\x05\x80\x00\x00',
                'data': b'\x00' + self.Short_id + b'\x01' + self.Endpoint,
            },

            'Leave response': {
                'cmd': b'\x40\x34\x80\x01\x00',
                'data': b'\x00',
            },

            'Read attribute response': {
                b'\x00\x00': {
                    'cmd': b'\x01\x00\x00\x04\x00',
                    'data': b'\x00' + b'\x42' + b'\x03' + 'LDS' + b'\x05\x00' + b'\x00' + b'\x42' + b'\x0e' + 'ZHA-ColorLight',
                },

                b'\x06\x00': {
                    'cmd': b'\x01\x06\x00\x00\x00',
                    'data': b'\x00' + b'\x10' + b'\x01' + self._Switch[0:0 + 1],
                },

                b'\x08\x00': {
                    'cmd': b'\x01\x08\x00\x00\x00',
                    'data': b'\x00' + b'\x20' + b'\x01' + b'\x00',
                },
            },

            'Bind response': {
                'cmd': b'\x40\x21\x80\x00\x00',
                'data': b'\x00',
            },

            'Configure reporting response': {
                b'\x06\x00': {
                    'cmd': b'\x07\x06\x00\x00\x00',
                    'data': b'\x00\x01',
                },

                b'\x08\x00': {
                    'cmd': b'\x07\x08\x00\x00\x00',
                    'data': b'\x00\x01',
                },

                'default': {
                    'cmd': b'\x07\x00\x00\x00\x00',
                    'data': b'\x00\x01',
                },
            },
        }
        return cmds.get(cmd, None)

    def get_default_response(self, datas):
        def_rsp = {
            'control': bit_set(datas['control'], 7),
            'seq': datas['seq'],
            'addr': self.sdk_obj.src_addr,
            'cmd': datas['cmd'],
            'reserve': b'',
            'data': b'',
        }
        return def_rsp

    def add_seq(self):
        seq = struct.unpack('B', self.seq)[0]
        seq += 1
        self.seq = struct.pack('B', seq)

    def set_seq(self, seq):
        self.seq = seq

    def convert_to_dictstr(self, src):
        ret_str = ''
        ret_str += '\n{\n'
        for item in src:
            ret_str += protocol_data_printB(src[item],
                                            title="    %s," % (item))
            ret_str += '\n'
        ret_str += '}'
        return ret_str


class Led(BaseSim):
    def __init__(self, logger, mac=b'123456', short_id=b'\x11\x11', Endpoint=b'\x01'):
        self.LOG = logger
        self.sdk_obj = None
        self.need_stop = False
        super(Led, self).__init__(logger=self.LOG)

        # state data:
        self._Switch = b'\x02\x00'
        self._Hue = b''
        self._Saturation = b''
        self.Transition_time = b''
        self._Color_X = b''
        self._Color_Y = b''
        self._Color_Temperature = b''
        self._Level = b''
        self._Window_covering = b''
        self.Percentage_Lift_Value = b''
        self.Short_id = short_id
        self.Endpoint = Endpoint
        self.mac = str(mac) + b'\x00' * (8 - len(str(mac)))
        self.Capability = b'\x01'
        self.seq = b'\x01'
        self.addr = b''
        self.task_obj = Task('Washer-task', self.LOG)
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 1)

        # self.task_obj.add_task('monitor event report',
        #                       self.status_report_monitor, 10000000, 1)

    def status_report_monitor(self):
        while self.need_stop == False:
            need_send_report = []
            if not hasattr(self, 'old_status'):
                self.old_status = defaultdict(lambda: {})
                for item in self.__dict__:
                    if item.startswith('_'):
                        self.LOG.yinfo("need check item: %s" % (item))
                        self.old_status[item] = copy.deepcopy(
                            self.__dict__[item])

            for item in self.old_status:
                if self.old_status[item] != self.__dict__[item]:
                    need_send_report.append(item)
                    self.old_status[item] = copy.deepcopy(self.__dict__[item])

            for item in need_send_report:
                self.LOG.warn('Device report: %s' % (item))
                self.event_report_proc(item)

    def run_forever(self):
        thread_list = []
        thread_list.append([self.task_obj.task_proc])
        thread_list.append([self.status_report_monitor])
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
            'cmd': b'\x0B' + datas['cmd'][1:],
            'reserve': datas['reserve'],
            'data': b'\x81',
        }
        if bit_get(datas['control'], 7):
            self.LOG.debug('ACK msg!')
            return
        else:
            self.LOG.info("recv msg: " + self.convert_to_dictstr(datas))
            self.send_msg(self.get_default_response(datas))
            self.set_seq(datas['seq'])
            self.addr = datas['addr']

        req_cmd_type = datas['cmd'][0:0 + 1]
        req_cmd_domain = datas['cmd'][1:1 + 2]
        req_cmd_word = datas['cmd'][3:3 + 2]

        if datas['cmd'] == b'\x40\x36\x00\x00\x00':
            rsp_data = self.get_cmd('Device Announce')
            if rsp_data:
                rsp_datas['control'] = datas['control']
                rsp_datas['cmd'] = rsp_data['cmd']
                rsp_datas['data'] = rsp_data['data']
            else:
                pass

        elif datas['cmd'] == b'\x40\x05\x00\x00\x00':
            self.Endpoint = b'\x01'
            rsp_data = self.get_cmd('Active Endpoint Response')
            #self.set_item('Short_id', datas['data'])
            if rsp_data:
                rsp_datas['cmd'] = rsp_data['cmd']
                rsp_datas['data'] = rsp_data['data']
            else:
                pass

        elif datas['cmd'] == b'\x40\x34\x00\x01\x00':
            rsp_data = self.get_cmd('Leave response')
            if rsp_data:
                rsp_datas['cmd'] = rsp_data['cmd']
                rsp_datas['data'] = rsp_data['data']
            else:
                pass

        elif datas['cmd'][:1] == b'\x00':
            rsp_data = self.get_cmd('Read attribute response')
            if rsp_data:
                if datas['cmd'][1:1 + 2] == b'\x00\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x00\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x00\x00']['data']

                elif datas['cmd'][1:1 + 2] == b'\x06\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x06\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x06\x00']['data']

                elif datas['cmd'][1:1 + 2] == b'\x08\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x08\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x08\x00']['data']

                else:
                    self.LOG.error("Fuck Read attribute response")
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        elif datas['cmd'] == b'\x40\x21\x00\x00\x00':
            #self.set_item('mac', datas['data'][0:0 + 8])
            #self.set_item('endpoint', datas['data'][8:8 + 1])
            #self.set_item('Short_id', datas['data'][9:9 + 2])
            rsp_data = self.get_cmd('Bind response')
            if rsp_data:
                rsp_datas['cmd'] = rsp_data['cmd']
                rsp_datas['data'] = rsp_data['data']
            else:
                pass

        elif datas['cmd'][0:0 + 1] == b'\x06':
            rsp_data = self.get_cmd('Configure reporting response')
            if rsp_data:
                if datas['cmd'][1:1 + 2] == b'\x06\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x06\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x06\x00']['data']

                elif datas['cmd'][1:1 + 2] == b'\x08\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x08\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x08\x00']['data']
                else:
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        elif datas['cmd'][0:0 + 1] == b'\x41':
            if datas['cmd'][1:1 + 2] == b'\x06\x00':
                self.set_item('_Switch', datas['cmd'][3:3 + 2])

            elif datas['cmd'][1:1 + 2] == b'\x00\x03':
                if datas['cmd'][3:3 + 2] == b'\x06\x00':
                    self.set_item('_Hue', datas['data'][0:0 + 1])
                    self.set_item('_Saturation', datas['data'][1:1 + 1])
                    #self.set_item('Transition_time', datas['data'][2:2 + 2])

                elif datas['cmd'][3:3 + 2] == b'\x07\x00':
                    self.set_item('_Color_X', datas['data'][0:0 + 2])
                    self.set_item('_Color_Y', datas['data'][2:2 + 2])
                    #self.set_item('Transition_time', datas['data'][4:4 + 2])

                elif datas['cmd'][3:3 + 2] == b'\x0a\x00':
                    self.set_item('_Color_Temperature', datas['data'][0:0 + 2])
                    #self.set_item('Transition_time', datas['data'][2:2 + 2])

                else:
                    self.LOG.error(protocol_data_printB(
                        datas['cmd'][3:3 + 2], title='Unknow cmd:'))

            elif datas['cmd'][1:1 + 2] == b'\x08\x00':
                self.set_item('_Level', datas['cmd'][0:0 + 1])
                #self.set_item('Transition_time', datas['data'][1:1 + 2])

            elif datas['cmd'][1:1 + 2] == b'\x02\x01':
                if datas['cmd'][3:3 + 2] == b'\x00\x00':
                    self.set_item('_Window_covering', datas['cmd'][3:3 + 2])

                elif datas['cmd'][3:3 + 2] == b'\x01\x00':
                    self.set_item('_Window_covering', datas['cmd'][3:3 + 2])

                elif datas['cmd'][3:3 + 2] == b'\x02\x00':
                    self.set_item('_Window_covering', datas['cmd'][3:3 + 2])

                elif datas['cmd'][3:3 + 2] == b'\x05\x00':
                    self.set_item('_Window_covering', datas['cmd'][3:3 + 2])
                    self.set_item('Percentage_Lift_Value',
                                  datas['data'][0:0 + 1])

                else:
                    self.LOG.error(protocol_data_printB(
                        datas['cmd'][3:3 + 2], title='Unknow cmd:'))

            else:
                self.LOG.error(protocol_data_printB(
                    datas['cmd'][1:1 + 2], title='Unknow cmd:'))

            return

        else:
            self.LOG.error("What is the fuck msg?")
            return "No_need_send"

        self.LOG.yinfo("send msg: " + self.convert_to_dictstr(rsp_datas))
        return rsp_datas

    def event_report_proc(self, req_cmd_word):
        if req_cmd_word == '_Switch':
            return self.send_msg(self.get_event_report(self._Switch, data=b''))

        elif req_cmd_word == '_Hue':
            pass

        elif req_cmd_word == '_Level':
            pass

        elif req_cmd_word == '_Window_covering':
            pass

        else:
            pass

    def get_event_report(self, req_cmd_word, data):
        self.add_seq()
        send_datas = {
            'control': b'\x00',
            'seq': self.seq,
            'addr': self.addr,
            'cmd': b'\x0a' + b'\x00\x00' + req_cmd_word,
            'reserve': b'',
            'data': data,
        }
        return send_datas


if __name__ == '__main__':

    pass
