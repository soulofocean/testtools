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
from protocol.wifi_protocol import Wifi

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

        # state data:
        self.task_obj = None

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
        thread_list.append([self.sdk_obj.schedule_loop])
        thread_list.append([self.sdk_obj.send_data_loop])
        thread_list.append([self.sdk_obj.recv_data_loop])
        thread_list.append([self.sdk_obj.heartbeat_loop])
        thread_list.append([self.task_obj.task_proc])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def status_maintain(self):
        pass

    def status_report_monitor(self):
        need_send_report = False
        if not hasattr(self, 'old_status'):
            self.old_status = defaultdict(lambda: {})
            for item in self.__dict__:
                if item.startswith('_'):
                    self.LOG.yinfo("need check item: %s" % (item))
                    self.old_status[item] = copy.deepcopy(self.__dict__[item])

        for item in self.old_status:
            if self.old_status[item] != self.__dict__[item]:
                need_send_report = True
                self.old_status[item] = copy.deepcopy(self.__dict__[item])

        if need_send_report:
            self.send_msg(self.get_event_report())


class Air(BaseSim):
    def __init__(self, logger, mac='123456', time_delay=500):
        self.LOG = logger
        self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,
                            mac=mac, deviceCategory='airconditioner.new', self_addr=None)
        self.sdk_obj.sim_obj = self

        # state data:
        self.task_obj = Task('AirSim-task', self.LOG)
        self._switchStatus = 'off'
        self._temperature = 16
        self._mode = "cold"
        self._speed = "low"
        self._wind_up_down = 'off'
        self._wind_left_right = 'off'
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 60)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "switchStatus": self._switchStatus,
                "temperature": self._temperature,
                "mode": self._mode,
                "speed": self._speed,
                "wind_up_down": self._wind_up_down,
                "wind_left_right": self._wind_left_right
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"airconditioner.new.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "switchStatus": self._switchStatus,
                        "temperature": self._temperature,
                        "mode": self._mode,
                        "speed": self._speed,
                        "wind_up_down": self._wind_up_down,
                        "wind_left_right": self._wind_left_right
                    }
                }
                return json.dumps(rsp_msg)
            if msg['nodeid'] == u"airconditioner.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "switchStatus": self._switchStatus,
                        "temperature": self._temperature,
                        "mode": self._mode,
                        "speed": self._speed,
                        "wind_up_down": self._wind_up_down,
                        "wind_left_right": self._wind_left_right
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"airconditioner.main.switch":
                self.LOG.warn(
                    ("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
                self.set_item('_switchStatus',
                              msg['params']["attribute"]["switch"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"airconditioner.main.mode":
                self.LOG.warn(
                    ("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
                self.set_item('_mode', msg['params']["attribute"]["mode"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"airconditioner.main.temperature":
                self.LOG.warn(
                    ("设置温度: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
                self.set_item('_temperature',
                              msg['params']["attribute"]["temperature"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"airconditioner.main.speed":
                self.LOG.warn(
                    ("设置风速: %s" % (msg['params']["attribute"]["speed"])).encode(coding))
                self.set_item('_speed', msg['params']["attribute"]["speed"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"airconditioner.main.wind_up_down":
                self.LOG.warn(
                    ("设置上下摆风: %s" % (msg['params']["attribute"]["wind_up_down"])).encode(coding))
                self.set_item('_wind_up_down',
                              msg['params']["attribute"]["wind_up_down"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"airconditioner.main.wind_left_right":
                self.LOG.warn(
                    ("设置左右摆风: %s" % (msg['params']["attribute"]["wind_left_right"])).encode(coding))
                self.set_item('_wind_left_right',
                              msg['params']["attribute"]["wind_left_right"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')
        else:
            self.LOG.warn('TODO in the feature!')


class Hanger(BaseSim):
    def __init__(self, logger, mac='123456', time_delay=500):
        self.LOG = logger
        self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,
                            mac=mac, deviceCategory='clothes_hanger.main', self_addr=None)
        self.sdk_obj.sim_obj = self

        # state data:
        self.task_obj = Task('HangerSim-task', self.LOG)
        self._status = 'pause'
        self._light = "off"
        self._sterilization = "off"
        self._sterilization_duration = 20
        self._sterilization_remain = 20
        self._drying = "off"
        self._drying_duration = 120
        self._drying_remain = 120
        self._air_drying = 'off'
        self._air_drying_duration = 120
        self._air_drying_remain = 120
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 60)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def status_maintain(self):
        need_send_report = False
        if self._sterilization == 'on':
            need_send_report = True
            if self._sterilization_remain > 0:
                self.set_item('_sterilization_remain',
                              self._sterilization_remain - 1)
                if self._sterilization_remain <= 0:
                    self.set_item('_sterilization', 'off')
            else:
                self.set_item('_sterilization', 'off')

        if self._drying == 'on':
            need_send_report = True
            if self._drying_remain > 0:
                self.set_item('_drying_remain', self._drying_remain - 1)
                if self._drying_remain <= 0:
                    self.set_item('_drying', 'off')
            else:
                self.set_item('_drying', 'off')

        if self._air_drying == 'on':
            need_send_report = True
            if self._air_drying_remain > 0:
                self.set_item('_air_drying_remain',
                              self._air_drying_remain - 1)
                if self._air_drying_remain <= 0:
                    self.set_item('_air_drying', 'off')
            else:
                self.set_item('_air_drying', 'off')

        if need_send_report:
            # self.send_event_report()
            pass

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "light": self._light,
                "sterilization": self._sterilization,
                "drying": self._drying,
                "air_drying": self._air_drying,
                "status": self._status,
                "sterilization_duration": self._sterilization_duration,
                "air_drying_duration": self._air_drying_duration,
                "drying_duration": self._drying_duration,
                "sterilization_remain": self._sterilization_remain,
                "air_drying_remain": self._air_drying_remain,
                "drying_remain": self._drying_remain
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"clothes_hanger.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "light": self._light,
                        "sterilization": self._sterilization,
                        "drying": self._drying,
                        "air_drying": self._air_drying,
                        "status": self._status,
                        "sterilization_duration": self._sterilization_duration,
                        "air_drying_duration": self._air_drying_duration,
                        "drying_duration": self._drying_duration,
                        "sterilization_remain": self._sterilization_remain,
                        "air_drying_remain": self._air_drying_remain,
                        "drying_remain": self._drying_remain
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"clothes_hanger.main.control":
                self.LOG.warn(
                    ("设置上下控制: %s" % (msg['params']["attribute"]["control"])).encode(coding))
                self.set_item('_status', msg['params']["attribute"]["control"])

                if self._status == 'up':
                    self.task_obj.add_task(
                        'change_status_top', self.set_item, 1, 10, '_status', 'top')

                elif self._status == 'down':
                    self.task_obj.add_task(
                        'change_status_bottom', self.set_item, 1, 10, '_status', 'bottom')

                elif self._status == 'pause':
                    self.task_obj.del_task('change_status_top')
                    self.task_obj.del_task('change_status_bottom')

                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"clothes_hanger.main.light":
                self.LOG.warn(
                    ("设置照明: %s" % (msg['params']["attribute"]["light"])).encode(coding))
                self.set_item('_light', msg['params']["attribute"]["light"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"clothes_hanger.main.sterilization":
                self.LOG.warn(
                    ("设置杀菌: %s" % (msg['params']["attribute"]["sterilization"])).encode(coding))
                self.set_item('_sterilization',
                              msg['params']["attribute"]["sterilization"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"clothes_hanger.main.sterilization_duration":
                self.LOG.warn(
                    ("设置杀菌时间: %s" % (msg['params']["attribute"]["sterilization_duration"])).encode(coding))
                self.set_item('_sterilization_duration',
                              msg['params']["attribute"]["sterilization_duration"])
                self.set_item('_sterilization_remain',
                              self._sterilization_duration)
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"clothes_hanger.main.drying":
                self.LOG.warn(
                    ("设置烘干: %s" % (msg['params']["attribute"]["drying"])).encode(coding))
                self.set_item('_drying', msg['params']["attribute"]["drying"])
                if self._drying == 'on':
                    self.set_item('_air_drying', 'off')
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"clothes_hanger.main.drying_duration":
                self.LOG.warn(
                    ("设置烘干时间: %s" % (msg['params']["attribute"]["drying_duration"])).encode(coding))
                self.set_item('_drying_duration',
                              msg['params']["attribute"]["drying_duration"])
                self.set_item('_drying_remain', self._drying_duration)
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"clothes_hanger.main.air_drying":
                self.LOG.warn(
                    ("设置风干: %s" % (msg['params']["attribute"]["air_drying"])).encode(coding))
                self.set_item(
                    '_air_drying', msg['params']["attribute"]["air_drying"])

                if self._air_drying == 'on':
                    self.set_item('_drying', 'off')
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            elif msg['nodeid'] == u"clothes_hanger.main.air_drying_duration":
                self.LOG.warn(
                    ("设置风干时间: %s" % (msg['params']["attribute"]["air_drying_duration"])).encode(coding))
                self.set_item('_air_drying_duration',
                              msg['params']["attribute"]["air_drying_duration"])
                self.set_item('_air_drying_remain', self._air_drying_duration)
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')
        else:
            self.LOG.warn('TODO in the feature!')


class WaterFilter(BaseSim):
    def __init__(self, logger, mac='123456', time_delay=500):
        self.LOG = logger
        self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,
                            mac=mac, deviceCategory='water_filter.main', self_addr=None)
        self.sdk_obj.sim_obj = self

        # state data:
        self.task_obj = Task('WaterFilter-task', self.LOG)
        self._filter_result = {
            "TDS": [
                500,
                100
            ]
        }
        self._status = 'filter'
        self._water_leakage = "off"
        self._water_shortage = "off"
        self._filter_time_used = {
            1: 101,
            2: 202,
        }
        self._filter_time_remaining = {
            1: 1899,
            2: 1798,
        }
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 60)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def reset_filter_time(self, id):
        if int(id) in self._filter_time_used:
            self._filter_time_used[int(id)] = 0
            self._filter_time_remaining[int(id)] = 2000
            return True
        else:
            self.LOG.error('Unknow ID: %s' % (id))
            return False

    def get_filter_time_used(self):
        filter_time_used_list = []
        for id in sorted(self._filter_time_used):
            filter_time_used_list.append(self._filter_time_used[id])
        return filter_time_used_list

    def get_filter_time_remaining(self):
        filter_time_remaining_list = []
        for id in sorted(self._filter_time_remaining):
            filter_time_remaining_list.append(self._filter_time_remaining[id])
        return filter_time_remaining_list

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "filter_result": self._filter_result,
                "status": self._status,
                "water_leakage": self._water_leakage,
                "water_shortage": self._water_shortage,
                "filter_time_used": self.get_filter_time_used(),
                "filter_time_remaining": self.get_filter_time_remaining()
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"water_filter.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "filter_result": self._filter_result,
                        "status": self._status,
                        "water_leakage": self._water_leakage,
                        "water_shortage": self._water_shortage,
                        "filter_time_used": self.get_filter_time_used(),
                        "filter_time_remaining": self.get_filter_time_remaining()
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"water_filter.main.control":
                self.LOG.warn(
                    ("设置冲洗: %s" % (msg['params']["attribute"]["control"])).encode(coding))
                self.set_item('_status', msg['params']["attribute"]["control"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                self.task_obj.add_task(
                    'change WaterFilter to filter', self.set_item, 1, 30, '_status', 'filter')
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"water_filter.main.reset_filter":
                self.LOG.warn(
                    ("复位滤芯: %s" % (msg['params']["attribute"]["reset_filter"])).encode(coding))
                filter_ids = msg['params']["attribute"]["reset_filter"]
                if 0 in filter_ids:
                    filter_ids = self.filter_time_used.keys()
                for filter_id in filter_ids:
                    self.reset_filter_time(filter_id)
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')

        else:
            self.LOG.warn('TODO in the feature!')


class AirFilter(BaseSim):
    def __init__(self, logger, mac='123456', time_delay=500):
        self.LOG = logger
        self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,
                            mac=mac, deviceCategory='air_filter.main', self_addr=None)
        self.sdk_obj.sim_obj = self

        # state data:
        self.task_obj = Task('AirFilter-task', self.LOG)
        self._air_filter_result = {
            "air_quality": [
                "low",
                "high"
            ],
            "PM25": [
                500,
                100
            ]
        }
        self._switch_status = 'off'
        self._child_lock_switch_status = "off"
        self._negative_ion_switch_status = "off"
        self._speed = "low"
        self._control_status = 'auto'
        self._filter_time_used = '101'
        self._filter_time_remaining = '1899'
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 60)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "air_filter_result": self._air_filter_result,
                "switch_status": self._switch_status,
                "child_lock_switch_status": self._child_lock_switch_status,
                "negative_ion_switch_status": self._negative_ion_switch_status,
                "speed": self._speed,
                "control_status": self._control_status,
                "filter_time_used": self._filter_time_used,
                "filter_time_remaining": self._filter_time_remaining
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"air_filter.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "air_filter_result": self._air_filter_result,
                        "switch_status": self._switch_status,
                        "child_lock_switch_status": self._child_lock_switch_status,
                        "negative_ion_switch_status": self._negative_ion_switch_status,
                        "speed": self._speed,
                        "control_status": self._control_status,
                        "filter_time_used": self._filter_time_used,
                        "filter_time_remaining": self._filter_time_remaining
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"air_filter.main.switch":
                self.LOG.warn(
                    ("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
                self.set_item('_switch_status',
                              msg['params']["attribute"]["switch"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"air_filter.main.child_lock_switch":
                self.LOG.warn(
                    ("童锁开关: %s" % (msg['params']["attribute"]["child_lock_switch"])).encode(coding))
                self.set_item('_child_lock_switch_status',
                              msg['params']["attribute"]["child_lock_switch"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"air_filter.main.negative_ion_switch":
                self.LOG.warn(
                    ("负离子开关: %s" % (msg['params']["attribute"]["negative_ion_switch"])).encode(coding))
                self.set_item('_negative_ion_switch_status',
                              msg['params']["attribute"]["negative_ion_switch"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"air_filter.main.control":
                self.LOG.warn(
                    ("设置模式切换: %s" % (msg['params']["attribute"]["control"])).encode(coding))
                self.set_item('_control_status',
                              msg['params']["attribute"]["control"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"air_filter.main.speed":
                self.LOG.warn(
                    ("设置风量调节: %s" % (msg['params']["attribute"]["speed"])).encode(coding))
                self.set_item('_speed', msg['params']["attribute"]["speed"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            else:
                self.LOG.warn('TODO in the feature!')

        else:
            self.LOG.warn('TODO in the feature!')


class Washer(BaseSim):
    def __init__(self, logger, mac='123456', time_delay=500):
        self.LOG = logger
        self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,
                            mac=mac, deviceCategory='wash_machine.main', self_addr=None)
        self.sdk_obj.sim_obj = self

        # state data:
        self.task_obj = Task('Washer-task', self.LOG)
        self._status = 'halt'
        self._auto_detergent_switch = 'off'
        self._child_lock_switch_status = "off"
        self._add_laundry_switch = "off"
        self._sterilization = "off"
        self._spin = 0
        self._temperature = 28
        self._reserve_wash = 24
        self._mode = 'mix'
        self._time_left = 10
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 60)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def status_maintain(self):
        need_send_report = False
        if self._status == 'start':
            need_send_report = True
            if self._time_left > 0:
                self.set_item('_time_left',
                              self._time_left - 1)
                if self._time_left <= 0:
                    self.set_item('_status', 'halt')
            else:
                self.set_item('_status', 'halt')

        if need_send_report:
            # return self.send_event_report()
            pass

    def get_event_report(self):
        report_msg = {
            "method": "report",
            "attribute": {
                "child_lock_switch": self._child_lock_switch_status,
                "auto_detergent_switch": self._auto_detergent_switch,
                "add_laundry_switch": self._add_laundry_switch,
                "sterilization": self._sterilization,
                "spin": self._spin,
                "temperature": self._temperature,
                "reserve_wash": self._reserve_wash,
                "mode": self._mode,
                "status": self._status,
                "time_left": self._time_left
            }
        }
        return json.dumps(report_msg)

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg['method'] == 'dm_get':
            if msg['nodeid'] == u"wash_machine.main.all_properties":
                self.LOG.warn("获取所有属性".encode(coding))
                rsp_msg = {
                    "method": "dm_get",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0,
                    "attribute": {
                        "child_lock_switch": self._child_lock_switch_status,
                        "auto_detergent_switch": self._auto_detergent_switch,
                        "add_laundry_switch": self._add_laundry_switch,
                        "sterilization": self._sterilization,
                        "spin": self._spin,
                        "temperature": self._temperature,
                        "reserve_wash": self._reserve_wash,
                        "mode": self._mode,
                        "status": self._status,
                        "time_left": self._time_left
                    }
                }
                return json.dumps(rsp_msg)
            else:
                self.LOG.warn('TODO in the feature!')

        elif msg['method'] == 'dm_set':
            if msg['nodeid'] == u"wash_machine.main.control":
                self.LOG.warn(
                    ("启动暂停: %s" % (msg['params']["attribute"]["control"])).encode(coding))
                self.set_item('_status', msg['params']["attribute"]["control"])
                self.set_item('_time_left', 10)
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.child_lock_switch":
                self.LOG.warn(
                    ("童锁开关: %s" % (msg['params']["attribute"]["child_lock_switch"])).encode(coding))
                self.set_item('_child_lock_switch_status',
                              msg['params']["attribute"]["child_lock_switch"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.auto_detergent_switch":
                self.LOG.warn(
                    ("设置智能投放: %s" % (msg['params']["attribute"]["auto_detergent_switch"])).encode(coding))
                self.set_item('_auto_detergent_switch',
                              msg['params']["attribute"]["auto_detergent_switch"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.add_laundry_switch":
                self.LOG.warn(
                    ("设置中途添衣: %s" % (msg['params']["attribute"]["add_laundry_switch"])).encode(coding))
                self.set_item('_add_laundry_switch',
                              msg['params']["attribute"]["add_laundry_switch"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.sterilization":
                self.LOG.warn(
                    ("一键除菌: %s" % (msg['params']["attribute"]["sterilization"])).encode(coding))
                self.set_item('_sterilization',
                              msg['params']["attribute"]["sterilization"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.mode":
                self.LOG.warn(
                    ("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
                self.set_item('_mode', msg['params']["attribute"]["mode"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.spin":
                self.LOG.warn(
                    ("设置脱水: %s" % (msg['params']["attribute"]["spin"])).encode(coding))
                self.set_item('_spin', msg['params']["attribute"]["spin"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.temperature":
                self.LOG.warn(
                    ("设置温度: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
                self.set_item('_temperature',
                              msg['params']["attribute"]["temperature"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            elif msg['nodeid'] == u"wash_machine.main.reserve_wash":
                self.LOG.warn(
                    ("设置预约功能: %s" % (msg['params']["attribute"]["reserve_wash"])).encode(coding))
                self.set_item('_reserve_wash',
                              msg['params']["attribute"]["reserve_wash"])
                rsp_msg = {
                    "method": "dm_set",
                    "req_id": msg['req_id'],
                    "msg": "success",
                    "code": 0
                }
                return json.dumps(rsp_msg)

            else:
                self.LOG.warn('TODO in the feature!')

        else:
            self.LOG.warn('TODO in the feature!')


class Door(BaseSim):
    def __init__(self, logger, config_file, server_addr, self_addr=None):
        module_name = "protocol.config.%s" % config_file
        mod = __import__(module_name)
        components = module_name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        self.sim_config = mod
        self.LOG = logger
        self.attribute_initialization()
        self.sdk_obj = SDK(addr=server_addr,
                           logger=logger, time_delay=0, self_addr=self_addr)
        self.sdk_obj.sim_obj = self
        self.sdk_obj.device_id = self._deviceID
        self.need_stop = False

        # state data:
        self.task_obj = Task('Washer-task', self.LOG)
        self.dev_register = False
        self.command_list = getattr(self.sim_config, "Command_list")
        self.create_tasks()

    def run_forever(self):
        thread_list = []
        thread_list.append([self.sdk_obj.schedule_loop])
        thread_list.append([self.sdk_obj.send_data_loop])
        thread_list.append([self.sdk_obj.recv_data_loop])
        thread_list.append([self.sdk_obj.heartbeat_loop])
        thread_list.append([self.task_obj.task_proc])
        thread_list.append([self.msg_dispatch])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 1)

        self.task_obj.add_task('monitor status report',
                               self.status_report_monitor, 10000000, 1)

        self.task_obj.add_task(
            'dev register', self.to_register_dev, 1, 1)

        self.task_obj.add_task(
            'check register', self.check_register_dev, 1, 10)

        self.task_obj.add_task(
            'heartbeat', self.to_send_heartbeat, 1000000, 60)

    def msg_dispatch(self):
        msgs = []

        for msg in self.test_msgs["msgs"]:
            for i in range(self.test_msgs["msgs"][msg]):
                msgs.append(msg)
        random.shuffle(msgs)
        for msg in msgs:
            self.LOG.debug(msg)
        while self.need_stop == False:
            for msg in msgs:
                time.sleep(self.test_msgs["interval"] / 1000.0)
                tmp_msg = msg.split('.')
                if tmp_msg[0] == 'COM_UPLOAD_DEV_STATUS':
                    self.send_msg(self.get_upload_status())
                elif tmp_msg[0] == 'COM_UPLOAD_RECORD':
                    self.send_msg(self.get_upload_record(tmp_msg[-1]))
                elif tmp_msg[0] == 'COM_UPLOAD_EVENT':
                    self.send_msg(self.get_upload_event(tmp_msg[-1]))
                else:
                    self.LOG.error("Unknow msg to dispatch: %s" % (msg))
            # time.sleep(9999)

    def status_maintain(self):
        for item in self.SPECIAL_ITEM:
            if "maintain" not in self.SPECIAL_ITEM[item]["use"]:
                continue
            if self.__dict__[item] != self.SPECIAL_ITEM[item]["init_value"]:
                tmp_item = '_current_time_' + item
                if '_current_time_' + item in self.__dict__:
                    if self.__dict__[tmp_item] > 0:
                        self.set_item(tmp_item, self.__dict__[tmp_item] - 1)
                        if self.__dict__[tmp_item] <= 0:
                            self.set_item(
                                tmp_item, self.SPECIAL_ITEM[item]["wait_time"])
                            self.set_item(
                                item, self.SPECIAL_ITEM[item]["init_value"])
                    else:
                        self.set_item(
                            item, self.SPECIAL_ITEM[item]["init_value"])
                else:
                    self.add_item('_current_time_' + item,
                                  self.SPECIAL_ITEM[item]["wait_time"])

    def status_report_monitor(self):
        need_send_report = False
        if not hasattr(self, 'old_status'):
            self.old_status = defaultdict(lambda: {})
            for item in self.__dict__:
                if item in self.SPECIAL_ITEM and "report" in self.SPECIAL_ITEM[item]["use"]:
                    self.LOG.yinfo("need check item: %s" % (item))
                    self.old_status[item] = copy.deepcopy(self.__dict__[item])

        for item in self.old_status:
            if self.old_status[item] != self.__dict__[item]:
                need_send_report = True
                self.old_status[item] = copy.deepcopy(self.__dict__[item])

        if need_send_report:
            self.send_msg(self.get_upload_status())

    def to_register_dev(self):
        if self.dev_register:
            self.LOG.debug(common_APIs.chinese_show("设备已经注册"))
        else:
            self.LOG.debug(common_APIs.chinese_show("发送设备注册"))
            self.send_msg(json.dumps(
                self.get_send_msg('COM_DEV_REGISTER')))

    def to_send_heartbeat(self):
        self.send_msg(json.dumps(
            self.get_send_msg('COM_HEARTBEAT')))

    def check_register_dev(self):
        if self.dev_register:
            self.LOG.yinfo(common_APIs.chinese_show("设备已经注册"))
        else:
            self.LOG.error(common_APIs.chinese_show("设备注册失败"))
            sys.exit()

    def get_upload_status(self):
        self.LOG.warn(common_APIs.chinese_show("设备状态上报"))
        return json.dumps(self.get_send_msg('COM_UPLOAD_DEV_STATUS'))

    def get_upload_record(self, record_type):
        self.LOG.warn(common_APIs.chinese_show("记录上传"))
        report_msg = self.get_send_msg('COM_UPLOAD_RECORD')
        report_msg["Data"][0]["RecordType"] = record_type
        return json.dumps(report_msg)

    def get_upload_event(self, event_type):
        self.LOG.warn(common_APIs.chinese_show("事件上报"))
        report_msg = self.get_send_msg('COM_UPLOAD_EVENT')
        report_msg["Data"][0]["EventType"] = event_type
        return json.dumps(report_msg)

    def protocol_handler(self, msg, ack=False):
        coding = sys.getfilesystemencoding()
        if ack:
            if msg['Command'] == 'COM_DEV_REGISTER':
                self.dev_register = True
                return None
            else:
                self.LOG.warn('Unknow msg: %s!' % (msg['Command']))
                return None

        if msg['Command'] in self.command_list:
            self.set_items(msg['Command'], msg)
            self.action(msg['Command'])
            rsp_msg = self.get_rsp_msg(msg['Command'])
            return json.dumps(rsp_msg)
        else:
            self.LOG.warn('Unknow msg: %s!' % (msg['Command']))
            return None

    def get_msg_by_command(self, command):
        command = getattr(self.sim_config, command)
        command_str = str(command)
        command_str = re.sub(r'\'TIMENOW\'', '"%s"' % datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'), command_str)
        command_str = re.sub(r'\'randint1\'', '"%s"' %
                             random.randint(0, 1), command_str)
        return eval(command_str.replace("'##", "").replace("##'", ""))

    def get_record_list(self):
        return getattr(self.sim_config, "defined_record")

    def get_event_list(self):
        return getattr(self.sim_config, "defined_event")

    def get_send_msg(self, command):
        return self.get_msg_by_command(command)['send_msg']

    def get_rsp_msg(self, command):
        return self.get_msg_by_command(command)['rsp_msg']

    def set_items(self, command, msg):
        item_dict = self.get_msg_by_command(command)['set_item']
        for item, msg_param in item_dict.items():
            msg_param_list = msg_param.split('.')
            tmp_msg = msg[msg_param_list[0]]
            for i in msg_param_list[1:]:
                tmp_msg = tmp_msg[i]
            self.set_item(item, tmp_msg)

    def action(self, command):
        action_dict = self.get_msg_by_command(command)['action']
        for action_fun, action_param in action_dict:
            if action_fun == 'reconnection':
                self.reconnection(action_param[0])
            else:
                self.LOG.warn('Unknow fun: %s!' % (action_fun))

    def reconnection(self, value):
        self.sdk_obj.connection_close()
        time.sleep(value)
        self.sdk_obj.connection_setup()

    def attribute_initialization(self):
        attribute_params_dict = getattr(
            self.sim_config, "Attribute_initialization")
        for attribute_params, attribute_params_value in attribute_params_dict.items():
            self.add_item(attribute_params, attribute_params_value)


class Led(BaseSim):
    def __init__(self, logger):
        self.LOG = logger
        self.sdk_obj = None
        self.need_stop = False

        # state data:
        self.task_obj = Task('Washer-task', self.LOG)
        self.create_tasks()

    def create_tasks(self):
        self.task_obj.add_task(
            'status maintain', self.status_maintain, 10000000, 60)

        self.task_obj.add_task('monitor event report',
                               self.status_report_monitor, 10000000, 1)

    def run_forever(self):
        thread_list = []
        thread_list.append([self.task_obj.task_proc])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def protocol_handler(self, datas):
        need_ASP_response = False
        need_default_response = False
        rsp_datas = {
            'control': datas['control'],
            'seq': datas['seq'],
            'addr': datas['addr'],
            'cmd': datas['cmd'],
            'reserve': datas['reserve'],
            'data': b'\x88\x88',
        }
        if bit_get(datas['control'], 7):
            self.LOG.debug('ACK msg!')
            return

        if bit_get(datas['control'], 6):
            self.LOG.info('Device: %s, disable default Response!' %
                          (struct.unpack('3s', datas['addr'])))
        else:
            need_default_response = True
            self.LOG.info('Device: %s, enable default Response!' %
                          (struct.unpack('3s', datas['addr'])))

        if bit_get(datas['control'], 5):
            self.LOG.info('Device: %s, disable ASP Response!' %
                          (struct.unpack('3s', datas['addr'])))
        else:
            need_ASP_response = True
            self.LOG.INFO('Device: %s, enable ASP Response!' %
                          (struct.unpack('3s', datas['addr'])))
        return rsp_datas


if __name__ == '__main__':

    pass
