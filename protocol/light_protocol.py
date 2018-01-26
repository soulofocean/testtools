#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""light protocol handle
by Kobe Gong. 2018-1-15
"""

import binascii
import datetime
import json
import logging
import os
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
from APIs.common_APIs import crc, crc16, protocol_data_printB
from protocol.protocol_process import communication_base

try:
    import queue as Queue
except:
    import Queue


class SDK(communication_base):
    state_lock = threading.Lock()

    def __init__(self, addr, logger, time_delay=0, self_addr=None):
        self.queue_in = Queue.Queue()
        self.queue_out = Queue.Queue()
        super(SDK, self).__init__(self.queue_in, self.queue_out,
                                  logger=logger, left_data=b'', min_length=57)
        self.addr = addr
        self.name = 'Device controler'
        self.connection = my_socket.MyClient(
            addr, logger, self_addr=self_addr, debug=False)
        self.state = 'close'
        self.time_delay = time_delay
        self.sim_obj = None

        # status data:
        # 4bytes
        self.version = b'HDXM'
        # 20bytes
        self.device_id = b'\x31\x30\x30\x34\x32\x30\x31\x36\x35\x38\x46\x43\x44\x42\x44\x38\x33\x34\x31\x45'
        # 4bytes
        self.pkg_number = b'\x00\x00\x00\x01'

    def msg_build(self, data, ack=b'\x01'):
        self.LOG.yinfo("send msg: " + self.convert_to_dictstr(data))
        if isinstance(data, type(b'')):
            pass
        else:
            data = data.encode('utf-8')
        if ack == b'\x00':
            src_id = self.device_id
            dst_id = b'\x30' * 20
            self.add_pkg_number()
        else:
            src_id = self.device_id
            dst_id = b'\x30' * 20

        if isinstance(src_id, type(b'')):
            pass
        else:
            src_id = src_id.encode('utf-8')
        msg_head = self.version + src_id + dst_id + ack + self.pkg_number
        msg_length = self.get_msg_length(data)
        msg_crc16 = crc16(data)
        msg = msg_head + msg_length + b'\x00\x00' + msg_crc16 + data
        return msg

    def protocol_data_washer(self, data):
        data_list = []
        left_data = b''

        while data[0:1] != b'\x48' and len(data) >= self.min_length:
            self.LOG.warn('give up dirty data: %02x' % ord(data[0]))
            data = data[1:]

        if len(data) < self.min_length:
            left_data = data
        else:
            if data[0:4] == b'\x48\x44\x58\x4d':
                length = struct.unpack('>I', data[49:53])[0]
                if length <= len(data[57:]):
                    data_list.append(data[0:57 + length])
                    data = data[57 + length:]
                    if data:
                        data_list_tmp, left_data_tmp = self.protocol_data_washer(
                            data)
                        data_list += data_list_tmp
                        left_data += left_data_tmp
                elif length >= 1 and length < 1000:
                    left_data = data
                else:
                    for s in data[:4]:
                        self.LOG.warn('give up dirty data: %02x' % ord(s))
                    left_data = data[4:]
            else:
                pass

        return data_list, left_data

    def add_pkg_number(self):
        pkg_number = struct.unpack('>I', self.pkg_number)[0]
        pkg_number += 1
        self.pkg_number = struct.pack('>I', self.pkg_number)

    def get_pkg_number(self, data):
        return truct.unpack('>I', data)[0]

    def set_pkg_number(self, data):
        self.pkg_number = data

    def get_msg_length(self, msg):
        return struct.pack('>I', len(msg))

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        ack = False
        if msg[0:4] == b'\x48\x44\x58\x4d':
            if msg[4:4 + 20] == b'\x30' * 20 and (msg[4 + 20:4 + 20 + 20] == self.device_id or msg[4 + 20:4 + 20 + 20] == self.device_id.encode('utf-8')):
                if msg[44:45] != b'\x00':
                    self.LOG.info("Get ack!")
                    ack = True

                self.set_pkg_number(msg[45:49])
                data_length = struct.unpack('>I', msg[49:53])[0]
                crc16 = struct.unpack('>H', msg[55:57])
                data = json.loads(msg[57:57 + data_length].decode('utf-8'))
                self.LOG.info("recv msg: " + self.convert_to_dictstr(data))
                time.sleep(self.time_delay / 1000.0)
                rsp_msg = self.sim_obj.protocol_handler(data, ack)
                if rsp_msg:
                    final_rsp_msg = self.msg_build(rsp_msg)
                else:
                    final_rsp_msg = 'No_need_send'
                return final_rsp_msg

            else:
                self.LOG.error('Unknow msg: %s' % (msg))
                return "No_need_send"

        else:
            self.LOG.warn('Unknow msg: %s!' % (msg))
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
