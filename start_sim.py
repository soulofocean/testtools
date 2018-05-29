# -*- encoding:UTF-8 -*-
import sys
import os
reload(sys)
sys.setdefaultencoding('utf8')
from protocol.wifi_devices import Air,Hanger,Waterfilter,AirFilter,Washer
import logging
from  os.path import join
from basic.log_tool import MyLogger
import time
import random
List_sim=['air','hanger','waterfilter','airfilter','washer']
device_online_list=[]
mac_sample_str="1234567890abcdef"
Sim=''
def start_sim():
    for sim_name in List_sim:
        Sim =None
        if sim_name == 'air':
            for i in range(0,3):
                Log = MyLogger(join('log','%s%s.log' % (sim_name,i)), clevel=logging.CRITICAL, rlevel=logging.WARN)
                Sim = Air
                sim = Sim(logger=Log, mac=''.join(random.sample(mac_sample_str, 12)), time_delay=500)
                sim.run_forever()
                device_online_list.append(sim)
        elif sim_name == 'hanger':
            Log = MyLogger(join('log','%s.log' % (sim_name)), clevel=logging.CRITICAL, rlevel=logging.WARN)
            Sim = Hanger
            sim = Sim(logger=Log, mac=''.join(random.sample(mac_sample_str, 12)), time_delay=500)
            sim.run_forever()
            device_online_list.append(sim)
        elif sim_name == 'waterfilter':
            Log = MyLogger(join('log','%s.log' % (sim_name)), clevel=logging.CRITICAL, rlevel=logging.WARN)
            Sim = Waterfilter
            sim = Sim(logger=Log, mac=''.join(random.sample(mac_sample_str, 12)), time_delay=500)
            sim.run_forever()
            device_online_list.append(sim)
        elif sim_name == 'airfilter':
            Log = MyLogger(join('log','%s.log' % (sim_name)), clevel=logging.CRITICAL, rlevel=logging.WARN)
            Sim = AirFilter
            sim = Sim(logger=Log, mac=''.join(random.sample(mac_sample_str, 12)), time_delay=500)
            sim.run_forever()
            device_online_list.append(sim)
        elif sim_name == 'washer':
            Log = MyLogger(join('log','%s.log' % (sim_name)), clevel=logging.CRITICAL, rlevel=logging.WARN)
            Sim = Washer
            sim = Sim(logger=Log, mac=''.join(random.sample(mac_sample_str, 12)), time_delay=500)
            sim.run_forever()
            device_online_list.append(sim)

def hold_on():
    while True:
        time.sleep(1)

if __name__ =='__main__':
    start_sim()
    os.system('python zb_dev_multiple.py')
    # hold_on()



