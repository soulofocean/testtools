#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATS socket
   by Kobe Gong. 2017-9-29
"""

import datetime
import os
import random
import re
import select
import socket
import sys
import threading
import time

import APIs.common_APIs as common_APIs
from APIs.common_APIs import protocol_data_printB
from basic.log_tool import MyLogger

try:
    import queue as Queue
except:
    import Queue
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

BUFF_SIZE = 512


class MyServer:
    def __init__(self, addr, logger, debug=False, singlethread=True, printB=True):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(False)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(addr)
        server.listen(10000)
        self.server = server

        self.LOG = logger
        self.debug = debug
        self.singlethread = singlethread
        self.printB = printB

        # comm data
        self.clients = {}
        self.inputs = [server]
        self.conn_to_addr = {}

    def get_client_count(self):
        return len(self.clients)

    def run_forever(self, *arg):
        BUFF_SIZE = 1024
        timeout = 1

        try:
            while True:
                if self.debug:
                    self.LOG.debug(
                        "Waiting for next event, now has active clients: %d" % (len(self.clients)))
                readable, writable, exceptional = select.select(
                    self.inputs, [], [], timeout)
                for conn in readable:
                    if conn == self.server:
                        try:
                            connection, client_address = self.server.accept()
                            connection.setblocking(0)
                            self.LOG.info(
                                "Get connection from: " + client_address[0])
                            self.clients[client_address] = {
                                'conn': connection,
                                'queue_in': Queue.Queue(),
                                'queue_out': Queue.Queue(),
                            }
                            self.inputs.append(connection)
                            self.conn_to_addr[connection] = client_address

                        except Exception as e:
                            self.LOG.error("Get connection %s falied![%s]" % (
                                client_address[0], e))
                            pass

                    else:
                        try:
                            data = conn.recv(BUFF_SIZE)
                            if data:
                                self.clients[self.conn_to_addr[conn]
                                             ]['queue_in'].put(data)

                                dmsg = b'\x48\x44\x58\x4d\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x01\x00\x00\x00\x01\x00\x00\x00\x29\x00\x00\x8f\x20\x7b\x22\x52\x65\x73\x75\x6c\x74\x22\x3a\x30\x2c\x22\x43\x6f\x6d\x6d\x61\x6e\x64\x22\x3a\x22\x43\x4f\x4d\x5f\x44\x45\x56\x5f\x52\x45\x47\x49\x53\x54\x45\x52\x22\x7d'

                                self.clients[self.conn_to_addr[conn]
                                             ]['queue_out'].put(dmsg)

                                if isinstance(data, type(b'')):
                                    tmp_data = data
                                else:
                                    tmp_data = data.encode('utf-8')

                                if self.debug:
                                    if self.printB:
                                        self.LOG.info(protocol_data_printB(
                                            tmp_data, title="Get data from " + self.conn_to_addr[conn][0] + ":"))
                                    else:
                                        self.LOG.info(
                                            "Get data from " + self.conn_to_addr[conn][0] + ": " + tmp_data.decode('utf-8'))
                            else:
                                # Interpret empty result as closed connection
                                self.LOG.error(
                                    self.conn_to_addr[conn][0] + ' closed!')
                                self.clients[self.conn_to_addr[conn]
                                             ]['conn'].close()
                                self.inputs.remove(conn)
                                del self.clients[self.conn_to_addr[conn]]
                                del self.conn_to_addr[conn]

                        except socket.error:
                            self.LOG.error("Get data from %s falied!" %
                                           (self.conn_to_addr[conn][0]))
                            self.clients[self.conn_to_addr[conn]
                                         ]['conn'].close()
                            self.inputs.remove(conn)
                            del self.clients[self.conn_to_addr[conn]]
                            del self.conn_to_addr[conn]

                if self.singlethread:
                    self.send_once()

        except KeyboardInterrupt:
            self.LOG.info(
                'KeyboardInterrupt, now to close all clinets and server!')
            for client in self.clients:
                self.clients[client]['conn'].close()
            self.server.close()

        except Exception as e:
            self.LOG.error(str(e))
            for client in self.clients:
                self.clients[client]['conn'].close()
            self.server.close()

        finally:
            self.LOG.info("socket server end!")
            sys.exit(0)

    def sendloop(self, *arg):
        while True:
            self.send_once()

    def send_once(self):
        try:
            for client in self.conn_to_addr:
                if self.clients[self.conn_to_addr[client]]['queue_out'].empty():
                    pass
                else:
                    data = self.clients[self.conn_to_addr[client]
                                        ]['queue_out'].get()
                    if isinstance(data, type(b'')):
                        tmp_data = data
                    else:
                        tmp_data = data.encode('utf-8')
                    if self.debug:
                        if self.printB:
                            self.LOG.yinfo(protocol_data_printB(
                                tmp_data, title="Send data to " + self.conn_to_addr[client][0] + ":"))
                        else:
                            self.LOG.yinfo(
                                "Send data to " + self.conn_to_addr[client][0] + ": " + tmp_data.decode('utf-8'))
                    client.send(tmp_data)

        except Exception as e:
            self.LOG.error(
                self.conn_to_addr[client][0] + ' closed! [%s]' % (str(e)))
            self.clients[self.conn_to_addr[client]]['conn'].close()
            self.inputs.remove(client)
            del self.clients[self.conn_to_addr[client]]
            del self.conn_to_addr[client]


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
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def get_connected(self):
        return self.connected

    @common_APIs.need_add_lock(state_lock)
    def set_connected(self, value):
        self.connected = value

    @common_APIs.need_add_lock(conn_lock)
    def connect(self):
        if self.self_addr and self.binded == False:
            # self.client.setblocking(False)
            #self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client.bind(self.self_addr)
            self.binded = True

        self.inputs = [self.client]
        try:
            self.client.connect(self.addr)
            self.LOG.info("Connection setup suceess!")
            self.set_connected(True)
            return True

        except Exception as e:
            self.LOG.warn("Connect to server failed[%s], wait 1s..." % (e))
            sys.exit()
            return False

    def close(self):
        return self.client.close()

    def recv_once(self, timeout=1):
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
                data = self.client.recv(BUFF_SIZE)
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
