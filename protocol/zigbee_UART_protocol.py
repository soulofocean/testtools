#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""zigbee UART protocol
by Kobe Gong. 2018-1-26
"""

import binascii
import datetime
import logging
import os
import random
import re
import struct
import sys
import threading
import time
from collections import defaultdict

import APIs.common_APIs as common_APIs
from APIs.common_APIs import (bit_clear, bit_get, bit_set, crc16,
                              protocol_data_printB)
from connections.my_serial import MySerial
from protocol.protocol_process import communication_base

try:
    import queue as Queue
except:
    import Queue

coding = sys.getfilesystemencoding()


class ZIGBEE(communication_base):
    status_lock = threading.Lock()

    def __init__(self, port, logger, time_delay=0):
        self.port = port
        self.LOG = logger
        super(ZIGBEE, self).__init__(queue_in=Queue.Queue(),
                                     queue_out=Queue.Queue(), logger=logger, left_data='', min_length=18)
        self.connection = MySerial(port, 115200, logger)
        self.devices = defaultdict(str)
        self.factorys = []
        self.state = 'close'
        self.time_delay = time_delay
        self.heartbeat_interval = 3
        self.heartbeat_data = ''

        # status data:
        self.head = b'\xaa\x55'
        self.dst_addr = b''
        self.src_addr = b'\x00\x00\xf1'
        self.working = False

    def set_work_status(self, status):
        self.working = status

    def add_device(self, factory):
        self.factorys.append(factory)
        self.LOG.info("Add factory: %s success! Now has %d factory!" %
                      (factory.__name__, len(self.factorys)))

    def del_device(self):
        self.factorys = self.factorys[1:]
        self.LOG.info("Del factory success! Now has %d factory!" %
                      (len(self.factorys)))

    def msg_build(self, datas):
        if len(datas) < 6:
            return 'No_need_send'
        tmp_msg = datas['control'] + datas['seq'] + self.dst_addr + \
            datas['addr'] + datas['cmd'] + datas['reserve'] + datas['data']

        rsp_msg = self.head
        rsp_msg += struct.pack('<B', len(tmp_msg) + 3)
        rsp_msg += tmp_msg
        rsp_msg += crc16(rsp_msg, reverse=True)
        #self.LOG.yinfo("send msg: " + self.convert_to_dictstr(datas))
        return rsp_msg

    def protocol_data_washer(self, data):
        msg_list = []
        left_data = ''

        while data[0:2] != b'\xaa\x55' and len(data) >= self.min_length:
            self.LOG.warn('give up dirty data: %02x' % ord(data[0]))
            data = data[1:]

        if len(data) < self.min_length:
            left_data = data
        else:
            length = struct.unpack('<B', data[2])[0]
            if length <= len(data[2:]):
                msg_list.append(data[0:2 + length])
                data = data[2 + length:]
                if data:
                    msg_list_tmp, left_data_tmp = self.protocol_data_washer(
                        data)
                    msg_list += msg_list_tmp
                    left_data += left_data_tmp
            elif length > 0:
                left_data = data
            else:
                for s in data[:3]:
                    self.LOG.warn('give up dirty data: %02x' % ord(s))
                left_data = data[3:]

        return msg_list, left_data

    def protocol_handler(self, msg):
        if msg[0:2] == b'\xaa\x55':
            length = struct.unpack('B', msg[2:2 + 1])[0]
            control = msg[3:3 + 1]
            seq = msg[4:4 + 1]
            dst_addr = msg[5:5 + 3]
            src_addr = msg[8:8 + 3]
            self.dst_addr = src_addr
            #self.src_addr = dst_addr
            cmd = msg[11:11 + 5]
            if dst_addr in self.devices:
                pass
            else:
                if self.factorys and self.working == False:
                    mac = ''.join(random.sample('0123456789abcdef', 3))
                    short_id = chr(random.randint(0, 255)) + \
                        chr(random.randint(0, 255))
                    Endpoint = b'\x00'
                    dst_addr = short_id + Endpoint
                    self.devices[dst_addr] = self.factorys[0](
                        logger=self.LOG, mac=mac, short_id=short_id, Endpoint=Endpoint)
                    self.devices[dst_addr].sdk_obj = self
                    self.devices[dst_addr].run_forever()
                    self.devices[short_id + b'\x01'] = self.devices[dst_addr]
                    self.LOG.warn("It is time to create a new zigbee device, type: %s, mac: %s" % (
                        self.factorys[0].__name__, mac))
                    # self.del_device()
                    self.set_work_status(True)
                else:
                    self.LOG.error(
                        "What is Fuck? Now has %d factory!" % (len(self.factorys)))
                    data_length = length - 16
                    data = msg[-2 - data_length:-2]
                    datas = {
                        'control': bit_set(control, 7),
                        'seq': seq,
                        'addr': dst_addr,
                        'cmd': cmd,
                        'reserve': b'',
                        'data': data,
                    }
                    return self.msg_build(datas)

            have_reserve_flag = bit_get(control, 3)
            if have_reserve_flag:
                reserve_length = struct.unpack('B', msg[16:16 + 1])[0]
                data_length = length - reserve_length - 16
                reserve_data = msg[16:16 + reserve_length]
            else:
                reserve_length = 0
                data_length = length - 16
                reserve_data = b''
            data = msg[-2 - data_length:-2]

            datas = {
                'control': control,
                'seq': seq,
                'addr': dst_addr,
                'cmd': cmd,
                'reserve': reserve_data,
                'data': data,
            }
            #self.LOG.info("debug recv msg: " + self.convert_to_dictstr(datas))
            time.sleep(self.time_delay / 1000.0)
            rsp_datas = self.devices[dst_addr].protocol_handler(datas)
            rsp_msg = ''
            if rsp_datas:
                if isinstance(rsp_datas, list):
                    for rsp in rsp_datas:
                        rsp_msg += self.msg_build(rsp)
                else:
                    rsp_msg = self.msg_build(rsp_datas)
            else:
                rsp_msg = 'No_need_send'
            return rsp_msg

        else:
            self.LOG.warn('Unknow msg: %s!' % (msg))
            return "No_need_send"

    @common_APIs.need_add_lock(status_lock)
    def connection_setup(self):
        self.LOG.warn('Try to open port %s...' % (self.port))
        if self.connection.is_open():
            self.LOG.info('Connection already setup!')
            return True
        elif self.connection.open():
            self.set_connection_state('online')
            self.LOG.info('Setup connection success!')
            return True
        else:
            self.LOG.warn(self.port + " can't open!")
            self.LOG.error('Setup connection failed!')
            return False

    def connection_close(self):
        if self.connection.close():
            self.connection = None
            self.set_connection_state('offline')
        else:
            self.LOG.error('Close connection failed!')

    def send_data(self, data):
        self.LOG.yinfo(protocol_data_printB(
            data, title=self.port + " send data:"))
        return self.connection.write(data)

    def recv_data(self):
        datas = self.connection.readall()
        if datas:
            self.LOG.info(protocol_data_printB(
                datas, title=self.port + " recv data:"))
        return datas

    def convert_to_dictstr(self, src):
        ret_str = ''
        ret_str += '\n{\n'
        for item in src:
            ret_str += protocol_data_printB(src[item],
                                            title="    %s," % (item))
            ret_str += '\n'
        ret_str += '}'
        return ret_str


if __name__ == '__main__':
    print(protocol_data_printB(msg, title='see see'))
