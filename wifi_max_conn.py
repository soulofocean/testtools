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
import psutil
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

def get_net_card_disp():
	info = psutil.net_if_addrs()
	for k,v in info.items():
		print k
		for vv in v:
			print "\t" + str(vv)
			for vvv in vv:
				print "\t\t" + str(vvv)

	info2 = psutil.net_if_stats()
	for k,v in info2.items():
		print k
		for vv in v:
			print "\t" + str(vv)

def get_net_card_ipv4_addr():
	card_info_dict = {}
	card_info_dict["connected"] = {}
	card_info_dict["dis_connected"] = {}
	addr_info = psutil.net_if_addrs()
	status_info = psutil.net_if_stats()
	for k, v in addr_info.items():
		mac = ''
		for vv in v:
			if(vv[0] == -1):
				mac = vv[1]
			#过滤掉非IPV4地址和LoopBack端口
			if (vv[0] == 2 and vv[1] != '127.0.0.1'):
				if(status_info[k][0]):
					card_info_dict["connected"][k]= {
						"ipv4" : vv[1],
						"mac" : mac
					}
				else:
					card_info_dict["dis_connected"][k] = {
						"ipv4": vv[1],
						"mac": mac
					}
	return card_info_dict

def card_info_dict_disp(card_info_dict):
	for k, v in card_info_dict.items():
		print k
		for vk, vv in v.items():
			print "\t" + vk
			for vvk, vvv in vv.items():
				print "\t\t" + vvk
				print "\t\t" + vvv

def get_ipaddr

if __name__ == '__main__':
	#start_sims()
	#hold_on()
	#get_net_card_disp()
	card_info_dict = get_net_card_ipv4_addr()
	card_info_dict_disp(card_info_dict)
	for v in card_info_dict["conn'"]
