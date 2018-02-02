#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""air app sim
by Kobe Gong. 2017-10-16
"""

import argparse
import ConfigParser
import datetime
import decimal
import json
import logging
import os
import Queue
import random
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from cmd import Cmd
from collections import defaultdict

import APIs.common_APIs as common_APIs
import connections.my_socket as my_socket
from APIs.common_APIs import (my_system, my_system_full_output,
                              my_system_no_check, protocol_data_printB)
from basic.cprint import cprint
from basic.log_tool import MyLogger
from protocol.protocol_process import communication_base

# 命令行参数梳理，-t time interval; -u uuid


class ArgHandle():
    def __init__(self):
        self.parser = self.build_option_parser("-" * 50)

    def build_option_parser(self, description):
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument(
            '-t', '--time-interval',
            dest='time_interval',
            action='store',
            default=200,
            type=int,
            help='time intervavl for msg send to router',
        )
        parser.add_argument(
            '--t2',
            dest='t2',
            action='store',
            default=10,
            type=int,
            help='time intervavl for msg send to each device',
        )
        parser.add_argument(
            '-u', '--device-uuid',
            dest='device_uuid',
            action='store',
            help='Specify device uuid',
        )
        parser.add_argument(
            '-f',
            dest='uuids_file',
            action='store',
            help='Specify device uuids',
        )
        parser.add_argument(
            '-c', '--send package number',
            dest='number_to_send',
            action='store',
            default=5000,
            type=int,
            help='Specify how many package to send',
        )
        parser.add_argument(
            '--password',
            dest='router_password',
            action='store',
            default='123456',
            help='Specify password to login router',
        )
        parser.add_argument(
            '--user',
            dest='router_username',
            action='store',
            default='13311223344',
            help='Specify user to login router',
        )
        parser.add_argument(
            '--device',
            dest='device_type',
            action='store',
            choices={'air', 'led', 'switch'},
            default='air',
            help="Specify device type: 'air', 'led', 'switch'",
        )
        return parser

    def get_args(self, attrname):
        return getattr(self.args, attrname)

    def check_args(self):
        if arg_handle.get_args('device_uuid') or arg_handle.get_args('uuids_file'):
            global uuids
            uuids = []
            if arg_handle.get_args('device_uuid'):
                uuids.append(arg_handle.get_args('device_uuid'))
            else:
                with open(arg_handle.get_args('uuids_file')) as f:
                    for line in f:
                        if line.strip():
                            uuids.append(line.strip())
            for uuid in uuids:
                LOG.info('uuid: %s is given.' % uuid)
        else:
            cprint.error_p("-f or -u should be give!")
            sys.exit()

    def run(self):
        self.args = self.parser.parse_args()
        cprint.notice_p("CMD line: " + str(self.args))
        self.check_args()


# CMD loop, 可以查看各个串口的消息统计
class MyCmd(Cmd):
    def __init__(self, coms_list):
        Cmd.__init__(self)
        self.prompt = "AIR>"
        self.coms_list = coms_list

    def help_sts(self):
        cprint.notice_p("show all msgs info!")

    def do_sts(self, arg, opts=None):
        pass

    def default(self, arg, opts=None):
        try:
            subprocess.call(arg, shell=True)
        except:
            pass

    def emptyline(self):
        pass

    def help_exit(self):
        print("Will exit")

    def do_exit(self, arg, opts=None):
        cprint.notice_p("Exit CLI, good luck!")
        sys_cleanup()
        sys.exit()


# 系统调度
def sys_proc(action="default"):
    global thread_ids
    thread_ids = []
    for th in thread_list:
        thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

    for th in thread_ids:
        th.setDaemon(True)
        th.start()
        # time.sleep(0.1)


def sys_join():
    for th in thread_ids:
        th.join()


# 系统初始化函数，在所有模块开始前调用
def sys_init():
    LOG.info("Let's go!!!")


# 系统清理函数，系统退出前调用
def sys_cleanup():
    LOG.info("Goodbye!!!")


def login_router(phone, password):
    msg = {
        "uuid": "111",
        "encry": "false",
        "content": {
            "method": "um_login_pwd",
            "timestamp": 12345667,
            "req_id": 123,
            "params": {
                "phone": phone,
                "pwd": password,
                "os_type": "Android",
                "app_version": "v0.5",
                "os_version": "android4.3",
                "hardware_version": "Huawei"
            }
        }
    }
    return str(json.dumps(msg)) + '\n'


def temperature_set_msg(req_id, uuid, *args):
    temperature = random.randint(17, 30)
    msg_temp_up = {
        "uuid": "111",
        "encry": "false",
        "content": {
            "method": "dm_set",
            "req_id": 113468,
            "token": "",
            "nodeid": "airconditioner.main.temperature",
            "params": {
                "device_uuid": "",
                "attribute": {
                    "temperature": temperature
                }
            }
        }
    }
    msg_temp_up['content']['req_id'] = req_id
    msg_temp_up['content']['params']['device_uuid'] = uuid
    return json.dumps(msg_temp_up) + '\n'


def led_control_msg(req_id, uuid, on_off, family_id=1, user_id=1):
    msg = {
        "uuid": "111",
        "encry": "false",
        "content": {
            "method": "dm_set",
            "req_id": req_id,
            "timestamp": 123456789,
            "nodeid": "bulb.main.switch",
            "params": {
                "family_id": family_id,
                "user_id": user_id,
                "device_uuid": uuid,
                "attribute": {
                    "switch": on_off
                }
            }
        }
    }
    return json.dumps(msg) + '\n'


def switch_control_msg(req_id, uuid, on_off, family_id=1, user_id=1):
    msg = {
        "uuid": "111",
        "encry": "false",
        "content": {
            "method": "dm_set",
            "req_id": req_id,
            "timestamp": 123456789,
            "nodeid": "switch.main.switch",
            "params": {
                "family_id": family_id,
                "user_id": user_id,
                "device_uuid": uuid,
                "attribute": {
                    "switch_chan0": on_off,
                    "switch_chan1": on_off,
                    "switch_chan2": on_off,
                }
            }
        }
    }
    return json.dumps(msg) + '\n'


class AirControl(communication_base):
    state_lock = threading.Lock()

    def __init__(self, addr, logger):
        self.queue_in = Queue.Queue()
        self.queue_out = Queue.Queue()
        super(AirControl, self).__init__(self.queue_in, self.queue_out,
                                         logger=logger, left_data='', min_length=10)
        self.addr = addr
        self.name = 'AirControl'
        self.connection = my_socket.MyClient(
            addr, logger, debug=False, printB=False)
        self.state = 'close'

        # state data:
        self.msgst = defaultdict(lambda: {})

    def protocol_handler(self, msg):
        self.LOG.yinfo('recv: ' + str(msg))
        json_msg = json.loads(msg)
        if ((not 'content' in json_msg)
            or (not 'req_id' in json_msg['content'])
            or (json_msg['content']['method'] == 'um_login_pwd')
            or (json_msg['content']['method'] == 'mdp_msg')
                or not (json_msg['content']['req_id']) in self.msgst):
            return 'No_need_send'

        rece_time = datetime.datetime.now()
        time_diff = (
            rece_time - self.msgst[json_msg['content']['req_id']]['send_time'])
        self.msgst[json_msg['content']['req_id']]['delaytime'] = time_diff.seconds * \
            1000.0 + (time_diff.microseconds / 1000.0)

        if(self.msgst[json_msg['content']['req_id']]['delaytime'] >= 1000):
            self.LOG.error("msg intervavl for %s is too long: %s\n" % (
                json_msg['content']['req_id'], self.msgst[json_msg['content']['req_id']]['delaytime']))
            return 'No_need_send'
        else:
            self.LOG.warn('msg intervavl for %s is %f\n' % (
                json_msg['content']['req_id'], self.msgst[json_msg['content']['req_id']]['delaytime']))
            return 'No_need_send'

    def protocol_data_washer(self, data):
        data_list = []
        left_data = ''

        if data.endswith('\n'):
            data_list = data.strip().split('\n')
        elif re.search(r'\n', data, re.S):
            data_list = data.split('\n')
            left_data = data_list[-1]
            data_list = data_list[:-1]

        else:
            left_data = data

        if len(data_list) > 1 or left_data:
            pass
            # self.LOG.warn('packet splicing')
        return data_list, left_data

    @common_APIs.need_add_lock(state_lock)
    def connection_setup(self):
        self.LOG.warn('Try to connect %s...' % str(self.addr))
        if self.connection.get_connected():
            self.LOG.info('Connection already setup!')
            return True
        elif self.connection.connect():
            self.set_connection_state(True)
            self.LOG.info('Setup connection success!')
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
        return self.connection.send_once(data)

    def recv_data(self):
        datas = self.connection.recv_once()
        return datas


# 空调遥控器模拟程序入口
if __name__ == '__main__':
    # sys log init
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace(
        'py', 'log'), clevel=logging.INFO, renable=False)

    cprint = cprint(os.path.abspath(sys.argv[0]).replace('py', 'log'))

    # cmd arg init
    arg_handle = ArgHandle()
    arg_handle.run()

    # sys init
    sys_init()

    # multi thread
    global thread_list
    thread_list = []

    app = AirControl(('192.168.10.1', 5100), logger=LOG)
    thread_list.append([app.schedule_loop])
    thread_list.append([app.send_data_loop])
    thread_list.append([app.recv_data_loop])

    # run threads
    sys_proc()

    try:
        while app.connection.get_connected() != True:
            pass
        msg = login_router(arg_handle.get_args('router_username'), common_APIs.get_md5(
            arg_handle.get_args('router_password')))
        LOG.info("To login router: " + msg.strip())
        app.queue_out.put(msg)
        time.sleep(1)

        if arg_handle.get_args('device_type') == 'air':
            for i in range(arg_handle.get_args('number_to_send')):
                j = 100000
                req_id = i + 88000000
                for uuid in uuids:
                    req_id += j
                    j += 1
                    msg = temperature_set_msg(req_id, uuid)
                    app.msgst[req_id]['send_time'] = datetime.datetime.now()
                    app.queue_out.put(msg)
                    LOG.info("send: " + msg.strip())
                    time.sleep(arg_handle.get_args('t2') / 1000.0)

                time.sleep(arg_handle.get_args('time_interval') / 1000.0)

        elif arg_handle.get_args('device_type') == 'led':
            for i in range(arg_handle.get_args('number_to_send')):
                j = 100000
                req_id = i + 88000000
                for uuid in uuids:
                    req_id += j
                    j += 1
                    msg = led_control_msg(req_id, uuid, 'on')
                    app.queue_out.put(msg)
                    app.msgst[req_id]['send_time'] = datetime.datetime.now()
                    app.queue_out.put(msg)
                    LOG.info("send: " + msg.strip())
                    time.sleep(arg_handle.get_args('t2') / 1000.0)
                time.sleep(arg_handle.get_args('time_interval') / 1000.0)

                j = 100000
                req_id = i + 99000000
                for uuid in uuids:
                    req_id += j
                    j += 1
                    msg = led_control_msg(req_id, uuid, 'off')
                    app.queue_out.put(msg)
                    app.msgst[req_id]['send_time'] = datetime.datetime.now()
                    app.queue_out.put(msg)
                    LOG.info("send: " + msg.strip())
                    time.sleep(arg_handle.get_args('t2') / 1000.0)
                time.sleep(arg_handle.get_args('time_interval') / 1000.0)

        elif arg_handle.get_args('device_type') == 'switch':
            for i in range(arg_handle.get_args('number_to_send')):
                j = 100000
                req_id = i + 88000000
                for uuid in uuids:
                    req_id += j
                    j += 1
                    msg = switch_control_msg(req_id, uuid, 'on')
                    app.queue_out.put(msg)
                    app.msgst[req_id]['send_time'] = datetime.datetime.now()
                    app.queue_out.put(msg)
                    LOG.info("send: " + msg.strip())
                    time.sleep(arg_handle.get_args('t2') / 1000.0)
                time.sleep(arg_handle.get_args('time_interval') / 1000.0)

                j = 100000
                req_id = i + 99000000
                for uuid in uuids:
                    req_id += j
                    j += 1
                    msg = switch_control_msg(req_id, uuid, 'off')
                    app.queue_out.put(msg)
                    app.msgst[req_id]['send_time'] = datetime.datetime.now()
                    app.queue_out.put(msg)
                    LOG.info("send: " + msg.strip())
                    time.sleep(arg_handle.get_args('t2') / 1000.0)
                time.sleep(arg_handle.get_args('time_interval') / 1000.0)

        else:
            LOG.error('Not support device!')

        while not app.queue_out.empty():
            time.sleep(1)
        time.sleep(5)

        pkg_lost = 0
        pkg_lost_list = []
        min_delay = 8888888888
        max_delay = 0
        total_delay = 0
        for item in app.msgst:
            if 'delaytime' in app.msgst[item]:
                if app.msgst[item]['delaytime'] > max_delay:
                    max_delay = app.msgst[item]['delaytime']
                if app.msgst[item]['delaytime'] < min_delay:
                    min_delay = app.msgst[item]['delaytime']
                total_delay += app.msgst[item]['delaytime']
            else:
                pkg_lost += 1
                pkg_lost_list.append(item)

        LOG.info('Total package: %d' % len(app.msgst))
        if pkg_lost_list:
            LOG.error('Package with these ids have lost:')
            for i in pkg_lost_list:
                LOG.warn('%d' % i)
        LOG.error('Loss Rate: ' + "%.2f" % (pkg_lost * 100.0 /
                                            arg_handle.get_args('number_to_send')) + '%')
        LOG.info('MAX delay time: %dms' % max_delay)
        LOG.yinfo('MIN delay time: %dms' % min_delay)
        LOG.info('Average delay time(%d / %d): %.2fms' % (total_delay, (len(app.msgst) -
                                                                        pkg_lost), (total_delay + 0.0) / (len(app.msgst) - pkg_lost)))

    except KeyboardInterrupt:
        LOG.info('KeyboardInterrupt!')
        sys.exit()

    except Exception as e:
        LOG.error('something wrong!' + str(e))
        sys.exit()
