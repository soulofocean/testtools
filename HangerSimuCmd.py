#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-2'
"""
import json
from basic.BasicCommon import *
from basic.BasicSimuCmd import BasicCmd, BaseWifiSim

# region const variates
rout_addr = ('192.168.10.1', 65381)

class HangerCmd(BasicCmd):
    def __init__(self, logger, cprint):
        self.air_version = "20180702"
        self.mac = str(hex(int(time.time())))[-8:]
        self.device_type = "Hanger"
        BasicCmd.__init__(self, logger=logger, cprint=cprint, version=self.air_version, d_type=self.device_type)
        self.sim_obj = eval(self.device_type)(logger, mac=self.mac, addr=rout_addr)
        self.do_start()
        self.onoff_kv = {"0": "off", "1": "on"}
        self.ctl_kv = {"0": "up", "1": "down", "2": "pause"}
        self.ster_d_list = [10, 20]
        self.dry_d_list = [30, 60, 90, 120]
        self.air_dry_d_list = [30, 60, 90, 120]

    def help_light(self):
        self.cprint.notice_p("%s light control:light %s" % (self.device_type, self.onoff_kv))

    def do_light(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_light()
        else:
            self.sim_obj.set_item("_light", self.onoff_kv[args[0]])

    def help_ctl(self):
        self.cprint.notice_p("%s up/down/pause control:ctl %s" % (self.device_type, self.ctl_kv))

    def do_ctl(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.ctl_kv):
            self.help_ctl()
        else:
            ctl_status = self.ctl_kv[args[0]]
            self.sim_obj.set_item("_status", ctl_status)
            if ctl_status == 'up':
                self.sim_obj.task_obj.del_task('change_status_bottom')
                self.sim_obj.task_obj.add_task(
                    'change_status_top', self.sim_obj.set_item, 1, 1000, '_status', 'top')

            elif ctl_status == 'down':
                self.sim_obj.task_obj.del_task('change_status_top')
                self.sim_obj.task_obj.add_task(
                    'change_status_bottom', self.sim_obj.set_item, 1, 1000, '_status', 'bottom')

            elif ctl_status == 'pause':
                self.sim_obj.task_obj.del_task('change_status_top')
                self.sim_obj.task_obj.del_task('change_status_bottom')

    def help_ster(self):
        self.cprint.notice_p("%s sterilization switch:ster %s" % (self.device_type, self.onoff_kv))

    def do_ster(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_ster()
        else:
            self.sim_obj.set_item("_sterilization", self.onoff_kv[args[0]])
            self.sim_obj.set_item("_sterilization_remain", self.sim_obj.get_item("_sterilization_duration"))

    def help_ster_d(self):
        self.cprint.notice_p("set %s sterilization duration:ster_d %s" % (self.device_type, self.ster_d_list))

    def do_ster_d(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) not in self.ster_d_list):
            self.help_ster_d()
        else:
            self.sim_obj.set_item("_sterilization_duration", int(args[0]))
            self.sim_obj.set_item("_sterilization_remain", self.sim_obj.get_item("_sterilization_duration"))

    def help_dry(self):
        self.cprint.notice_p("%s drying switch:dry %s" % (self.device_type, self.onoff_kv))

    def do_dry(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_dry()
        else:
            self.sim_obj.set_item("_drying", self.onoff_kv[args[0]])
            self.sim_obj.set_item("_drying_remain", self.sim_obj.get_item("_drying_duration"))

    def help_dry_d(self):
        self.cprint.notice_p("set %s drying duration:dry_d %s" % (self.device_type, self.dry_d_list))

    def do_dry_d(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) not in self.dry_d_list):
            self.help_dry_d()
        else:
            self.sim_obj.set_item("_drying_duration", int(args[0]))
            self.sim_obj.set_item("_drying_remain", self.sim_obj.get_item("_drying_duration"))

    def help_air_dry(self):
        self.cprint.notice_p("%s air drying switch:air_dry %s" % (self.device_type, self.onoff_kv))

    def do_air_dry(self, arg):
        args = arg.split()
        if (len(args) != 1 or args[0] not in self.onoff_kv):
            self.help_air_dry()
        else:
            self.sim_obj.set_item("_air_drying", self.onoff_kv[args[0]])
            self.sim_obj.set_item("_air_drying_remain", self.sim_obj.get_item("_drying_duration"))

    def help_air_dry_d(self):
        self.cprint.notice_p("set %s air drying duration:air_dry_d %s" % (self.device_type, self.air_dry_d_list))

    def do_air_dry_d(self, arg):
        args = arg.split()
        if (len(args) != 1 or not args[0].isdigit() or int(args[0]) not in self.air_dry_d_list):
            self.help_air_dry_d()
        else:
            self.sim_obj.set_item("_air_drying_duration", int(args[0]))
            self.sim_obj.set_item("_air_drying_remain", self.sim_obj.get_item("_air_drying_duration"))

class Hanger(BaseWifiSim):
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


if __name__ == '__main__':
    LOG = MyLogger(os.path.abspath(sys.argv[0]).replace('py', 'log'), clevel=logging.DEBUG,
                   rlevel=logging.WARN)
    cprint = cprint(__name__)
    airCmd = HangerCmd(logger=LOG, cprint=cprint)
    cprint.yinfo_p("start simu mac [%s]" % (airCmd.mac,))
    airCmd.cmdloop()
