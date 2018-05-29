#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-5-25'
"""
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from protocol.wifi_devices import Air
import logging
from  os.path import join
from basic.log_tool import MyLogger
import os
import time
import socket
sim_type = "Air"
log_path = "wifi_mul_dev_log"
device_online_list=[]
sim_num = 129
heartbeat_interval = 3
def start_sims():
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	for i in range(1, sim_num+1):
		print i
		mac_tmp = str(i)
		log = MyLogger(join(log_path,'%s%s.log' % (sim_type, mac_tmp)), clevel=logging.WARN, flevel=logging.ERROR)
		sim = eval(sim_type)
		sim_temp = sim(logger=log, mac=mac_tmp)
		#sim_temp.sdk_obj.heartbeat_interval = heartbeat_interval
		#print sim_temp.sdk_obj.connection.client.settimeout(100)
		sim_temp.run_forever()
		device_online_list.append(sim_temp)

def hold_on():
	while True:
		time.sleep(100)


if __name__ == '__main__':
	start_sims()
	hold_on()