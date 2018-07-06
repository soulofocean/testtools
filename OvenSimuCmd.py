#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-4'
"""
import json
from basic.BasicCommon import *
from basic.BasicSimuCmd import BasicCmd, BaseWifiSim

# region const variates
rout_addr = ('192.168.10.1', 65381)

class OvenCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180704"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "Oven"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version,d_type=self.device_type)
        self.sim_obj = eval(self.device_type)(logger, mac=self.mac, addr=rout_addr)
        self.do_start()
        self.onoff_kv = {"0": "off", "1": "on"}

    def help_switch(self):
        self.cprint.notice_p("switch %s:switch %s" % (self.device_type, self.onoff_kv))
    def do_switch(self, arg):
        args = arg.split()
        if(len(args)!=1 or args[0] not in self.onoff_kv):
            self.help_switch()
        else:
            self.sim_obj.set_item("_switch", self.onoff_kv[args[0]])

class Oven(BaseWifiSim):
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

if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = OvenCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()