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
import re
import struct
import sys
import threading
import time
from abc import ABCMeta, abstractmethod
from collections import defaultdict

import APIs.common_APIs as common_APIs
from APIs.common_APIs import protocol_data_printB

try:
    import queue as Queue
except:
    import Queue


if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class communication_base(object):
    send_lock = threading.Lock()

    def __init__(self, queue_in, queue_out, logger, left_data=b'', min_length=10):
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.LOG = logger
        self.left_data = left_data
        self.min_length = min_length
        self.connection = ''
        self.name = 'some guy'
        self.heartbeat_interval = 3
        self.heartbeat_data = None
        self.need_stop = False

    @abstractmethod
    def protocol_handler(self, msg):
        pass

    @abstractmethod
    def protocol_data_washer(self, data):
        pass

    def run_forever(self):
        thread_list = []
        thread_list.append([self.schedule_loop])
        thread_list.append([self.send_data_loop])
        thread_list.append([self.recv_data_loop])
        # thread_list.append([self.heartbeat_loop])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    @abstractmethod
    def msg_build(self):
        pass

    @abstractmethod
    def connection_setup(self):
        pass

    @abstractmethod
    def connection_close(self):
        pass

    def get_connection_state(self):
        return self.connection.get_connected()

    def set_connection_state(self, new_state):
        self.connection.set_connected(new_state)

    @abstractmethod
    def send_data(self, data):
        pass

    @abstractmethod
    def recv_data(self, data):
        pass

    @common_APIs.need_add_lock(send_lock)
    def add_send_data(self, data):
        self.queue_out.put(data)

    @common_APIs.need_add_lock(send_lock)
    def send_data_once(self, data=None):
        if data:
            self.queue_out.put(data)
        if self.queue_out.empty():
            pass
        else:
            while not self.queue_out.empty():
                data = self.queue_out.get()
                self.send_data(data)

    def recv_data_once(self):
        #datas = ''
        #data = self.recv_data()
        # while data:
        #    datas += data
        #    data = self.recv_data()
        datas = self.recv_data()
        if datas:
            self.queue_in.put(datas)
        return datas

    def send_data_loop(self):
        while self.need_stop == False:
            if self.get_connection_state():
                pass
            else:
                if self.connection_setup():
                    pass
                else:
                    time.sleep(1)
                    continue
            self.send_data_once()

    def recv_data_loop(self):
        while self.need_stop == False:
            if self.get_connection_state():
                pass
            else:
                if self.connection_setup():
                    pass
                else:
                    time.sleep(1)
                    continue
            self.recv_data_once()

    def heartbeat_loop(self):
        while self.need_stop == False:
            if self.get_connection_state():
                data = self.heartbeat_data
                if not data:
                    self.LOG.debug('No need control heartbeat, I am out!')
                    sys.exit()

                if isinstance(data, type(b'')):
                    tmp_data = data.decode('utf-8')
                else:
                    tmp_data = data
                self.LOG.yinfo("send msg: " + tmp_data)
                self.send_data_once(data=data)
            else:
                self.LOG.debug('offline?')
            time.sleep(self.heartbeat_interval)

    def schedule_loop(self):
        while self.need_stop == False:
            if self.queue_in.empty():
                continue
            else:
                ori_data = self.left_data + self.queue_in.get()
                while len(ori_data) < self.min_length:
                    ori_data += self.queue_in.get()
                data_list, self.left_data = self.protocol_data_washer(ori_data)
                if data_list:
                    for request_msg in data_list:
                        response_msg = self.protocol_handler(request_msg)
                        if response_msg == 'No_need_send':
                            pass
                        elif response_msg:
                            self.queue_out.put(response_msg)
                        else:
                            self.LOG.error(protocol_data_printB(
                                request_msg, title='%s: got invalid data:' % (self.name)))
                else:
                    continue

    def stop(self):
        self.need_stop = True
        self.LOG.warn('Thread %s stoped!' % (__name__))

    def convert_to_dictstr(self, src):
        if isinstance(src, dict):
            return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        elif isinstance(src, str):
            return json.dumps(json.loads(src), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        elif isinstance(src, bytes):
            return json.dumps(json.loads(src.decode('utf-8')), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        else:
            self.LOG.error('Unknow type(%s): %s' % (src, str(type(src))))
            return None


if __name__ == '__main__':
    p = PProcess(None)
