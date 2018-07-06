#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-5'
"""
import random
import json
from abc import abstractmethod
from BasicConn import *
from collections import defaultdict

try:
    import queue as Queue
except:
    import Queue

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class communication_base(object):
    send_lock = threading.Lock()

    def __init__(self, queue_in, queue_out, logger, left_data=b'', min_length=10):
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.LOG = logger
        self.left_data = left_data
        self.min_length = min_length
        self.connection = ''
        self.name = 'some guy'
        self.heartbeat_interval = 3
        self.heartbeat_data = None
        self.need_stop = False

    @abstractmethod
    def protocol_handler(self, msg):
        pass

    @abstractmethod
    def protocol_data_washer(self, data):
        pass

    def run_forever(self):
        thread_list = []
        thread_list.append([self.schedule_loop])
        thread_list.append([self.send_data_loop])
        thread_list.append([self.recv_data_loop])
        thread_list.append([self.heartbeat_loop])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    @abstractmethod
    def msg_build(self):
        pass

    @abstractmethod
    def connection_setup(self):
        pass

    @abstractmethod
    def connection_close(self):
        pass

    def get_connection_state(self):
        return self.connection.get_connected()

    def set_connection_state(self, new_state):
        self.connection.set_connected(new_state)

    @abstractmethod
    def send_data(self, data):
        pass

    @abstractmethod
    def recv_data(self, data):
        pass

    @need_add_lock(send_lock)
    def add_send_data(self, data):
        self.queue_out.put(data)

    @need_add_lock(send_lock)
    def send_data_once(self, data=None):
        if data:
            self.queue_out.put(data)
        if self.queue_out.empty():
            pass
        else:
            while not self.queue_out.empty():
                data = self.queue_out.get()
                self.send_data(data)

    def recv_data_once(self):
        # datas = ''
        # data = self.recv_data()
        # while data:
        #    datas += data
        #    data = self.recv_data()
        datas = self.recv_data()
        if datas:
            self.queue_in.put(datas)
        return datas

    def send_data_loop(self):
        while self.need_stop == False:
            if self.get_connection_state():
                pass
            else:
                if self.connection_setup():
                    pass
                else:
                    time.sleep(1)
                    continue
            self.send_data_once()

    def recv_data_loop(self):
        while self.need_stop == False:
            if self.get_connection_state():
                pass
            else:
                if self.connection_setup():
                    pass
                else:
                    time.sleep(1)
                    continue
            self.recv_data_once()

    def heartbeat_loop(self, debug=True):
        while self.need_stop == False:
            if self.get_connection_state():
                data = self.heartbeat_data
                if not data:
                    self.LOG.debug('No need control heartbeat, I am out!')
                    sys.exit()

                if isinstance(data, type(b'')):
                    tmp_data = data.decode('utf-8')
                else:
                    tmp_data = data
                if debug:
                    self.LOG.yinfo("send msg: " + tmp_data)
                self.send_data_once(data=data)
            else:
                self.LOG.debug('offline?')
            time.sleep(self.heartbeat_interval)

    def schedule_loop(self):
        while self.need_stop == False:
            if self.queue_in.empty():
                continue
            else:
                ori_data = self.left_data + self.queue_in.get()
                while len(ori_data) < self.min_length:
                    ori_data += self.queue_in.get()
                data_list, self.left_data = self.protocol_data_washer(ori_data)
                if data_list:
                    for request_msg in data_list:
                        response_msg = self.protocol_handler(request_msg)
                        if response_msg == 'No_need_send':
                            pass
                        elif response_msg:
                            self.queue_out.put(response_msg)
                        else:
                            self.LOG.error(protocol_data_printB(
                                request_msg, title='%s: got invalid data:' % (self.name)))
                else:
                    continue

    def stop(self):
        self.need_stop = True
        self.LOG.warn('Thread %s stoped!' % (__name__))

    def convert_to_dictstr(self, src):
        if isinstance(src, dict):
            return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        elif isinstance(src, str):
            return json.dumps(json.loads(src), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        elif isinstance(src, bytes):
            return json.dumps(json.loads(src.decode('utf-8')), sort_keys=True, indent=4, separators=(',', ': '),
                              ensure_ascii=False)

        else:
            self.LOG.error('Unknow type(%s): %s' % (src, str(type(src))))
            return None


class Wifi(communication_base):
    state_lock = threading.Lock()

    def __init__(self, logger=None, addr=('192.168.10.1', 65381), time_delay=500, mac='123456',
                 deviceCategory='airconditioner.new', self_addr=None):
        self.queue_in = Queue.Queue()
        self.queue_out = Queue.Queue()
        super(Wifi, self).__init__(self.queue_in, self.queue_out,
                                   logger=logger, left_data=b'', min_length=10)
        self.addr = addr
        self.name = 'WIFI module'
        self.connection = MyClient(
            addr, logger, self_addr=self_addr, debug=False)
        self.state = 'close'
        self.time_delay = time_delay
        self.sim_obj = None
        self.heartbeat_interval = 3
        self.heartbeat_data = '0'

        # state data:
        # 2:short version
        self.version = '\x01\x00'
        # char mac[32]
        # mac = random.randint(100000, 999999)
        self.mac = str(mac) + '\x00' * (32 - len(str(mac)))
        # char manufactureId[34]; // manuafacture name: haier
        manufacture = 'HDiot'
        self.manufacture = manufacture + '\x00' * (34 - len(manufacture))
        # char deviceCategory[34]; // device category: KFR-50LW/10CBB23AU1
        self.deviceCategory = deviceCategory + \
                              '\x00' * (34 - len(deviceCategory))
        # 2:short subCategory; //subCategory: 1
        self.subCategory = '\x01\x00'
        # char deviceModel[34];// device model: KFR-50LW/10CBB23AU1
        self.deviceModel = 'KFR-50LW/10CBB23AU1' + \
                           '\x00' * (34 - len('KFR-50LW/10CBB23AU1'))
        # char firmwareVersion[32];// firmware version
        firmwareVersion = '0.6.8'
        self.firmwareVersion = firmwareVersion + \
                               '\x00' * (32 - len(firmwareVersion))
        # char token[32];
        self.token = 'xx' + '\x00' * (32 - len('xx'))
        # 1:unsigned char wait_added;
        self.wait_added = '\x00'

    def msg_build(self, data):
        # self.LOG.debug(str(data))
        self.LOG.yinfo("send msg: " + self.convert_to_dictstr(data))
        msg_head = self.get_msg_head(data)
        msg_code = '\x01'
        msg_length = self.get_msg_length(msg_code + data + '\x00')
        msg = msg_head + msg_length + msg_code + data + '\x00'
        return msg

    def protocol_data_washer(self, data):
        data_list = []
        left_data = ''

        while data[0] != b'\x77' and len(data) >= self.min_length:
            self.LOG.warn('give up dirty data: %02x' % ord(data[0]))
            data = data[1:]

        if len(data) < self.min_length:
            left_data = data
        else:
            if data[0:4] == b'\x77\x56\x43\xaa':
                length = struct.unpack('>H', data[4:6])[0]
                if length <= len(data[6:]):
                    data_list.append(data[4:4 + length + 2])
                    data = data[4 + length + 2:]
                    if data:
                        data_list_tmp, left_data_tmp = self.protocol_data_washer(
                            data)
                        data_list += data_list_tmp
                        left_data += left_data_tmp
                elif length >= 4:
                    left_data = data
                else:
                    for s in data[:4]:
                        self.LOG.warn('give up dirty data: %02x' % ord(s))
                    left_data = data[4:]
            else:
                pass

        return data_list, left_data

    def get_msg_head(self, msg):
        resp_msg = '\x77\x56\x43\xaa'
        # self.LOG.debug(protocol_data_printB(resp_msg, title="head is:"))
        return resp_msg

    def get_msg_code(self, msg):
        resp_msg = '\x01'
        resp_msg += struct.pack('>B', struct.unpack('>B', msg[3])[0] + 1)
        # for AI Router 0.4.5 should resp_msg += msg[4:6]
        resp_msg += msg[4:6]
        # self.LOG.debug(protocol_data_printB(resp_msg, title="code is:"))
        return resp_msg

    def get_msg_length(self, msg):
        resp_msg = struct.pack('>H', len(msg))
        # self.LOG.debug(protocol_data_printB(resp_msg, title="length is:"))
        return resp_msg

    def protocol_handler(self, msg):
        coding = sys.getfilesystemencoding()
        if msg[2] == b'\x02':
            if msg[3] == b'\x20':
                if msg[4:6] == b'\x00\x05':
                    self.LOG.warn("获取设备信息".decode('utf-8').encode(coding))
                    rsp_msg = ''
                    rsp_msg += self.version
                    rsp_msg += self.mac
                    rsp_msg += self.manufacture
                    rsp_msg += self.deviceCategory
                    rsp_msg += self.subCategory
                    rsp_msg += self.deviceModel
                    rsp_msg += self.firmwareVersion
                    rsp_msg += self.token
                    rsp_msg += self.wait_added
                    msg_head = self.get_msg_head(msg)
                    msg_code = self.get_msg_code(msg)
                    msg_length = self.get_msg_length(msg_code + rsp_msg)
                    return msg_head + msg_length + msg_code + rsp_msg

                elif msg[4:6] == b'\x00\x04':
                    self.LOG.warn("查询设备".decode('utf-8').encode(coding))
                    msg_head = self.get_msg_head(msg)
                    msg_code = self.get_msg_code(msg)
                    msg_length = self.get_msg_length(msg_code)
                    return msg_head + msg_length + msg_code

                elif msg[4:6] == b'\x00\x06':
                    self.LOG.warn("删除设备".decode('utf-8').encode(coding))
                    msg_head = self.get_msg_head(msg)
                    msg_code = self.get_msg_code(msg)
                    msg_length = self.get_msg_length(msg_code)
                    return msg_head + msg_length + msg_code

                else:
                    self.LOG.error('Unknow msg: %s' % (msg[4:6]))
                    return "No_need_send"

            else:
                self.LOG.error('Unknow msg: %s' % (msg[3:6]))
                return "No_need_send"

        elif msg[2] == b'\x03':
            dict_msg = json.loads(msg[3:-1])
            self.LOG.info("recv msg: " + self.convert_to_dictstr(dict_msg))
            time.sleep(self.time_delay / 1000.0)
            rsp_msg = self.sim_obj.protocol_handler(dict_msg)
            if rsp_msg:
                final_rsp_msg = self.msg_build(rsp_msg)
            else:
                final_rsp_msg = 'No_need_send'
            return final_rsp_msg

        else:
            self.LOG.warn('Todo in the feature!')
            return "No_need_send"

    @need_add_lock(state_lock)
    def connection_setup(self):
        self.LOG.warn('Try to connect %s...' % str(self.addr))
        if self.connection.get_connected():
            self.LOG.info('Connection already setup!')
            return True
        elif self.connection.connect():
            self.set_connection_state(True)
            self.LOG.info('Connection setup success!')
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
        self.LOG.debug(protocol_data_printB(
            data, " send data:"))
        return self.connection.send_once(data)

    def recv_data(self):
        datas = self.connection.recv_once()
        if datas:
            self.LOG.debug(protocol_data_printB(
                datas, " recv data:"))
        return datas

    def convert_to_dictstr(self, src):
        if isinstance(src, dict):
            return json.dumps(src, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        elif isinstance(src, str):
            return json.dumps(json.loads(src), sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

        else:
            self.LOG.error('Unknow type(%s): %s' % (src, str(type(src))))
            return None


class ZIGBEE(communication_base):
    status_lock = threading.Lock()
    factory_lock = threading.Lock()

    def __init__(self, port, logger, time_delay=0):
        self.port = port
        self.LOG = logger
        super(ZIGBEE, self).__init__(queue_in=Queue.Queue(),
                                     queue_out=Queue.Queue(), logger=logger, left_data='', min_length=18)
        self.connection = MySerial(port, 115200, logger)
        self.devices = defaultdict(str)
        self.factory = ''
        self.state = 'close'
        self.time_delay = time_delay
        self.heartbeat_interval = 3
        self.heartbeat_data = ''
        self.task_obj = Task('zigbee-UART-task', self.LOG)

        # status data:
        self.head = b'\xaa\x55'
        self.dst_addr = b''
        self.src_addr = b'\x00\x00\xf1'
        self.working = False

    @need_add_lock(factory_lock)
    def set_work_status(self, status):
        if status:
            self.LOG.warn("Set factory in busy status!")
        else:
            self.LOG.warn("Clear factory from busy status!")
        self.working = status

    @need_add_lock(factory_lock)
    def get_work_status(self):
        return self.working

    def set_device(self, factory):
        self.factory = factory
        self.LOG.info("Set factory: %s success!" % (factory.__name__))

    def msg_build(self, datas):
        if len(datas) < 6:
            return 'No_need_send'
        tmp_msg = datas['control'] + datas['seq'] + self.dst_addr + \
                  datas['addr'] + datas['cmd'] + datas['reserve'] + datas['data']

        rsp_msg = self.head
        rsp_msg += struct.pack('<B', len(tmp_msg) + 3)
        rsp_msg += tmp_msg
        rsp_msg += crc16(rsp_msg, reverse=True)
        # self.LOG.yinfo("send msg: " + self.convert_to_dictstr(datas))
        return rsp_msg

    def protocol_data_washer(self, data):
        msg_list = []
        left_data = ''

        while data[0:2] != b'\xaa\x55' and len(data) >= self.min_length:
            self.LOG.warn('give up dirty data: %02x' % ord(data[0]))
            data = data[1:]

        if len(data) < self.min_length:
            left_data = data
        else:
            length = struct.unpack('<B', data[2])[0]
            if length <= len(data[2:]):
                msg_list.append(data[0:2 + length])
                data = data[2 + length:]
                if data:
                    msg_list_tmp, left_data_tmp = self.protocol_data_washer(
                        data)
                    msg_list += msg_list_tmp
                    left_data += left_data_tmp
            elif length > 0:
                left_data = data
            else:
                for s in data[:3]:
                    self.LOG.warn('give up dirty data: %02x' % ord(s))
                left_data = data[3:]

        return msg_list, left_data

    def run_forever(self):
        thread_list = []
        thread_list.append([self.schedule_loop])
        thread_list.append([self.send_data_loop])
        thread_list.append([self.recv_data_loop])
        thread_list.append([self.heartbeat_loop])
        thread_list.append([self.task_obj.task_proc])
        thread_ids = []
        for th in thread_list:
            thread_ids.append(threading.Thread(target=th[0], args=th[1:]))

        for th in thread_ids:
            th.setDaemon(True)
            th.start()

    def protocol_handler(self, msg):
        if msg[0:2] == b'\xaa\x55':
            length = struct.unpack('B', msg[2:2 + 1])[0]
            control = msg[3:3 + 1]
            seq = msg[4:4 + 1]
            dst_addr = msg[5:5 + 3]
            src_addr = msg[8:8 + 3]
            self.dst_addr = src_addr
            # self.src_addr = dst_addr
            cmd = msg[11:11 + 5]
            if dst_addr == b'\x00\x00\x00':
                self.LOG.error('Unknow address!')
                return 'No_need_send'

            if dst_addr in self.devices:
                pass
            else:
                if self.factory and self.get_work_status() == False:
                    self.set_work_status(True)
                    self.task_obj.add_task(
                        'reset factory status', self.set_work_status, 1, 500, False)
                    mac = ''.join(random.sample('0123456789abcdef', 3))
                    short_id = chr(random.randint(0, 255)) + \
                               chr(random.randint(0, 255))
                    Endpoint = b'\x00'
                    dst_addr = short_id + Endpoint
                    self.devices[dst_addr] = self.factory(
                        logger=self.LOG, mac=mac, short_id=short_id, Endpoint=Endpoint)
                    self.devices[dst_addr].sdk_obj = self
                    self.devices[dst_addr].run_forever()
                    self.devices[short_id + b'\x01'] = self.devices[dst_addr]
                    self.LOG.warn("It is time to create a new zigbee device, type: %s, mac: %s" % (
                        self.factory.__name__, mac))
                else:
                    self.LOG.error("Factory busy!")
                    data_length = length - 16
                    data = msg[-2 - data_length:-2]
                    datas = {
                        'control': bit_set(control, 7),
                        'seq': seq,
                        'addr': dst_addr,
                        'cmd': cmd,
                        'reserve': b'',
                        'data': data,
                    }
                    return self.msg_build(datas)

            have_reserve_flag = bit_get(control, 3)
            if have_reserve_flag:
                reserve_length = struct.unpack('B', msg[16:16 + 1])[0]
                data_length = length - reserve_length - 16
                reserve_data = msg[16:16 + reserve_length]
            else:
                reserve_length = 0
                data_length = length - 16
                reserve_data = b''
            data = msg[-2 - data_length:-2]

            datas = {
                'control': control,
                'seq': seq,
                'addr': dst_addr,
                'cmd': cmd,
                'reserve': reserve_data,
                'data': data,
            }
            # self.LOG.info("debug recv msg: " + self.convert_to_dictstr(datas))
            time.sleep(self.time_delay / 1000.0)
            rsp_datas = self.devices[dst_addr].protocol_handler(datas)
            rsp_msg = ''
            if rsp_datas:
                if isinstance(rsp_datas, list):
                    for rsp in rsp_datas:
                        rsp_msg += self.msg_build(rsp)
                else:
                    rsp_msg = self.msg_build(rsp_datas)
            else:
                rsp_msg = 'No_need_send'
            return rsp_msg

        else:
            self.LOG.warn('Unknow msg: %s!' % (msg))
            return "No_need_send"

    @need_add_lock(status_lock)
    def connection_setup(self):
        self.LOG.warn('Try to open port %s...' % (self.port))
        if self.connection.is_open():
            self.LOG.info('Connection already setup!')
            return True
        elif self.connection.open():
            self.set_connection_state('online')
            self.LOG.info('Setup connection success!')
            return True
        else:
            self.LOG.warn(self.port + " can't open!")
            self.LOG.error('Setup connection failed!')
            return False

    def connection_close(self):
        if self.connection.close():
            self.connection = None
            self.set_connection_state('offline')
        else:
            self.LOG.error('Close connection failed!')

    def send_data(self, data):
        self.LOG.yinfo(protocol_data_printB(
            data, title=self.port + " send data:"))
        return self.connection.write(data)

    def recv_data(self):
        datas = self.connection.readall()
        if datas:
            self.LOG.info(protocol_data_printB(
                datas, title=self.port + " recv data:"))
        return datas

    def convert_to_dictstr(self, src):
        ret_str = ''
        ret_str += '\n{\n'
        for item in src:
            ret_str += protocol_data_printB(src[item],
                                            title="    %s," % (item))
            ret_str += '\n'
        ret_str += '}'
        return ret_str


if __name__ == '__main__':
    pass
