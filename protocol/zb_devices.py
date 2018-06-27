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
        self.need_stop = False

        # state data:
        self.task_obj = Task('common-task', self.LOG)
        self.create_tasks()

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
        thread_list.append([self.task_obj.task_proc])
        thread_list.append([self.status_report_monitor])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 1)

        # self.task_obj.add_task('monitor event report',
        #                       self.status_report_monitor, 10000000, 1)

    def status_maintain(self):
        pass

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
        if seq >= 255:
            seq = 0
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

    def get_event_report(self, req_cmd_word=b'\x0a' + b'\x06\x00' + b'\x00\x00', data=b'\x10\x01'):
        self.add_seq()
        send_datas = {
            'control': b'\x00',
            'seq': self.seq,
            'addr': self.addr,
            'cmd': req_cmd_word,
            'reserve': b'',
            'data': data,
        }
        return send_datas


class Led(BaseSim):
    def __init__(self, logger, mac=b'123456', short_id=b'\x11\x11', Endpoint=b'\x01'):
        super(Led, self).__init__(logger=logger)
        self.LOG = logger
        self.sdk_obj = None
        self.need_stop = False

        # state data:
        self._Switch = b'\x00\x00'
        self._Hue = b''
        self.Saturation = b''
        self._Color_X = b'\x66\x2d'
        self._Color_Y = b'\xdf\x5c'
        self._Color_Temperature = b'\xdd\x00'
        self._Level = b'\x00\x00'
        self._Window_covering = b''
        self.Percentage_Lift_Value = b''
        self.Short_id = short_id
        self.Endpoint = Endpoint
        self.mac = str(mac) + b'\x00' * (8 - len(str(mac)))
        self.Capability = b'\x05'
        self.seq = b'\x01'
        self.cmd = b''
        self.addr = b''

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
                    #'data': b'\x00' + b'\x42' + b'\x03' + 'PAK' + b'\x05\x00' + b'\x00' + b'\x42' + b'\x16' + 'PAK_Dimmable_downlight',
                    #'data': b'\x00' + b'\x42' + b'\x03' + 'LDS' + b'\x05\x00' + b'\x00' + b'\x42' + b'\x0e' + 'ZHA-ColorLight',
                    'data': b'\x00' + b'\x42' + b'\x03' + 'PAK' + b'\x05\x00' + b'\x00' + b'\x42' + b'\x16' + 'PAK_RGB_LedStrip',
                },

                b'\x06\x00': {
                    'cmd': b'\x01\x06\x00\x00\x00',
                    'data': b'\x00' + b'\x10' + b'\x01' + self._Switch[0:0 + 1],
                },

                b'\x08\x00': {
                    'cmd': b'\x01\x08\x00\x00\x00',
                    'data': b'\x00' + b'\x20' + b'\x01' + self._Level[0:0 + 1],
                },

                b'\x00\x03': {
                    'cmd': b'\x01\x00\x03' + self.cmd[3:3 + 2],
                    'data': b'\x00' + b'\x21' + b'\x04' + self._Color_X + self._Color_Y,
                },
                'default': {
                    'cmd': b'\x01\x00\x00\x00\x00',
                    'data': b'\x00' + b'\x10' + b'\x01\x00',
                },
            },

            'Bind response': {
                'cmd': b'\x40\x21\x80\x00\x00',
                'data': b'\x00',
            },

            'Configure reporting response': {
                b'\x06\x00': {
                    'cmd': b'\x07\x06\x00\x00\x00',
                    'data': b'\x00\x00\x00\x00',
                },

                b'\x08\x00': {
                    'cmd': b'\x07\x08\x00\x00\x00',
                    'data': b'\x00\x00\x00\x00',
                },

                b'\x00\x03': {
                    'cmd': b'\x07\x00\x03' + self.cmd[3:3 + 2],
                    'data': b'\x00\x00\x00\x00',
                },

                'default': {
                    'cmd': b'\x07\x00\x00\x00\x00',
                    'data': b'\x00\x00\x00\x00',
                },
            },
        }
        return cmds.get(cmd, None)

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
            self.cmd = datas['cmd']

        req_cmd_type = datas['cmd'][0:0 + 1]
        req_cmd_domain = datas['cmd'][1:1 + 2]
        req_cmd_word = datas['cmd'][3:3 + 2]

        if datas['cmd'][:1] == b'\x40':
            if datas['cmd'][1:] == b'\x36\x00\x00\x00':
                rsp_data = self.get_cmd('Device Announce')
                if rsp_data:
                    rsp_datas['control'] = datas['control']
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x05\x00\x00\x00':
                self.Endpoint = b'\x01'
                rsp_data = self.get_cmd('Active Endpoint Response')
                #self.set_item('Short_id', datas['data'])
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x34\x00\x01\x00':
                self.sdk_obj.set_work_status(False)
                rsp_data = self.get_cmd('Leave response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x21\x00\x00\x00':
                #self.set_item('mac', datas['data'][0:0 + 8])
                #self.set_item('endpoint', datas['data'][8:8 + 1])
                #self.set_item('Short_id', datas['data'][9:9 + 2])
                rsp_data = self.get_cmd('Bind response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            else:
                self.LOG.error(protocol_data_printB(
                    datas['cmd'][1:], title='Unknow cmd:'))

        elif datas['cmd'][:1] == b'\x41':
            if datas['cmd'][1:1 + 2] == b'\x06\x00':
                if datas['cmd'][3:3 + 2] == b'\x00\x00':
                    self.set_item('_Switch', b'\x00')
                elif datas['cmd'][3:3 + 2] == b'\x01\x00':
                    self.set_item('_Switch', b'\x01')
                else:
                    self.set_item('_Switch', b'\x02')

            elif datas['cmd'][1:1 + 2] == b'\x00\x03':
                if datas['cmd'][3:3 + 2] == b'\x06\x00':
                    self.set_item('_Hue', datas['data'][0:0 + 1])
                    self.set_item('Saturation', datas['data'][1:1 + 1])

                elif datas['cmd'][3:3 + 2] == b'\x07\x00':
                    self.set_item('_Color_X', datas['data'][0:0 + 2])
                    self.set_item('_Color_Y', datas['data'][2:2 + 2])

                elif datas['cmd'][3:3 + 2] == b'\x0a\x00':
                    self.set_item('_Color_Temperature', datas['data'][0:0 + 2])

                else:
                    self.LOG.error(protocol_data_printB(
                        datas['cmd'][3:3 + 2], title='Unknow cmd:'))

            elif datas['cmd'][1:1 + 2] == b'\x08\x00':
                self.set_item('_Level', datas['data'][0:0 + 1])

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
                #add by -zx for cmd:00 00 03 03 00 and 00 00 03 04 00
                elif datas['cmd'][1:1 + 2] == b'\x00\x03':
                    rsp_datas['cmd'] = rsp_data[b'\x00\x03']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x00\x03']['data']

                else:
                    self.LOG.error("Fuck Read attribute response")
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        elif datas['cmd'][:1] == b'\x06':
            self.sdk_obj.set_work_status(False)
            rsp_data = self.get_cmd('Configure reporting response')
            if rsp_data:
                if datas['cmd'][1:1 + 2] == b'\x06\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x06\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x06\x00']['data']

                elif datas['cmd'][1:1 + 2] == b'\x08\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x08\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x08\x00']['data']

                elif datas['cmd'][1:1 + 2] == b'\x00\x03':
                    rsp_datas['cmd'] = rsp_data[b'\x00\x03']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x00\x03']['data']

                else:
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        else:
            self.LOG.error("What is the fuck msg?")
            return

        self.LOG.yinfo("send msg: " + self.convert_to_dictstr(rsp_datas))
        return rsp_datas

    def event_report_proc(self, req_cmd_word):
        if req_cmd_word == '_Switch':
            return self.send_msg(self.get_event_report(req_cmd_word=b'\x0a' + b'\x06\x00' + b'\x00\x00', data=b'\x10' + self._Switch))

        elif req_cmd_word == '_Color_Temperature' or req_cmd_word == '_Color_X':
            return self.send_msg(self.get_event_report(req_cmd_word=b'\x0a' + b'\x00\x03' + b'\x04\x00',
                                                       data=b'\x21' + self._Color_Y + b'\x03\x00' +
                                                       b'\x21' + self._Color_X + b'\x07\x00' +
                                                       b'\x21' + self._Color_Temperature))

        elif req_cmd_word == '_Level':
            return self.send_msg(self.get_event_report(req_cmd_word=b'\x0a' + b'\x08\x00' + b'\x00\x00', data=b'\x20' + self._Level))

        elif req_cmd_word == '_Window_covering':
            pass

        else:
            pass


class Curtain(BaseSim):
    def __init__(self, logger, mac=b'123456', short_id=b'\x11\x11', Endpoint=b'\x01'):
        super(Curtain, self).__init__(logger=logger)
        self.LOG = logger
        self.sdk_obj = None
        self.need_stop = False

        # state data:
        self.switch = 99
        self._percent_lift = 1
        self.Short_id = short_id
        self.Endpoint = Endpoint
        self.mac = str(mac) + b'\x00' * (8 - len(str(mac)))
        self.Capability = b'\x02'
        self.seq = b'\x01'
        self.cmd = b''
        self.addr = b''

    def update_percent_lift(self, action):
        if action == 'close':
            if self._percent_lift > 1:
                self._percent_lift -= 1
            else:
                pass
        else:
            if self._percent_lift < 100:
                self._percent_lift += 1
            else:
                pass

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
                    'data': b'\x00' + b'\x42' + b'\x05' + 'dooya' + b'\x05\x00' + b'\x00' + b'\x42' + b'\x0d' + 'onoff_curtain',
                },

                b'\x02\x01': {
                    'cmd': b'\x01\x02\x01' + self.cmd[3:3 + 2],
                    'data': b'\x00' + b'\x20' + b'\x01' + b'\x88',
                },
            },

            'Bind response': {
                'cmd': b'\x40\x21\x80\x00\x00',
                'data': b'\x00',
            },

            'Configure reporting response': {
                b'\x02\x01': {
                    'cmd': b'\x07\x02\x01' + self.cmd[3:3 + 2],
                    'data': b'\x00\x00\x00\x00',
                },

                'default': {
                    'cmd': b'\x07\x00\x00\x00\x00',
                    'data': b'\x00\x00\x00\x00',
                },
            },
        }
        return cmds.get(cmd, None)

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
            self.cmd = datas['cmd']

        req_cmd_type = datas['cmd'][0:0 + 1]
        req_cmd_domain = datas['cmd'][1:1 + 2]
        req_cmd_word = datas['cmd'][3:3 + 2]

        if datas['cmd'][:1] == b'\x40':
            if datas['cmd'][1:] == b'\x36\x00\x00\x00':
                rsp_data = self.get_cmd('Device Announce')
                if rsp_data:
                    rsp_datas['control'] = datas['control']
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x05\x00\x00\x00':
                self.Endpoint = b'\x01'
                rsp_data = self.get_cmd('Active Endpoint Response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x34\x00\x01\x00':
                self.sdk_obj.set_work_status(False)
                rsp_data = self.get_cmd('Leave response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x21\x00\x00\x00':
                rsp_data = self.get_cmd('Bind response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            else:
                self.LOG.error(protocol_data_printB(
                    datas['cmd'][1:], title='Unknow cmd:'))

        elif datas['cmd'][:1] == b'\x41':
            if datas['cmd'][1:1 + 2] == b'\x02\x01':
                if datas['cmd'][3:3 + 2] == b'\x00\x00':
                    self.set_item('switch', 1)
                    self.task_obj.del_task('close')
                    self.task_obj.add_task(
                        'open', self.update_percent_lift, 100, 10, 'open')

                elif datas['cmd'][3:3 + 2] == b'\x01\x00':
                    self.set_item('switch', 0)
                    self.task_obj.del_task('open')
                    self.task_obj.add_task(
                        'close', self.update_percent_lift, 100, 10, 'close')

                elif datas['cmd'][3:3 + 2] == b'\x02\x00':
                    self.set_item('switch', 2)
                    self.task_obj.del_task('close')
                    self.task_obj.del_task('open')

                elif datas['cmd'][3:3 + 2] == b'\x05\x00':
                    self.task_obj.del_task('close')
                    self.task_obj.del_task('open')
                    self.set_item('_percent_lift', struct.unpack(
                        'B', datas['data'][:])[0])

                else:
                    self.LOG.error(protocol_data_printB(
                        datas['cmd'][3:3 + 2], title='What is the fuck cmd:'))

            else:
                self.LOG.error(protocol_data_printB(
                    datas['cmd'][1:1 + 2], title='Unknow cmd:'))

            return

        elif datas['cmd'][:1] == b'\x00':
            rsp_data = self.get_cmd('Read attribute response')
            if rsp_data:
                if datas['cmd'][1:1 + 2] == b'\x00\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x00\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x00\x00']['data']

                elif datas['cmd'][1:1 + 2] == b'\x02\x01':
                    rsp_datas['cmd'] = rsp_data[b'\x02\x01']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x02\x01']['data']

                else:
                    self.LOG.error("Fuck Read attribute response")
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        elif datas['cmd'][:1] == b'\x06':
            self.sdk_obj.set_work_status(False)
            rsp_data = self.get_cmd('Configure reporting response')
            if rsp_data:
                if datas['cmd'][1:1 + 2] == b'\x02\x01':
                    rsp_datas['cmd'] = rsp_data[b'\x02\x01']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x02\x01']['data']

                else:
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        else:
            self.LOG.error("What is the fuck msg?")
            return

        self.LOG.yinfo("send msg: " + self.convert_to_dictstr(rsp_datas))
        return rsp_datas

    def event_report_proc(self, req_cmd_word):
        if req_cmd_word == '_percent_lift':
            return self.send_msg(self.get_event_report(req_cmd_word=b'\x0a' + b'\x02\x01' + b'\x08\x00', data=b'\x20' + struct.pack('B', self._percent_lift)))

        else:
            pass


class Switch(BaseSim):
    def __init__(self, logger, mac=b'123456', short_id=b'\x11\x11', Endpoint=b'\x01'):
        super(Switch, self).__init__(logger=logger)
        self.LOG = logger
        self.sdk_obj = None
        self.need_stop = False

        # state data:
        self._Switch = b'\x08'
        self.Short_id = short_id
        self.Endpoint = Endpoint
        self.mac = str(mac) + b'\x00' * (8 - len(str(mac)))
        self.Capability = b'\x08'
        self.seq = b'\x01'
        self.cmd = b''
        self.addr = b''

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
                    'data': b'\x00' + b'\x42' + b'\x0a' + 'EverGrande' + b'\x05\x00' + b'\x00' + b'\x42' + b'\x0e' + 'BH-SZ103',
                },

                b'\x06\x00': {
                    'cmd': b'\x01\x06\x00\x00\x00',
                    'data': b'\x00' + b'\x10' + b'\x01' + b'\x00',
                },
            },

            'Bind response': {
                'cmd': b'\x40\x21\x80\x00\x00',
                'data': b'\x00',
            },

            'Configure reporting response': {
                b'\x06\x00': {
                    'cmd': b'\x07\x06\x00\x00\x00',
                    'data': b'\x00\x00\x00\x00',
                },
            },
        }
        return cmds.get(cmd, None)

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
            self.cmd = datas['cmd']

        req_cmd_type = datas['cmd'][0:0 + 1]
        req_cmd_domain = datas['cmd'][1:1 + 2]
        req_cmd_word = datas['cmd'][3:3 + 2]

        if datas['cmd'][:1] == b'\x40':
            if datas['cmd'][1:] == b'\x36\x00\x00\x00':
                rsp_data = self.get_cmd('Device Announce')
                if rsp_data:
                    rsp_datas['control'] = datas['control']
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x05\x00\x00\x00':
                self.Endpoint = b'\x01'
                rsp_data = self.get_cmd('Active Endpoint Response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x34\x00\x01\x00':
                self.sdk_obj.set_work_status(False)
                rsp_data = self.get_cmd('Leave response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            elif datas['cmd'][1:] == b'\x21\x00\x00\x00':
                rsp_data = self.get_cmd('Bind response')
                if rsp_data:
                    rsp_datas['cmd'] = rsp_data['cmd']
                    rsp_datas['data'] = rsp_data['data']
                else:
                    pass

            else:
                self.LOG.error(protocol_data_printB(
                    datas['cmd'][1:], title='Unknow cmd:'))

        elif datas['cmd'][:1] == b'\x41':
            if datas['cmd'][1:1 + 2] == b'\x06\x00':
                if datas['cmd'][3:3 + 2] == b'\x01\x00':
                    self.set_item('_Switch', b'\x01')

                elif datas['cmd'][3:3 + 2] == b'\x00\x00':
                    self.set_item('_Switch', b'\x00')

                else:
                    self.LOG.error(protocol_data_printB(
                        datas['cmd'][3:3 + 2], title='Unknow cmd:'))

            else:
                self.LOG.error(protocol_data_printB(
                    datas['cmd'][1:1 + 2], title='Unknow cmd:'))

            return

        elif datas['cmd'][:1] == b'\x00':
            rsp_data = self.get_cmd('Read attribute response')
            if rsp_data:
                if datas['cmd'][1:1 + 2] == b'\x00\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x00\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x00\x00']['data']

                elif datas['cmd'][1:1 + 2] == b'\x06\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x06\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x06\x00']['data']

                else:
                    self.LOG.error("Fuck Read attribute response")
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        elif datas['cmd'][:1] == b'\x06':
            self.sdk_obj.set_work_status(False)
            rsp_data = self.get_cmd('Configure reporting response')
            if rsp_data:
                if datas['cmd'][1:1 + 2] == b'\x06\x00':
                    rsp_datas['cmd'] = rsp_data[b'\x06\x00']['cmd']
                    rsp_datas['data'] = rsp_data[b'\x06\x00']['data']

                else:
                    self.LOG.error("Fuck Configure reporting response")
                    rsp_datas['cmd'] = rsp_data['default']['cmd']
                    rsp_datas['data'] = rsp_data['default']['data']

            else:
                pass

        else:
            self.LOG.error("What is the fuck msg?")
            return

        self.LOG.yinfo("send msg: " + self.convert_to_dictstr(rsp_datas))
        return rsp_datas

    def event_report_proc(self, req_cmd_word):
        if req_cmd_word == '_Switch':
            return self.send_msg(self.get_event_report(req_cmd_word=b'\x0a' + b'\x06\x00' + b'\x00\x00', data=b'\x10' + self._Switch))

        elif req_cmd_word == '_Window_covering':
            pass

        else:
            pass


if __name__ == '__main__':

    pass
