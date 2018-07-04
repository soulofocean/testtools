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

alarm_lock = threading.Lock()


class BaseSim():
	__metaclass__ = ABCMeta
	status_lock = threading.Lock()

	def __init__(self, logger, addr=('192.168.10.1', 65381), mac='123456', time_delay=500
                 , self_addr=None, deviceCategory='airconditioner.new'):
		self.LOG = logger
		self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,
							mac=mac, deviceCategory=deviceCategory, self_addr=self_addr, addr=addr)
		self.sdk_obj.sim_obj = self
		self.need_stop = False

		# state data:
		self.task_obj = Task('Washer-task', self.LOG)
		self.create_tasks()
		self.alarm_dict = defaultdict(dict)
		self.attr_dict = defaultdict(dict)  # add by zx 20180524

	@common_APIs.need_add_lock(status_lock)
	def set_item(self, item, value):
		if item in self.__dict__:
			self.__dict__[item] = value
		else:
			self.LOG.error("Unknow item: %s" % (item))

	# add by zx 20180524
	@common_APIs.need_add_lock(status_lock)
	def get_item(self, item):
		if item in self.__dict__:
			return self.__dict__[item]
		else:
			self.LOG.error("get_item Unknown item: %s" % (item))

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
	def protocol_handler(self, msg):
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
		thread_list.append([self.sdk_obj.heartbeat_loop, False])
		thread_list.append([self.task_obj.task_proc])
		thread_list.append([self.alarm_proc])
		thread_ids = []
		for th in thread_list:
			thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

		for th in thread_ids:
			th.setDaemon(True)
			th.start()

	def create_tasks(self):
		self.task_obj.add_task(
			'status maintain', self.status_maintain, 10000000, 100)

		self.task_obj.add_task('monitor event report',
							   self.status_report_monitor, 10000000, 1)

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

	def alarm_proc(self):
		while self.need_stop == False:
			alarm_lock.acquire()
			for alarm in self.alarm_dict:
				if self.alarm_dict[alarm]['status'] == 'ready':
					self.alarm_dict[alarm]['status'] = "over"
					self.send_msg(self.alarm_report(self.alarm_dict[alarm]['error_code'], self.alarm_dict[alarm]
					['error_status'], self.alarm_dict[alarm]['error_level'], self.alarm_dict[alarm]['error_msg']))

				elif self.alarm_dict[alarm]['status'] == 'over':
					pass

			alarm_lock.release()
			time.sleep(3)

	def alarm_report(self, error_code, error_status, error_level=1, error_msg="test alarm"):
		report_msg = {
			"method": "alarm",
			"attribute": {
				"error_code": error_code,
				"error_msg": error_msg,
				"error_level": error_level,
				"error_status": error_status,
			}
		}
		return json.dumps(report_msg)

	@common_APIs.need_add_lock(alarm_lock)
	def add_alarm(self, error_code, error_status, error_level=1, error_msg="test alarm"):
		if error_code in self.alarm_dict and self.alarm_dict[error_code]['status'] != 'over':
			pass
		else:
			self.alarm_dict[error_code]['error_code'] = error_code
			self.alarm_dict[error_code]['error_status'] = error_status
			self.alarm_dict[error_code]['error_level'] = error_level
			self.alarm_dict[error_code]['error_msg'] = error_msg
			self.alarm_dict[error_code]['status'] = 'ready'

	@common_APIs.need_add_lock(alarm_lock)
	def set_alarm(self, error_code, status):
		if error_code in self.alarm_dict:
			self.alarm_dict[error_code]['status'] = status
		else:
			self.LOG.error('error code not exist!')

	@common_APIs.need_add_lock(alarm_lock)
	def del_alarm(self, error_code):
		if error_code in self.alarm_dict:
			self.alarm_dict[error_code]['status'] = status
			self.LOG.error('Del error code: %s' % str(error_code))

	def alarm_confirm_rsp(self, req, error_code):
		self.LOG.warn(("故障(解除)上报确认:").encode(coding))
		self.set_alarm(error_code, 'over')
		rsp_msg = {
			"method": "dm_set",
			"req_id": req,
			"msg": "success",
			"code": 0,
			"attribute": {
				"error_code": error_code,
				"error_status": self.alarm_dict[error_code]["error_status"]
			}
		}
		return json.dumps(rsp_msg)

	def dm_set_rsp(self, req):
		rsp_msg = {
			"method": "dm_set",
			"req_id": req,
			"msg": "success",
			"code": 0
		}
		return json.dumps(rsp_msg)

	# add by zx-20180524
	def initAttrAndDict(self, initAttr=True, initDict=True):
		dictTmp = defaultdict(dict)
		sourceDict = self.attr_dict
		if sourceDict:
			for key, value in sourceDict.items():
				item_name = "_" + key
				if (initAttr):
					self.add_item(item_name, value)
					# setattr(self, "_" + key, value)
				if (initDict):
					dictTmp[key] = self.get_item(item_name)
		return dictTmp


class Air(BaseSim):
	def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
		super(Air, self).__init__(logger, addr=addr, mac=mac,time_delay=time_delay
                                  ,self_addr=self_addr,deviceCategory='airconditioner.new')
		#self.LOG = logger
		#self.sdk_obj = Wifi(logger=logger, time_delay=time_delay
        # , mac=mac, deviceCategory='airconditioner.new', self_addr=self_addr)
		#self.sdk_obj.sim_obj = self

		# state data:
		# self._switchStatus = 'off'
		# self._temperature = 16
		# self._mode = "cold"
		# self._speed = "low"
		# self._wind_up_down = 'off'
		# self._wind_left_right = 'off'
		# add by zx 20180524
		self.attr_dict = {
			"switchStatus": 'off',
			"temperature": 16,
			"mode": 'cold',
			"speed": 'low',
			"wind_up_down": 'off',
			"wind_left_right": 'off',
			"env_temperature": 205
		}
		self.initAttrAndDict(initDict=False)

	def get_event_report(self):
		self.LOG.warn("get_event_report".encode(coding))
		report_msg = {
			"method": "report",
			# "attribute": {
			# "switchStatus": self._switchStatus,
			# "temperature": self._temperature,
			# "mode": self._mode,
			# "speed": self._speed,
			# "wind_up_down": self._wind_up_down,
			# "wind_left_right": self._wind_left_right
			# }
			"attribute": self.initAttrAndDict(initAttr=False)
		}
		return json.dumps(report_msg)

	def protocol_handler(self, msg):
		coding = sys.getfilesystemencoding()
		if msg['method'] == 'dm_get':
			if msg['nodeid'] == u"airconditioner.new.all_properties":
				self.LOG.warn("获取所有属性new".encode(coding))
				rsp_msg = {
					"method": "dm_get",
					"req_id": msg['req_id'],
					"msg": "success",
					"code": 0,
					# "attribute": {
					# "switchStatus": self._switchStatus,
					# "temperature": self._temperature,
					# "mode": self._mode,
					# "speed": self._speed,
					# "wind_up_down": self._wind_up_down,
					# "wind_left_right": self._wind_left_right
					# }
					"attribute": self.initAttrAndDict(initAttr=False)
				}
				return json.dumps(rsp_msg)
			if msg['nodeid'] == u"airconditioner.main.all_properties":
				self.LOG.warn("获取所有属性main".encode(coding))
				rsp_msg = {
					"method": "dm_get",
					"req_id": msg['req_id'],
					"msg": "success",
					"code": 0,
					# "attribute": {
					# "switchStatus": self._switchStatus,
					# "temperature": self._temperature,
					# "mode": self._mode,
					# "speed": self._speed,
					# "wind_up_down": self._wind_up_down,
					# "wind_left_right": self._wind_left_right
					# }
					"attribute": self.initAttrAndDict(initAttr=False)
				}
				return json.dumps(rsp_msg)
			else:
				self.LOG.warn('Unknow msg!')

		elif msg['method'] == 'dm_set':

			if msg['nodeid'] == u"condition.main.switch":
				self.LOG.warn(
					("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
				self.set_item('_switchStatus',
							  msg['params']["attribute"]["switch"])
				return self.dm_set_rsp(msg['req_id'])
			elif msg['nodeid'] == u"airconditioner.main.switch":
				self.LOG.warn(
					("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
				self.set_item('_switchStatus',
							  msg['params']["attribute"]["switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"airconditioner.main.mode":
				self.LOG.warn(
					("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
				self.set_item('_mode', msg['params']["attribute"]["mode"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"airconditioner.main.temperature":
				self.LOG.warn(
					("设置温度: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
				self.set_item('_temperature',
							  msg['params']["attribute"]["temperature"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"airconditioner.main.speed":
				self.LOG.warn(
					("设置风速: %s" % (msg['params']["attribute"]["speed"])).encode(coding))
				self.set_item('_speed', msg['params']["attribute"]["speed"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"airconditioner.main.wind_up_down":
				self.LOG.warn(
					("设置上下摆风: %s" % (msg['params']["attribute"]["wind_up_down"])).encode(coding))
				self.set_item('_wind_up_down',
							  msg['params']["attribute"]["wind_up_down"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"airconditioner.main.wind_left_right":
				self.LOG.warn(
					("设置左右摆风: %s" % (msg['params']["attribute"]["wind_left_right"])).encode(coding))
				self.set_item('_wind_left_right',
							  msg['params']["attribute"]["wind_left_right"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wifi.main.alarm_confirm":
				return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

			else:
				self.LOG.warn('Unknow msg!')
		else:
			self.LOG.error('Msg wrong!')


class Hanger(BaseSim):
	def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
		super(Hanger, self).__init__(logger, addr=addr, mac=mac,time_delay=time_delay,self_addr=self_addr,deviceCategory='clothes_hanger.main')
		#self.LOG = logger
		#self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='clothes_hanger.main', self_addr=self_addr)
		#self.sdk_obj.sim_obj = self

		# state data:
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

	def status_maintain(self):
		if self._sterilization == 'on':
			if self._sterilization_remain > 0:
				self.set_item('_sterilization_remain',
							  self._sterilization_remain - 1)
				if self._sterilization_remain <= 0:
					self.set_item('_sterilization', 'off')
			else:
				self.set_item('_sterilization', 'off')

		if self._drying == 'on':
			if self._drying_remain > 0:
				self.set_item('_drying_remain', self._drying_remain - 1)
				if self._drying_remain <= 0:
					self.set_item('_drying', 'off')
			else:
				self.set_item('_drying', 'off')

		if self._air_drying == 'on':
			if self._air_drying_remain > 0:
				self.set_item('_air_drying_remain',
							  self._air_drying_remain - 1)
				if self._air_drying_remain <= 0:
					self.set_item('_air_drying', 'off')
			else:
				self.set_item('_air_drying', 'off')

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
				self.LOG.warn('Unknow msg!')

		elif msg['method'] == 'dm_set':
			if msg['nodeid'] == u"clothes_hanger.main.control":
				self.LOG.warn(
					("设置上下控制: %s" % (msg['params']["attribute"]["control"])).encode(coding))
				self.set_item('_status', msg['params']["attribute"]["control"])

				if self._status == 'up':
					self.task_obj.del_task('change_status_bottom')
					self.task_obj.add_task(
						'change_status_top', self.set_item, 1, 1000, '_status', 'top')

				elif self._status == 'down':
					self.task_obj.del_task('change_status_top')
					self.task_obj.add_task(
						'change_status_bottom', self.set_item, 1, 1000, '_status', 'bottom')

				elif self._status == 'pause':
					self.task_obj.del_task('change_status_top')
					self.task_obj.del_task('change_status_bottom')

				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"clothes_hanger.main.light":
				self.LOG.warn(
					("设置照明: %s" % (msg['params']["attribute"]["light"])).encode(coding))
				self.set_item('_light', msg['params']["attribute"]["light"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"clothes_hanger.main.sterilization":
				self.LOG.warn(
					("设置杀菌: %s" % (msg['params']["attribute"]["sterilization"])).encode(coding))
				self.set_item('_sterilization',
							  msg['params']["attribute"]["sterilization"])
				self.set_item('_sterilization_remain',
							  self._sterilization_duration)
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"clothes_hanger.main.sterilization_duration":
				self.LOG.warn(
					("设置杀菌时间: %s" % (msg['params']["attribute"]["sterilization_duration"])).encode(coding))
				self.set_item('_sterilization_duration',
							  msg['params']["attribute"]["sterilization_duration"])
				self.set_item('_sterilization_remain',
							  self._sterilization_duration)
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"clothes_hanger.main.drying":
				self.LOG.warn(
					("设置烘干: %s" % (msg['params']["attribute"]["drying"])).encode(coding))
				self.set_item('_drying', msg['params']["attribute"]["drying"])
				self.set_item('_drying_remain', self._drying_duration)
				if self._drying == 'on':
					self.set_item('_air_drying', 'off')
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"clothes_hanger.main.drying_duration":
				self.LOG.warn(
					("设置烘干时间: %s" % (msg['params']["attribute"]["drying_duration"])).encode(coding))
				self.set_item('_drying_duration',
							  msg['params']["attribute"]["drying_duration"])
				self.set_item('_drying_remain', self._drying_duration)
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"clothes_hanger.main.air_drying":
				self.LOG.warn(
					("设置风干: %s" % (msg['params']["attribute"]["air_drying"])).encode(coding))
				self.set_item(
					'_air_drying', msg['params']["attribute"]["air_drying"])
				self.set_item('_air_drying_remain', self._air_drying_duration)

				if self._air_drying == 'on':
					self.set_item('_drying', 'off')
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"clothes_hanger.main.air_drying_duration":
				self.LOG.warn(
					("设置风干时间: %s" % (msg['params']["attribute"]["air_drying_duration"])).encode(coding))
				self.set_item('_air_drying_duration',
							  msg['params']["attribute"]["air_drying_duration"])
				self.set_item('_air_drying_remain', self._air_drying_duration)
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wifi.main.alarm_confirm":
				return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

			else:
				self.LOG.warn('Unknow msg!')
		else:
			self.LOG.error('Msg wrong!')


class Waterfilter(BaseSim):
	def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
		super(Waterfilter, self).__init__(logger, addr=addr, mac=mac,time_delay=time_delay,self_addr=self_addr,deviceCategory='water_filter.main')
		#self.LOG = logger
		#self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='water_filter.main', self_addr=self_addr)
		#self.sdk_obj.sim_obj = self

		# state data:
		self._filter_result = {
			"TDS": [
				500,
				100
			]
		}
		self._status = 'standby'
		self._water_leakage = "off"
		self._water_shortage = "off"
		self._filter_time_total = [
			2000,
			2000,
		]
		self._filter_time_remaining = [
			1000,
			1000,
		]
		self._filter_lifetime = [
			15,
			23
		]
		self._filter_status = "normal"
		self._water_leakage = "off"
		self._water_shortage = "off"

	def reset_filter_time(self, id):
		if int(id) in self._filter_time_total:
			self._filter_time_remaining[int(
				id)] = self._filter_time_total[int(id)]
			return True
		else:
			self.LOG.error('Unknow ID: %s' % (id))
			return False

	def get_event_report(self):
		report_msg = {
			"method": "report",
			"attribute": {
				"water_filter_result": self._filter_result,
				"status": self._status,
				"filter_time_total": self._filter_time_total,
				"filter_time_remaining": self._filter_time_remaining,
				"water_shortage": self._water_shortage,
				"water_leakage": self._water_leakage,
				"filter_lifetime": self._filter_lifetime
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
						"water_filter_result": self._filter_result,
						"status": self._status,
						"filter_time_total": self._filter_time_total,
						"filter_time_remaining": self._filter_time_remaining,
						"filter_lifetime": self._filter_lifetime,
						"filter_status": self._filter_status,
						"water_shortage": self._water_shortage,
						"water_leakage": self._water_leakage,
					}
				}
				return json.dumps(rsp_msg)
			else:
				self.LOG.warn('Unknow msg!')

		elif msg['method'] == 'dm_set':
			if msg['nodeid'] == u"water_filter.main.control":
				self.LOG.warn(
					("设置冲洗: %s" % (msg['params']["attribute"]["control"])).encode(coding))
				self.set_item('_status', msg['params']["attribute"]["control"])
				self.task_obj.add_task(
					'change WaterFilter to filter', self.set_item, 1, 100, '_status', 'standby')
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"water_filter.main.reset_filter":
				self.LOG.warn(
					("复位滤芯: %s" % (msg['params']["attribute"]["reset_filter"])).encode(coding))
				filter_ids = msg['params']["attribute"]["reset_filter"]
				if 0 in filter_ids:
					filter_ids = self._filter_time_total
				for filter_id in filter_ids:
					self.reset_filter_time(filter_id)
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wifi.main.alarm_confirm":
				return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

			else:
				self.LOG.warn('Unknow msg!')

		else:
			self.LOG.error('Msg wrong!')


class AirFilter(BaseSim):
	def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
		super(AirFilter, self).__init__(logger, addr=addr, mac=mac,time_delay=time_delay,self_addr=self_addr,deviceCategory='air_filter.main')
		#self.LOG = logger
		#self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='air_filter.main', self_addr=self_addr)
		#self.sdk_obj.sim_obj = self

		# state data:
		self._air_filter_result = {
			"air_quality": [
				"good"
			],
			"PM25": [
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
		self._temperature = "1888"
		self._humidity = "5666"
		self._replace_filter = "false"

	def get_event_report(self):
		report_msg = {
			"method": "report",
			"attribute": {
				"air_filter_result": self._air_filter_result,
				"switch_status": self._switch_status,
				"child_lock_switch_status": self._child_lock_switch_status,
				"negative_ion_switch_status": self._negative_ion_switch_status,
				"speed": self._speed,
				"control": self._control_status,
				"filter_time_used": self._filter_time_used,
				"filter_time_remaining": self._filter_time_remaining,
				"temperature": self._temperature,
				"humidity": self._humidity,
				"replace_filter": self._replace_filter
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
						"control": self._control_status,
						"filter_time_used": self._filter_time_used,
						"filter_time_remaining": self._filter_time_remaining,
						"temperature": self._temperature,
						"humidity": self._humidity,
						"replace_filter": self._replace_filter
					}
				}
				return json.dumps(rsp_msg)
			else:
				self.LOG.warn('Unknow msg!')

		elif msg['method'] == 'dm_set':
			if msg['nodeid'] == u"air_filter.main.switch":
				self.LOG.warn(
					("开关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
				self.set_item('_switch_status',
							  msg['params']["attribute"]["switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"air_filter.main.child_lock_switch":
				self.LOG.warn(
					("童锁开关: %s" % (msg['params']["attribute"]["child_lock_switch"])).encode(coding))
				self.set_item('_child_lock_switch_status',
							  msg['params']["attribute"]["child_lock_switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"air_filter.main.negative_ion_switch":
				self.LOG.warn(
					("负离子开关: %s" % (msg['params']["attribute"]["negative_ion_switch"])).encode(coding))
				self.set_item('_negative_ion_switch_status',
							  msg['params']["attribute"]["negative_ion_switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"air_filter.main.control":
				self.LOG.warn(
					("设置模式切换: %s" % (msg['params']["attribute"]["control"])).encode(coding))
				self.set_item('_control_status',
							  msg['params']["attribute"]["control"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"air_filter.main.speed":
				self.LOG.warn(
					("设置风量调节: %s" % (msg['params']["attribute"]["speed"])).encode(coding))
				self.set_item('_speed', msg['params']["attribute"]["speed"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wifi.main.alarm_confirm":
				return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

			else:
				self.LOG.warn('Unknow msg!')

		else:
			self.LOG.error('Msg wrong!')


class Washer(BaseSim):
	def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
		super(Washer, self).__init__(logger, addr=addr, mac=mac,time_delay=time_delay,self_addr=self_addr,deviceCategory='wash_machine.main')
		#self.LOG = logger
		#self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='wash_machine.main', self_addr=self_addr)
		#self.sdk_obj.sim_obj = self

		# state data:
		self._status = 'standby'#
		self._auto_detergent_switch = 'off'##
		self._child_lock_switch_status = "off"##
		self._add_laundry_switch = "off"#
		self._sterilization = "off"#
		self._spin = 0#
		self._temperature = 28#
		self._reserve_wash = 24#
		self._mode = "mix"#
		self._time_left = 10#
		self._drying = "no_drying"#
		self._operation = "spin"#
		self._drying_duration = 15#
		self._switch = "on"#


	def status_maintain(self):
		if self._status == 'start':
			if self._time_left > 0:
				self.set_item('_time_left',
							  self._time_left - 1)
				if self._time_left <= 0:
					self.set_item('_status', 'halt')
			else:
				self.set_item('_status', 'halt')

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
				"time_left": self._time_left,
				"drying": self._drying,
				"operation": self._operation,
				"drying_duration": self._drying_duration,
				"switch": self._switch
			}
		}
		return json.dumps(report_msg)

	def protocol_handler(self, msg):
		coding = sys.getfilesystemencoding()
		if msg['method'] == 'dm_get':
			if msg['nodeid'] == u"wash_machine.main.all_properties":
				self.LOG.warn("[%s]获取所有属性main".encode(coding) % self)
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
						"time_left": self._time_left,
						"drying" : self._drying,
						"operation" : self._operation,
						"drying_duration" : self._drying_duration,
						"switch" : self._switch
					}
				}
				return json.dumps(rsp_msg)
			else:
				self.LOG.warn('Unknow msg!')

		elif msg['method'] == 'dm_set':
			if msg['nodeid'] == u"wash_machine.main.control":
				self.LOG.warn(
					("启动暂停: %s" % (msg['params']["attribute"]["control"])).encode(coding))
				self.set_item('_status', msg['params']["attribute"]["control"])
				self.set_item('_time_left', 10)
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.child_lock_switch":
				self.LOG.warn(
					("童锁开关: %s" % (msg['params']["attribute"]["child_lock_switch"])).encode(coding))
				self.set_item('_child_lock_switch_status',
							  msg['params']["attribute"]["child_lock_switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.auto_detergent_switch":
				self.LOG.warn(
					("设置智能投放: %s" % (msg['params']["attribute"]["auto_detergent_switch"])).encode(coding))
				self.set_item('_auto_detergent_switch',
							  msg['params']["attribute"]["auto_detergent_switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.add_laundry_switch":
				self.LOG.warn(
					("设置中途添衣: %s" % (msg['params']["attribute"]["add_laundry_switch"])).encode(coding))
				self.set_item('_add_laundry_switch',
							  msg['params']["attribute"]["add_laundry_switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.sterilization":
				self.LOG.warn(
					("一键除菌: %s" % (msg['params']["attribute"]["sterilization"])).encode(coding))
				self.set_item('_sterilization',
							  msg['params']["attribute"]["sterilization"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.mode":
				self.LOG.warn(
					("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
				self.set_item('_mode', msg['params']["attribute"]["mode"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.spin":
				self.LOG.warn(
					("设置脱水: %s" % (msg['params']["attribute"]["spin"])).encode(coding))
				self.set_item('_spin', msg['params']["attribute"]["spin"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.temperature":
				self.LOG.warn(
					("设置温度: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
				self.set_item('_temperature',
							  msg['params']["attribute"]["temperature"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wash_machine.main.reserve_wash":
				self.LOG.warn(
					("设置预约功能: %s" % (msg['params']["attribute"]["reserve_wash"])).encode(coding))
				self.set_item('_reserve_wash',
							  msg['params']["attribute"]["reserve_wash"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wifi.main.alarm_confirm":
				return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

			else:
				self.LOG.warn('Unknow msg!')

		else:
			self.LOG.error('Msg wrong!')


class Oven(BaseSim):
	def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
		super(Oven, self).__init__(logger, addr=addr, mac=mac,time_delay=time_delay,self_addr=self_addr,deviceCategory='oven.main.')
		#self.LOG = logger
		#self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='oven.main', self_addr=self_addr)
		#self.sdk_obj.sim_obj = self

		# state data:
		self._switch = 'off'
		self._status = 'stop'
		self._mode = 'broil'
		self._bake_duration = 99
		self._convection = 'off'
		self._rotisserie = 'off'
		self._temperature = 230
		self._reserve_bake = 1440
		self._remaining = 0
		self._step = 'bake'
		self._light = 'off'
		self._child_lock = 'off'
		self._time = time.strftime("%H:%M")
		self._preheat = 'off'

	def get_event_report(self):
		report_msg = {
			"method": "report",
			"attribute": {
				"switch": self._switch,
				"status": self._status,
				"mode": self._mode,
				"bake_duration": self._bake_duration,
				"convection": self._convection,
				"rotisserie": self._rotisserie,
				"temperature": self._temperature,
				"reserve_bake": self._reserve_bake,
				"remaining": self._remaining,
				"step": self._step,
				"light": self._light,
				"child_lock": self._child_lock,
				"time": self._time,
				"preheat": self._preheat
			}
		}
		return json.dumps(report_msg)

	def protocol_handler(self, msg):
		coding = sys.getfilesystemencoding()
		if msg['method'] == 'dm_get':
			if msg['nodeid'] == u"oven.main.all_properties":
				self.LOG.warn("获取所有属性".encode(coding))
				rsp_msg = {
					"method": "dm_get",
					"req_id": msg['req_id'],
					"msg": "success",
					"code": 0,
					"attribute": {
						"switch": self._switch,
						"status": self._status,
						"mode": self._mode,
						"bake_duration": self._bake_duration,
						"convection": self._convection,
						"rotisserie": self._rotisserie,
						"temperature": self._temperature,
						"reserve_bake": self._reserve_bake,
						"remaining": self._remaining,
						"step": self._step,
						"light": self._light,
						"child_lock": self._child_lock,
						"time": self._time,
						"preheat": self._preheat
					}
				}
				return json.dumps(rsp_msg)

			else:
				self.LOG.warn('Unknow msg!')

		elif msg['method'] == 'dm_set':
			if msg['nodeid'] == u"oven.main.switch":
				self.LOG.warn(
					("开/关机: %s" % (msg['params']["attribute"]["switch"])).encode(coding))
				self.set_item(
					'_switch', msg['params']["attribute"]["switch"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.control":
				self.LOG.warn(
					("启动暂停: %s" % (msg['params']["attribute"]["control"])).encode(coding))
				self.set_item(
					'_control', msg['params']["attribute"]["control"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.mode":
				self.LOG.warn(
					("设置模式: %s" % (msg['params']["attribute"]["mode"])).encode(coding))
				self.set_item(
					'_mode', msg['params']["attribute"]["mode"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.bake_duration":
				self.LOG.warn(
					("设置定时: %s" % (msg['params']["attribute"]["bake_duration"])).encode(coding))
				self.set_item(
					'_bake_duration', msg['params']["attribute"]["bake_duration"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.convection":
				self.LOG.warn(
					("设置热风对流: %s" % (msg['params']["attribute"]["convection"])).encode(coding))
				self.set_item(
					'_convection', msg['params']["attribute"]["convection"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.rotisserie":
				self.LOG.warn(
					("设置转叉: %s" % (msg['params']["attribute"]["rotisserie"])).encode(coding))
				self.set_item(
					'_rotisserie', msg['params']["attribute"]["rotisserie"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.temperature":
				self.LOG.warn(
					("设置温度: %s" % (msg['params']["attribute"]["temperature"])).encode(coding))
				self.set_item(
					'_temperature', msg['params']["attribute"]["temperature"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.reserve_bake":
				self.LOG.warn(
					("设置预约功能: %s" % (msg['params']["attribute"]["reserve_bake"])).encode(coding))
				self.set_item(
					'_reserve_bake', msg['params']["attribute"]["reserve_bake"])
				self.task_obj.del_task('switch')
				self.task_obj.add_task(
					'switch', self.set_item, 1, self._reserve_bake * 100, '_switch', 'off')
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.light":
				self.LOG.warn(
					("设置照明灯: %s" % (msg['params']["attribute"]["light"])).encode(coding))
				self.set_item(
					'_light', msg['params']["attribute"]["light"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.child_lock":
				self.LOG.warn(
					("设置童锁: %s" % (msg['params']["attribute"]["child_lock"])).encode(coding))
				self.set_item(
					'_child_lock', msg['params']["attribute"]["child_lock"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.time":
				self.LOG.warn(
					("设置时间: %s" % (msg['params']["attribute"]["time"])).encode(coding))
				self.set_item(
					'_time', msg['params']["attribute"]["time"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.preheat":
				self.LOG.warn(
					("设置辅热: %s" % (msg['params']["attribute"]["preheat"])).encode(coding))
				self.set_item(
					'_preheat', msg['params']["attribute"]["preheat"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"oven.main.custom":
				self.LOG.warn(
					("设置custom: %s" % (msg['params']["attribute"])).encode(coding))
				self.set_item(
					'_switch', msg['params']["attribute"]["switch"])
				self.set_item(
					'_status', msg['params']["attribute"]["control"])
				self.set_item(
					'_mode', msg['params']["attribute"]["mode"])
				self.set_item(
					'_bake_duration', msg['params']["attribute"]["bake_duration"])
				self.set_item(
					'_convection', msg['params']["attribute"]["convection"])
				self.set_item(
					'_rotisserie', msg['params']["attribute"]["rotisserie"])
				self.set_item(
					'_temperature', msg['params']["attribute"]["temperature"])
				self.set_item(
					'_reserve_bake', msg['params']["attribute"]["reserve_bake"])
				self.set_item(
					'_light', msg['params']["attribute"]["light"])
				self.set_item(
					'_child_lock', msg['params']["attribute"]["child_lock"])
				self.set_item(
					'_time', msg['params']["attribute"]["time"])
				self.set_item(
					'_preheat', msg['params']["attribute"]["preheat"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wifi.main.alarm_confirm":
				return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

			else:
				self.LOG.warn('Unknow msg %s!' % (msg['nodeid'],))

		else:
			self.LOG.error('Msg wrong!')


class Repeater(BaseSim):
	def __init__(self, logger, mac='123456', time_delay=500, self_addr=None, addr=('192.168.10.1', 65381)):
		super(Repeater, self).__init__(logger, addr=addr, mac=mac,time_delay=time_delay,self_addr=self_addr,deviceCategory='wifi_repeater.main')
		#self.LOG = logger
		#self.sdk_obj = Wifi(logger=logger, time_delay=time_delay,mac=mac, deviceCategory='wifi_repeater.main', self_addr=self_addr)
		#self.sdk_obj.sim_obj = self

		# state data:
		self._control = 'stop'

	def status_report_monitor(self):
		pass

	def protocol_handler(self, msg):
		coding = sys.getfilesystemencoding()
		if msg['method'] == 'dm_get':
			self.LOG.warn('Unknow msg!')

		elif msg['method'] == 'dm_set':
			if msg['nodeid'] == u"wifi_repeater.main.control":
				self.LOG.warn(
					("开启/关闭: %s" % (msg['params']["attribute"]["control"])).encode(coding))
				self.set_item(
					'_control', msg['params']["attribute"]["control"])
				return self.dm_set_rsp(msg['req_id'])

			elif msg['nodeid'] == u"wifi.main.alarm_confirm":
				return self.alarm_confirm_rsp(msg['req_id'], msg['params']["attribute"]["error_code"])

			else:
				self.LOG.warn('Unknow msg!')

		else:
			self.LOG.error('Msg wrong!')


if __name__ == '__main__':
	pass
