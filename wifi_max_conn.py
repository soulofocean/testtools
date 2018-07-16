#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-5-25'
"""
import sys
import subprocess
reload(sys)
sys.setdefaultencoding("utf-8")
from protocol.wifi_devices import Air
import logging
from  os.path import join
from basic.log_tool import MyLogger
import os
import time
import psutil
import ConfigParser

cf = ConfigParser.ConfigParser()
cf.read('test.conf')

sim_type = "Air"#要启动的设备类型
log_path = "wifi_mul_dev_log"#LOG文件存放的目录
device_online_list=[]
sim_num = 128#要启动的设备数
start_port = cf.get('wifi','start_port')#预设的设备端口数
bind_self = True
force_dev_num = True
show_net_card = eval(cf.get('wifi','show_net_card'))
# [disconnect_while_show,connect_while_show]
# [True,False]:disconnect all wifi
# [False,True]:connect all wifi
rout_addr = (cf.get('wifi','rout_addr'), 65381)
disconnect_while_show = eval(cf.get('wifi','disconnect_while_show'))
disconnect_interval = cf.get('wifi','disconnect_interval')
connect_while_show = eval(cf.get('wifi','connect_while_show'))
connect_interval = cf.get('wifi','connect_interval')
ssid = cf.get('wifi','ssid')
wifi_file = cf.get('wifi','wifi_file')
mac_prefix = cf.get('wifi','mac_prefix')
cl_level = cf.get('wifi','cl_level')
fl_level = cf.get('wifi','fl_level')
start_one_by_one = False
#heartbeat_interval = 3
def start_sims():
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	addr_len = 0
	if bind_self:
		addr_list = get_connected_ipv4_list()
		addr_len = len(addr_list)
	for i in range(0, sim_num):
		mac_tmp = mac_prefix + sim_type+"mac"+str(i)
		log = MyLogger(join(log_path,'%s%s.log' % (sim_type, mac_tmp)),
					   clevel=eval(cl_level), flevel=eval(fl_level))
		log.warn("device mac:%s" % (mac_tmp,))
		sim = eval(sim_type)
		if bind_self and addr_len > 0:
			if force_dev_num and i >= addr_len:
				log.error("devices should not more than net cards number!")
				break
			addr_index = i % (addr_len)
			sim_temp = sim(logger=log, mac=mac_tmp, addr=rout_addr,
						   self_addr=(addr_list[addr_index], int(start_port) + i))
		else:
			log.error("no any net card is connected!")
			sys.exit(-666)
			#sim_temp = sim(logger=log, mac=mac_tmp)
		#sim_temp.sdk_obj.heartbeat_interval = heartbeat_interval
		sim_temp.run_forever()
		device_online_list.append(sim_temp)
		if start_one_by_one:
			log.warn("press any key to start next devices")
			raw_input()

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
		#过滤掉虚拟机的网卡和本地有线网卡
		if 'VMware' in k or 'HDLocal' in k:
			continue
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

def get_connected_ipv4_list():
	addr_list=[]
	addr_info = psutil.net_if_addrs()
	status_info = psutil.net_if_stats()
	for k, v in addr_info.items():
		# 过滤掉虚拟机的网卡和本地有线网卡
		if 'VMware' in k or 'HDLocal' in k:
			continue
		for vv in v:
			# 过滤掉非IPV4地址和LoopBack端口
			if (vv[0] == 2 and vv[1] != '127.0.0.1'):
				if (status_info[k][0]):
					addr_list.append(vv[1])
	return addr_list

def card_info_dict_disp(card_info_dict):
	for k, v in card_info_dict.items():
		print k
		for vk, vv in v.items():
			print "\t" + vk
			for vvk, vvv in vv.items():
				print "\t\t" + vvk
				print "\t\t" + vvv

def connect_wifi_by_netsh(iface, wifi_ssid=ssid,wifi_file=wifi_file):
	#netsh wlan connect name=BeeBox_039696 ssid=BeeBox_039696 interface=RTL8192CU_1
	subprocess.call("netsh wlan connect name=%s ssid=%s interface=\"%s\"" % (wifi_file, wifi_ssid, iface), shell=True)

def disconnect_wifi_by_netsh(iface):
	#netsh wlan disconnect interface=RTL8192CU_1
	subprocess.call("netsh wlan disconnect interface=\"%s\"" % (iface,), shell=True)

def connect_wifi():
	card_info_dict = get_net_card_ipv4_addr()
	for card in card_info_dict["connected"].keys():
		print "Connecting:",card
		connect_wifi_by_netsh(card)
		time.sleep(float(connect_interval))
	for card in card_info_dict["dis_connected"].keys():
		print "Connecting:", card
		connect_wifi_by_netsh(card)
		time.sleep(float(connect_interval))

def dis_connect_wifi():
	card_info_dict = get_net_card_ipv4_addr()
	for card in card_info_dict["connected"].keys():
		print "DisConnecting:",card
		disconnect_wifi_by_netsh(card)
		time.sleep(float(disconnect_interval))

if __name__ == '__main__':
	if show_net_card:
		card_info_dict = get_net_card_ipv4_addr()
		card_info_dict_disp(card_info_dict)
		if disconnect_while_show:
			dis_connect_wifi()
		if connect_while_show:
			connect_wifi()
		card_info_dict = get_net_card_ipv4_addr()
		card_info_dict_disp(card_info_dict)
			#time.sleep(5)
			#disconnect_wifi_by_netsh('RTL8192CU_1')
	#for k,v in card_info_dict["connected"].items():
	#	print k
	#	for kk,vv in v.items():
	#		print "\t"+kk
	#		print "\t"+vv
	#	print v["ipv4"]
	#addr_l = get_connected_ipv4_list()
	#print addr_l
	else:
		start_sims()
		hold_on()