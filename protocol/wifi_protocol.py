#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""air sim protocol handle
by Kobe Gong. 2017-9-13
"""

import binascii
import datetime
import json
import logging
import os
import Queue
import random
import re
import struct
import sys
import threading
import time
from abc import ABCMeta, abstractmethod
from collections import defaultdict

import APIs.common_APIs as common_APIs
import connections.my_socket as my_socket
from APIs.common_APIs import crc, protocol_data_printB
from protocol.protocol_process import communication_base


class Wifi(communication_base):
    state_lock = threading.Lock()

    def __init__(self, logger=None, addr=('192.168.10.1', 65381), time_delay=500, mac='123456', deviceCategory='airconditioner.new', self_addr=None):
        self.queue_in = Queue.Queue()
        self.queue_out = Queue.Queue()
        super(Wifi, self).__init__(self.queue_in, self.queue_out,
                                   logger=logger, left_data=b'', min_length=10)
        self.addr = addr
        self.name = 'WIFI module'
        self.connection = my_socket.MyClient(
            addr, logger, self_addr=self_addr, debug=False)
        self.state = 'close'
        self.time_delay = time_delay
        self.sim_obj = None
        self.heartbeat_interval = 3
        self.heartbeat_data = '0'

        # state data:
        # 2:short version
        self.version = '\x01\x00'
        # char mac[32]
        #mac = random.randint(100000, 999999)
        self.mac = str(mac) + '\x00' * (32 - len(str(mac)))
        # char manufactureId[34]; // manuafacture name: haier
        manufacture = 'HDiot'
        self.manufacture = manufacture + '\x00' * (34 - len(manufacture))
        # char deviceCategory[34]; // device category: KFR-50LW/10CBB23AU1
        self.deviceCategory = deviceCategory + \
            '\x00' * (34 - len(deviceCategory))
        # 2:short subCategory; //subCategory: 1
        self.subCategory = '\x01\x00'
        # char deviceModel[34];// device model: KFR-50LW/10CBB23AU1
        self.deviceModel = 'KFR-50LW/10CBB23AU1' + \
            '\x00' * (34 - len('KFR-50LW/10CBB23AU1'))
        # char firmwareVersion[32];// firmware version
        firmwareVersion = '0.6.8'
        self.firmwareVersion = firmwareVersion + \
            '\x00' * (32 - len(firmwareVersion))
        # char token[32];
        self.token = 'xx' + '\x00' * (32 - len('xx'))
        # 1:unsigned char wait_added;
        self.wait_added = '\x00'

    def msg_build(self, data):
        # self.LOG.debug(str(data))
        self.LOG.yinfo("send msg: " + self.convert_to_dictstr(data))
        msg_head = self.get_msg_head(data)
        msg_code = '\x01'
        msg_length = self.get_msg_length(msg_code + data + '\x00')
        msg = msg_head + msg_length + msg_code + data + '\x00'
        return msg

    def protocol_data_washer(self, data):
        data_list = []
        left_data = ''

        while data[0] != b'\x77' and len(data) >= self.min_length:
            self.LOG.warn('give up dirty data: %02x' % ord(data[0]))
            data = data[1:]

        if len(data) < self.min_length:
            left_data = data
        else:
            if data[0:4] == b'\x77\x56\x43\xaa':
                length = struct.unpack('>H', data[4:6])[0]
                if length <= len(data[6:]):
                    data_list.append(data[4:4 + length + 2])
                    data = data[4 + length + 2:]
                    if data:
                        data_list_tmp, left_data_tmp = self.protocol_data_washer(
                            data)
                        data_list += data_list_tmp
                        left_data += left_data_tmp
                elif length >= 4:
                    left_data = data
                else:
                    for s in data[:4]:
                        self.LOG.warn('give up dirty data: %02x' % ord(s))
                    left_data = data[4:]
            else:
                pass

        return data_list, left_data

    def get_msg_head(self, msg):
        resp_msg = '\x77\x56\x43\xaa'
        #self.LOG.debug(protocol_data_printB(resp_msg, title="head is:"))
        return resp_msg

    def get_msg_code(self, msg):
        resp_msg = '\x01'
        resp_msg += struct.pack('>B', struct.unpack('>B', msg[3])[0] + 1)
        #for AI Router 0.4.5 should resp_msg += msg[4:6]
        resp_msg += msg[4:6]
        #self.LOG.debug(protocol_data_printB(resp_msg, title="code is:"))
        return resp_msg

    def get_msg_length(self, msg):
        resp_msg = struct.pack('>H', len(msg))
        #self.LOG.debug(protocol_data_printB(resp_msg, title="length is:"))
        return resp_msg

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg[2] == b'\x02':
            if msg[3] == b'\x20':
                if msg[4:6] == b'\x00\x05':
                    self.LOG.warn("获取设备信息".decode('utf-8').encode(coding))
                    rsp_msg = ''
                    rsp_msg += self.version
                    rsp_msg += self.mac
                    rsp_msg += self.manufacture
                    rsp_msg += self.deviceCategory
                    rsp_msg += self.subCategory
                    rsp_msg += self.deviceModel
                    rsp_msg += self.firmwareVersion
                    rsp_msg += self.token
                    rsp_msg += self.wait_added
                    msg_head = self.get_msg_head(msg)
                    msg_code = self.get_msg_code(msg)
                    msg_length = self.get_msg_length(msg_code + rsp_msg)
                    return msg_head + msg_length + msg_code + rsp_msg

                elif msg[4:6] == b'\x00\x04':
                    self.LOG.warn("查询设备".decode('utf-8').encode(coding))
                    msg_head = self.get_msg_head(msg)
                    msg_code = self.get_msg_code(msg)
                    msg_length = self.get_msg_length(msg_code)
                    return msg_head + msg_length + msg_code

                elif msg[4:6] == b'\x00\x06':
                    self.LOG.warn("删除设备".decode('utf-8').encode(coding))
                    msg_head = self.get_msg_head(msg)
                    msg_code = self.get_msg_code(msg)
                    msg_length = self.get_msg_length(msg_code)
                    return msg_head + msg_length + msg_code

                else:
                    self.LOG.error('Unknow msg: %s' % (msg[4:6]))
                    return "No_need_send"

            else:
                self.LOG.error('Unknow msg: %s' % (msg[3:6]))
                return "No_need_send"

        elif msg[2] == b'\x03':
            dict_msg = json.loads(msg[3:-1])
            self.LOG.info("recv msg: " + self.convert_to_dictstr(dict_msg))
            time.sleep(self.time_delay / 1000.0)
            rsp_msg = self.sim_obj.protocol_handler(dict_msg)
            if rsp_msg:
                final_rsp_msg = self.msg_build(rsp_msg)
            else:
                final_rsp_msg = 'No_need_send'
            return final_rsp_msg

        else:
            self.LOG.warn('Todo in the feature!')
            return "No_need_send"

    @common_APIs.need_add_lock(state_lock)
    def connection_setup(self):
        self.LOG.warn('Try to connect %s...' % str(self.addr))
        if self.connection.get_connected():
            self.LOG.info('Connection already setup!')
            return True
        elif self.connection.connect():
            self.set_connection_state(True)
            self.LOG.info('Connection setup success!')
            return True
        else:
            self.LOG.warn("Can't connect %s!" % str(self.addr))
            self.LOG.error('Setup connection failed!')
            return False

    def connection_close(self):
        if self.connection.close():
            self.connection.set_connected(False)
            self.set_connection_state(False)
        else:
            self.LOG.error('Close connection failed!')

    def send_data(self, data):
        self.LOG.debug(protocol_data_printB(
            data, " send data:"))
        return self.connection.send_once(data)

    def recv_data(self):
        datas = self.connection.recv_once()
        if datas:
            self.LOG.debug(protocol_data_printB(
                datas, " recv data:"))
        return datas

    def convert_to_dictstr(self, src):
        if isinstance(src, dict):
            return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        elif isinstance(src, str):
            return json.dumps(json.loads(src), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        else:
            self.LOG.error('Unknow type(%s): %s' % (src, str(type(src))))
            return None


if __name__ == '__main__':
    #print(protocol_data_printB(msg, title='see see'))
    pass
