#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-5'
"""
import serial
import socket
import select
from BasicCommon import *

class MySerial():
    def __init__(self, port=None, baudrate=9600, logger=None, user='root', password='hdiotwzb100'):
        self.LOG = logger
        self.port = port
        self.baudrate = baudrate
        self.com = None
        self.user = user
        self.password = password
        self.connected = False

    def get_connected(self):
        return self.connected

    #@common_APIs.need_add_lock(state_lock)
    def set_connected(self, value):
        self.connected = value

    def get_available_ports(self):
        port_list = list(serial.tools.list_ports.comports())
        r_port_list = []

        if len(port_list) <= 0:
            #self.LOG.error("Can't find any serial port!")
            pass
        else:
            for i in range(len(port_list)):
                serial_name = list(port_list[i])[0]
                #self.LOG.debug("Get serial port: %s" % (serial_name))
                r_port_list.append(serial_name)

        return r_port_list

    def open(self, need_retry=False):
        port_list = self.get_available_ports()
        if self.port in port_list:
            pass
        elif self.port == 'any' and port_list:
            self.port = port_list[0]
        else:
            self.LOG.error("Can't find port: %s!" % self.port)
            return False

        try:
            self.com = serial.Serial(
                self.port, baudrate=self.baudrate, timeout=1)
            if self.is_open():
                if need_retry:
                    for i in range(5):
                        self.write('\n')
                        a = self.readlines()
                        self.LOG.debug(str(a))
                        if re.search('root@OpenWrt:~# ', str(a)):
                            break
                        elif re.search('OpenWrt login: ', str(a)):
                            self.send(self.user)
                            a = self.readlines()
                            self.LOG.debug(str(a))
                            self.send(self.password)
                            a = self.readlines()
                            self.LOG.debug(str(a))
                            self.LOG.debug(
                                "port: %s open success" % (self.port))
                            break
                        self.set_connected(True)
            else:
                self.LOG.error("Can't open %s!" % (self.port))
                return False

        except Exception as er:
            self.com = None
            self.LOG.error('Open %s fail!' % (self.port))
            return False
        return True

    def close(self):
        if type(self.com) != type(None):
            self.com.close()
            self.com = None
            return True

        return not self.com.isOpen()

    def is_open(self):
        if self.com:
            return self.com.isOpen()
        else:
            return False

    def readn(self, n=1):
        return self.com.read(n)

    def read(self):
        return self.com.read()

    def readline(self):
        return self.com.readline()

    def readlines(self):
        return self.com.readlines()

    def readall(self):
        return self.com.read_all()

    def read_until(self, prompt):
        ret = self.com.read_until(terminator=prompt)
        self.LOG.yinfo(ret)
        return re.search(r'%s' % (prompt), ret, re.S)

    def readable(self):
        return self.com.readable()

    def send(self, data):
        return self.write(data + '\r')

    def write(self, data):
        return self.com.write(data)

    def timeout_set(self, timeout=100):
        self.com.timeout = timeout

class MyClient:
    state_lock = threading.Lock()
    conn_lock = threading.Lock()

    def __init__(self, addr, logger, self_addr=None, debug=True, printB=True):
        self.client = ''
        self.addr = addr
        self.LOG = logger
        self.self_addr = self_addr
        self.connected = False
        self.debug = debug
        self.printB = printB
        self.binded = False
        self.BUFF_SIZE = 512
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get_connected(self):
        return self.connected

    @need_add_lock(state_lock)
    def set_connected(self, value):
        self.connected = value

    @need_add_lock(conn_lock)
    def connect(self):
        if self.self_addr and self.binded == False:
            # self.client.setblocking(False)
            #self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client.bind(self.self_addr)
            self.LOG.warn("Client bind %s" % str(self.self_addr))
            self.binded = True

        self.inputs = [self.client]
        try:
            code = self.client.connect_ex(self.addr)
            if code == 0:
                self.LOG.info("Connection setup suceess!")
                self.set_connected(True)
                return True
            elif code ==10065:#一般是由于绑定的网卡不可用或者木有连接WIFI
                self.LOG.error("Connect to server failed [code:%s] wait 10s..." % (code))
                if self.binded and self.self_addr:
                    self.LOG.error("May be client bind interface is down binded addr:%s" % str(self.self_addr))
                time.sleep(10)
                return False
            else:#不知道神马情况，遇到再说，先睡一秒
                self.LOG.warn("Connect to server failed other code[code:%s]" % (code))
                time.sleep(1)
                return False
        except Exception as e:
            self.LOG.warn("Connect to server failed[%s], wait 1s..." % (e))
            #TODO, these case should handle the socket.error 9 only, add more code here later...
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # add by zx for add->del->add WIFI sim
            if(self.binded):#保证Socket绑定的网卡不变
                self.binded = False
            #sys.exit()
            return False

    def close(self):
        return self.client.close()

    def recv_once(self, timeout=None):
        try:
            if not self.get_connected():
                return
            data = ''
            readable, writable, exceptional = select.select(
                self.inputs, [], self.inputs, timeout)

            # When timeout reached , select return three empty lists
            if not (readable):
                pass
            else:
                data = self.client.recv(self.BUFF_SIZE)
                if data:
                    if self.debug:
                        if isinstance(data, type(b'')):
                            tmp_data = data
                        else:
                            tmp_data = data.encode('utf-8')
                        if self.printB:
                            self.LOG.info(protocol_data_printB(
                                tmp_data, title="client get data:"))
                        else:
                            self.LOG.info("client get data: %s" %
                                          (tmp_data.decode('utf-8')))

                else:
                    self.LOG.error("Server maybe has closed!")
                    self.client.close()
                    self.inputs.remove(self.client)
                    self.set_connected(False)
            return data

        except socket.error:
            self.LOG.error("socket error, don't know why.")
            self.client.close()
            self.inputs.remove(self.client)
            self.set_connected(False)

    def send_once(self, data=None):
        try:
            if not self.get_connected():
                return
            if isinstance(data, type(b'')):
                tmp_data = data
            else:
                tmp_data = data.encode('utf-8')

            if self.debug:
                if self.printB:
                    self.LOG.yinfo(protocol_data_printB(
                        tmp_data, title="client send date:"))
                else:
                    self.LOG.yinfo("client send data: %s" %
                                   (tmp_data.decode('utf-8')))

            self.client.send(tmp_data)

        except Exception as e:
            self.LOG.error(
                "send data fail, Server maybe has closed![%s]" % (str(e)))
            self.client.close()
            self.inputs.remove(self.client)
            self.set_connected(False)

if __name__ == '__main__':
    pass