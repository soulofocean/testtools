#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""air sim protocol handle
by Kobe Gong. 2017-9-13
"""

import binascii
import datetime
import logging
import os
import Queue
import re
import struct
import sys
import threading
import time
from abc import ABCMeta, abstractmethod
from collections import defaultdict

import APIs.common_APIs as common_APIs
from APIs.common_APIs import crc, protocol_data_printB
from connections.my_serial import MySerial
from protocol.protocol_process import communication_base

# 空调模拟器


class Air(communication_base):
    state_lock = threading.Lock()

    def __init__(self, port=None, baudrate=9600, logger=None):
        super(Air, self).__init__(queue_in=Queue.Queue(),
                                  queue_out=Queue.Queue(), logger=logger, left_data='', min_length=13)
        self.port = port
        self.name = port
        self.connection = MySerial(port, baudrate, logger)
        self.msg_statistics = defaultdict(int)
        self.state = 'close'

        # 当前温度 1word
        self._TEMP = b'\x00\x00'

        # 设定温度 1word
        self._STEMP = b'\x00\x00'

        # 设定湿度和当前湿度
        # 高字节，设定湿度Humidity：范围：30%-90%(1E-5A)
        # 低字节，当前湿度HUM：湿度值范围：1-100%(00-64)
        self._HUMSD = b'\x00\x00'

        # 空气质量加外环温1word
        # 空气质量(1 byte )+ 外环温(1 byte)
        self._HHON = b'\x00\x00'

        # 功率1word
        self._MMON = b'\x00\x00'

        # PM2.5 1word
        self._HHOFF = b'\x00\x00'

        # 预留
        self._MMOFF = b'\x00\x00'

        # 模式 1word 0000 ~ 0004
        self._MODE = B'\x00\x00'

        # 风速 1word 0000 ~ 0003
        self._WIND = b'\x00\x00'

        # 立体送风 1word
        # SOLIDH0:表示字SOLIDH的第0位，为“0”时，表示无“上下摆风”
        #                           为“1”时，表示有“上下摆风”
        # SOLIDH1:表示字SOLIDH的第1位，为“0”时，表示无“左右摆风”
        #                           为“1”时，表示有“左右摆风”
        self._SOLLDH = b'\x00\x00'

        # 字A：WORDA ( 1 word )
        self._WORDA = b'\x00\x00'

        # 字B：WORDB( 1 word )
        self._WORDB = b'\x00\x00'

    # 存储空调设置温度
    def TEMP_set(self, word, ifprint=0):
        if self.bit_get(word, 15):
            if ifprint:
                temp1 = struct.unpack('BB', word)
                temp2 = temp1[0] * 256 + temp1[1] + 16 + 0.5
                self.LOG.warn("设定温度".decode(
                    'utf-8').encode(sys.getfilesystemencoding()) + ': %0.1f' % (temp2))
            self.WORDA_set_bit(5)
        else:
            if ifprint:
                temp1 = struct.unpack('BB', word)
                temp2 = temp1[0] * 256 + temp1[1] + 16
                self.LOG.warn("设定温度".decode(
                    'utf-8').encode(sys.getfilesystemencoding()) + ': %d' % (temp2))
            self.WORDA_clear_bit(5)
        self._STEMP = word
        self._TEMP = word

    # 存储空调送风设置，UD_data：上下送风标志， LR_data：左右送风标志
    def SOLLDH_set(self, UD_data=None, LR_data=None):
        if UD_data:
            if self.bit_get(UD_data, 0):
                self._SOLLDH = self.bit_set(self._SOLLDH, 0)
            else:
                self._SOLLDH = self.bit_clear(self._SOLLDH, 0)

        if LR_data:
            if self.bit_get(LR_data, 0):
                self._SOLLDH = self.bit_set(self._SOLLDH, 1)
            else:
                self._SOLLDH = self.bit_clear(self._SOLLDH, 1)

    # 存储空调风速设置
    def WIND_set(self, word, ifprint=0):
        if word in [b'\x00\x00', b'\x00\x01', b'\x00\x02', b'\x00\x03']:
            self._WIND = word
            if ifprint:
                if word == b'\x00\x00':
                    self.LOG.warn("风速高风".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
                elif word == b'\x00\x01':
                    self.LOG.warn("风速中风".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
                elif word == b'\x00\x02':
                    self.LOG.warn("风速低风".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
                else:
                    self.LOG.warn("风速自动".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
        else:
            self.LOG.error("风速设置异常".decode(
                'utf-8').encode(sys.getfilesystemencoding()))

    # 存储空调模式设置
    def MODE_set(self, word, ifprint=0):
        if word in [b'\x00\x00', b'\x00\x01', b'\x00\x02', b'\x00\x03', b'\x00\x04']:
            self._MODE = word
            if ifprint:
                if word == b'\x00\x00':
                    self.LOG.warn("自动模式".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
                elif word == b'\x00\x01':
                    self.LOG.warn("制冷模式".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
                elif word == b'\x00\x02':
                    self.LOG.warn("制热模式".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
                elif word == b'\x00\x03':
                    self.LOG.warn("送风模式".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
                else:
                    self.LOG.warn("除湿模式".decode(
                        'utf-8').encode(sys.getfilesystemencoding()))
        else:
            self.LOG.error("模式设置异常".decode(
                'utf-8').encode(sys.getfilesystemencoding()))

    # 存储空调湿度设置
    def HUMSD_set(self, word, ifprint=0):
        self._HUMSD = word
        if ifprint:
            temp1 = struct.unpack('BB', word)
            temp2 = temp1[0] * 256 + temp1[1]
            self.LOG.warn("除湿湿度".decode(
                'utf-8').encode(sys.getfilesystemencoding()) + ': %0.1f' % (temp2))

    # 设置WORDA的某位
    def WORDA_set_bit(self, bit):
        self._WORDA = self.bit_set(self._WORDA, bit)

    # 获取WORDA的某位
    def WORDA_get_bit(self, bit):
        return self.bit_get(self._WORDA, bit)

    # 清除WORDA的某位
    def WORDA_clear_bit(self, bit):
        self._WORDA = self.bit_clear(self._WORDA, bit)

    # 设置WORDB的某位
    def WORDB_set_bit(self, bit):
        self._WORDB = self.bit_set(self._WORDB, bit)

    # 清除WORDB的某位
    def WORDB_clear_bit(self, bit):
        self._WORDB = self.bit_clear(self._WORDB, bit)

    def bit_set(self, word, bit):
        temp1 = struct.unpack('BB', word)
        temp2 = temp1[0] * 256 + temp1[1]
        temp2 = temp2 | (1 << bit)
        return struct.pack('BB', temp2 >> 8, temp2 % 256)

    def bit_get(self, word, bit):
        temp1 = struct.unpack('BB', word)
        temp2 = temp1[0] * 256 + temp1[1]
        temp2 = temp2 & (1 << bit)
        return temp2

    def bit_clear(self, word, bit):
        temp1 = struct.unpack('BB', word)
        temp2 = temp1[0] * 256 + temp1[1]
        temp2 = temp2 & ~(1 << bit)
        return struct.pack('BB', temp2 >> 8, temp2 % 256)

    def msg_build(self):
        data = (self._TEMP + self._HHON + self._MMON + self._HHOFF + self._MMOFF
                + self._MODE + self._WIND + self._SOLLDH + self._WORDA + self._WORDB + self._HUMSD + self._STEMP)
        # 固定两位 ff ff
        answer = b'\xFF\xFF'
        # 数据长度
        answer += struct.pack('B', len(data) + 10)
        # 固定格式
        answer += b'\x00\x00\x00\x00\x00\x01'
        # 固定字节02
        answer += b'\x02'
        # 控制字
        answer += '\x6D\x01'
        # 数据
        answer += data
        # CRC
        answer += crc(answer[2:])
        return answer

    def update_msg_statistics(self, data):
        self.msg_statistics[data] += 1

    def get_msg_msg_statistics(self):
        return self.msg_statistics

    def show_state(self):
        # 当前温度 1word
        if self.WORDA_get_bit(5):
            temp1 = struct.unpack('BB', self._TEMP)
            temp2 = temp1[0] * 256 + temp1[1] + 16 + 0.5
        else:
            temp1 = struct.unpack('BB', self._TEMP)
            temp2 = temp1[0] * 256 + temp1[1] + 16
        self.LOG.warn("当前温度".decode(
            'utf-8').encode(sys.getfilesystemencoding()) + ': %0.1f' % (temp2))

        # 设定温度 1word
        if self.WORDA_get_bit(5):
            temp1 = struct.unpack('BB', self._STEMP)
            temp2 = temp1[0] * 256 + temp1[1] + 16 + 0.5
        else:
            temp1 = struct.unpack('BB', self._STEMP)
            temp2 = temp1[0] * 256 + temp1[1] + 16
        self.LOG.warn("设定温度".decode(
            'utf-8').encode(sys.getfilesystemencoding()) + ': %0.1f' % (temp2))

        # 模式 1word 0000 ~ 0004
        temp = struct.unpack('BB', self._MODE)
        mode = {
            0: '自动',
            1: '制冷',
            2: '制热',
            3: '送风',
            4: '除湿'
        }
        self.LOG.warn("模式".decode('utf-8').encode(sys.getfilesystemencoding()) +
                      ': %s' % (mode[temp[1]].decode('utf-8').encode(sys.getfilesystemencoding())))

        # 风速 1word 0000 ~ 0003
        temp = struct.unpack('BB', self._WIND)
        wind = {
            0: '高风',
            1: '中风',
            2: '低风',
            3: '自动',
        }
        self.LOG.warn("风速".decode('utf-8').encode(sys.getfilesystemencoding()) +
                      ': %s' % (wind[temp[1]].decode('utf-8').encode(sys.getfilesystemencoding())))

        # 立体送风 1word
        # SOLIDH0:表示字SOLIDH的第0位，为“0”时，表示无“上下摆风”
        #                           为“1”时，表示有“上下摆风”
        # SOLIDH1:表示字SOLIDH的第1位，为“0”时，表示无“左右摆风”
        #                           为“1”时，表示有“左右摆风”
        #self._SOLLDH = b'\x00\x00'
        if self.bit_get(self._SOLLDH, 0):
            mode = '有'
        else:
            mode = '无'
        self.LOG.warn("上下摆风".decode('utf-8').encode(sys.getfilesystemencoding()) +
                      ': %s' % (mode.decode('utf-8').encode(sys.getfilesystemencoding())))
        if self.bit_get(self._SOLLDH, 1):
            mode = '有'
        else:
            mode = '无'
        self.LOG.warn("左右摆风".decode('utf-8').encode(sys.getfilesystemencoding()) +
                      ': %s' % (mode.decode('utf-8').encode(sys.getfilesystemencoding())))

    def protocol_data_washer(self, data):
        data_list = []
        left_data = ''

        while data[0] != b'\xff' and len(data) >= self.min_length:
            self.LOG.warn('give up dirty data: %02x' % ord(data[0]))
            data = data[1:]

        if len(data) < 13:
            left_data = data
        else:
            if data[0] == b'\xff' and data[1] == b'\xff':
                length = struct.unpack('>B', data[2])[0]
                # min length is 10
                if length >= 10 and length <= len(data[3:]):
                    #data_list.append(struct.unpack('%ds' % (length), data[3:])[0])
                    data_list.append(data[0:3 + length])
                    data = data[3 + length:]
                    if data:
                        data_list_tmp, left_data_tmp = self.protocol_data_washer(
                            data)
                        data_list += data_list_tmp
                        left_data += left_data_tmp
                elif length >= 10:
                    left_data = data
                else:
                    for s in data[:3]:
                        self.LOG.warn('give up dirty data: %02x' % ord(s))
                    left_data = data[3:]

        return data_list, left_data

    def protocol_handler(self, msg):
        # 查询
        if msg[10:12] == b'\x4d\x01':
            self.LOG.debug("查询命令".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            # too much such msg, ignore it
            return self.msg_build()
            pass

        # 开机
        elif msg[10:12] == b'\x4d\x02':
            self.LOG.warn("开机".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_set_bit(0)
            return self.msg_build()

        # 关机
        elif msg[10:12] == b'\x4d\x03':
            self.LOG.warn("关机".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_clear_bit(0)
            return self.msg_build()

        # 电加热 无
        elif msg[10:12] == b'\x4d\x04':
            self.LOG.warn("电加热 无".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_clear_bit(1)
            return self.msg_build()

        # 电加热 有
        elif msg[10:12] == b'\x4d\x05':
            self.LOG.warn("电加热 有".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_set_bit(1)
            return self.msg_build()

        # 健康 无
        elif msg[10:12] == b'\x4d\x08':
            self.LOG.warn("健康 无".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_clear_bit(3)
            return self.msg_build()

        # 健康 有
        elif msg[10:12] == b'\x4d\x09':
            self.LOG.warn("健康 有".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_set_bit(3)
            return self.msg_build()

        # 设定温度
        elif msg[10:12] == b'\x5d\x01':
            self.TEMP_set(msg[12:14], ifprint=1)
            return self.msg_build()

        # 电子锁 无
        elif msg[10:12] == b'\x4d\x18':
            self.LOG.warn("电子锁 无".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_clear_bit(15)
            return self.msg_build()

        # 电子锁 有
        elif msg[10:12] == b'\x4d\x19':
            self.LOG.warn("电子锁 有".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_set_bit(15)
            return self.msg_build()

        # 换新风 无
        elif msg[10:12] == b'\x4d\x1e':
            self.LOG.warn("换新风 无".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDB_clear_bit(0)
            return self.msg_build()

        # 换新风 有
        elif msg[10:12] == b'\x4d\x1f':
            self.LOG.warn("换新风 有".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDB_set_bit(0)
            return self.msg_build()

        # 加湿 无
        elif msg[10:12] == b'\x4d\x1c':
            self.LOG.warn("加湿 无".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_clear_bit(6)
            return self.msg_build()

        # 加湿 有
        elif msg[10:12] == b'\x4d\x1d':
            self.LOG.warn("加湿 有".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_set_bit(6)
            return self.msg_build()

        # 上下摆风
        elif msg[10:12] == b'\x4d\x22':
            if msg[12:14] == b'\x00\x01':
                self.LOG.warn("上下摆风 有".decode(
                    'utf-8').encode(sys.getfilesystemencoding()))
            else:
                self.LOG.warn("上下摆风 无".decode(
                    'utf-8').encode(sys.getfilesystemencoding()))
            self.SOLLDH_set(UD_data=msg[12:14])
            return self.msg_build()

        # 左右摆风
        elif msg[10:12] == b'\x4d\x23':
            if msg[12:14] == b'\x00\x01':
                self.LOG.warn("左右摆风 有".decode(
                    'utf-8').encode(sys.getfilesystemencoding()))
            else:
                self.LOG.warn("左右摆风 无".decode(
                    'utf-8').encode(sys.getfilesystemencoding()))
            self.SOLLDH_set(LR_data=msg[12:14])
            return self.msg_build()

        # 上下左右摆风
        elif msg[10:12] == b'\x4d\x24':
            if msg[12:14] == b'\x00\x01':
                self.LOG.warn("全摆风 有".decode(
                    'utf-8').encode(sys.getfilesystemencoding()))
            else:
                self.LOG.warn("全摆风 无".decode(
                    'utf-8').encode(sys.getfilesystemencoding()))
            self.SOLLDH_set(UD_data=msg[12:14], LR_data=msg[12:14])
            return self.msg_build()

        # 自清洁 无
        # elif msg[10:12] == b'\x4d\x1c':
        #    self.LOG.warn("自清洁 无".decode('utf-8').encode(sys.getfilesystemencoding()))
        #    self.WORDA_clear_bit(6)
        #    return self.msg_build()

        # 自清洁 有
        elif msg[10:12] == b'\x4d\x26':
            self.LOG.warn("自清洁 有".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_set_bit(2)
            return self.msg_build()

        # 感人功能 无
        elif msg[10:12] == b'\x4d\x28':
            self.LOG.warn("感人功能 无".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_clear_bit(12)
            return self.msg_build()

        # 感人功能 有
        elif msg[10:12] == b'\x4d\x27':
            self.LOG.warn("感人功能 有".decode(
                'utf-8').encode(sys.getfilesystemencoding()))
            self.WORDA_set_bit(12)
            return self.msg_build()

        # 风速
        elif msg[10:12] == b'\x5d\x07':
            self.WIND_set(msg[12:14], ifprint=1)
            return self.msg_build()

        # 模式
        elif msg[10:12] == b'\x5d\x08':
            self.MODE_set(msg[12:14], ifprint=1)
            return self.msg_build()

        # 健康除湿湿度
        elif msg[10:12] == b'\x4d\x0d':
            self.HUMSD_set(msg[12:14], ifprint=1)
            return self.msg_build()

        # 组控制命令
        # TODO， 模块暂时不支持

        # others
        else:
            self.LOG.error(protocol_data_printB(
                msg, title='%s: invalid data:'))
            return self.msg_build()

    @common_APIs.need_add_lock(state_lock)
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


if __name__ == '__main__':
    print(protocol_data_printB(msg, title='see see'))
