#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""serial module
by Kobe Gong. 2017-9-11
"""

import datetime
import logging
import os
import re
import sys
import time
from abc import ABCMeta, abstractmethod

import serial
import serial.tools.list_ports

# serial comm class


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


class Robot():
    def __init__(self, port=None, baudrate=115200, logger=None):
        self.LOG = logger
        self.port = port
        self.baudrate = baudrate
        self.serial = MySerial(
            port=self.port, baudrate=self.baudrate, logger=self.LOG)

    def open(self, ):
        self.LOG.debug('To open robot...')
        if not self.serial.is_open():
            self.serial.open()
            self.serial.read()
        # self.serial.write('O')
        # self.serial.read()
        self.serial.close()

    def close(self, ):
        self.LOG.debug('To close robot...')
        if not self.serial.is_open():
            self.serial.open()
            self.serial.read()
        self.serial.write('C')
        self.serial.read()
        self.serial.close()

    def led_access_net(self, open_close_time=6):
        return
        for i in range(open_close_time):
            self.open()
            time.sleep(1.5)


class Wifi():
    def __init__(self, port=None, baudrate=115200, logger=None):
        self.LOG = logger
        self.port = port
        self.baudrate = baudrate
        # self.serial = MySerial(
        #    port=self.port, baudrate=self.baudrate, logger=self.LOG)

    def wifi_access_net(self, open_close_time=6):
        return
        if not self.serial.is_open():
            self.serial.open()
        self.serial.send('clrcfg')
        self.serial.send('reboot')

    def wifi_close(self):
        return
        if self.serial.is_open():
            self.serial.close()
