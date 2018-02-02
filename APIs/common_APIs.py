# -*- coding: utf-8 -*-

"""common APIs
by Kobe Gong 2017-8-21
use:
    all the funcs can be used by any module should be here
"""

import binascii
import functools
import hashlib
import os
import re
import socket
import struct
import sys
import threading
from binascii import unhexlify
from subprocess import *

import crcmod.predefined


'''
def file_lock(open_file):
    return fcntl.flock(open_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

def file_unlock(open_file):
    return fcntl.flock(open_file, fcntl.LOCK_UN)
'''


def get_output(*popenargs, **kwargs):
    process = Popen(*popenargs, stdout=PIPE, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    return output


def full_output(*popenargs, **kwargs):
    process = Popen(*popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    return output


# run a cmd and check exec result
def my_system(*cmd):
    return check_output(*cmd, universal_newlines=True, shell=True)


# run a cmd without check exec result
def my_system_no_check(*cmd):
    print('run:' + cmd[0])
    return get_output(*cmd, universal_newlines=True, shell=True)


# run a cmd without check exec result
def my_system_full_output(*cmd):
    print('run:' + cmd[0])
    return full_output(*cmd, universal_newlines=True, shell=True)


def register_caseid(casename):
    def cls_decorator(cls):
        def __init__(self, config_file='C:\\ATS\\config.ini', case_id='xxxxxxxx'):
            super(cls, self).__init__(case_id=casename.split('_')[1])

        cls.__init__ = __init__
        return cls
    return cls_decorator


# get all the files match regex 'file_re' from a dir
def get_file_by_re(dir, file_re):
    file_list = []
    if os.path.exists(dir):
        pass
    else:
        print(dir + ' not exist!\n')
        return file_list

    all_things = os.listdir(dir)

    for item in all_things:
        if os.path.isfile(os.path.join(dir, os.path.basename(item))) and re.match(file_re, item, re.S):
            file_list.append(os.path.join(dir, os.path.basename(item)))

        elif os.path.isdir(os.path.join(dir, os.path.basename(item))):
            file_list += get_file_by_re(os.path.join(dir,
                                                     os.path.basename(item)), file_re)

        else:
            continue

    return file_list


# use to copy a dir to another dir
def dir_copy(source_dir, target_dir):
    for f in os.listdir(source_dir):
        sourceF = os.path.join(source_dir, f)
        targetF = os.path.join(target_dir, f)

        if os.path.isfile(sourceF):
            # 创建目录
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # 文件不存在，或者存在但是大小不同，覆盖
            if not os.path.exists(targetF) or (os.path.exists(targetF) and (os.path.getsize(targetF) != os.path.getsize(sourceF))):
                # 2进制文件
                open(targetF, "wb").write(open(sourceF, "rb").read())
            else:
                pass

        elif os.path.isdir(sourceF):
            dir_copy(sourceF, targetF)


# use to make a dir standard
def dirit(dir):
    if not dir.endswith(os.path.sep):
        dir += os.path.sep

    return re.sub(r'%s+' % (re.escape(os.path.sep)), re.escape(os.path.sep), dir, re.S)


# use to add lock befow call the func
def need_add_lock(lock):
    def sync_with_lock(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            lock.acquire()
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()

        return new_func
    return sync_with_lock


# Hex print
def protocol_data_printB(data, title=''):
    if isinstance(data, type(b'')):
        pass
    else:
        data = data.encode('utf-8')
    ret = title + ' %s bytes:' % (len(data)) + '\n\t\t'
    counter = 0
    for item in data:
        if isinstance('', type(b'')):
            ret += '{:02x}'.format(ord(item)) + ' '
        else:
            ret += '{:02x}'.format(item) + ' '
        counter += 1
        if counter == 10:
            ret += ' ' + '\n\t\t'
            counter -= 10

    return ret


# create CRC
def crc(s):
    result = 0
    for i in range(len(s)):
        result += struct.unpack('B', s[i])[0]

    result %= 0xff
    return struct.pack('B', result)


# create CRC16
def crc16(data, reverse=False):
    if isinstance(data, type(b'')):
        pass
    else:
        data = data.encode('utf-8')
    a = binascii.b2a_hex(data)
    s = unhexlify(a)
    crc16 = crcmod.predefined.Crc('crc-ccitt-false')
    crc16.update(s)
    if reverse == False:
        return struct.pack('>H', crc16.crcValue)
    else:
        return struct.pack('<H', crc16.crcValue)


def get_md5(strtext):
    m2 = hashlib.md5()
    m2.update(strtext)
    return str(m2.hexdigest())


def find_max(str_list):
    max_str = '0'
    for item in str_list:
        if int(item) > int(max_str):
            max_str = item
    return max_str


def chinese_show(data):
    coding = sys.getfilesystemencoding()
    if isinstance('', type(u'')):
        tmp_data = data
    else:
        tmp_data = data.decode('utf-8').encode(coding)

    return tmp_data


def get_local_ipv4():
    addrs = socket.getaddrinfo(socket.gethostname(), None)
    return [item[4][0] for item in addrs if ':' not in item[4][0]]


def bit_set(byte, bit):
    temp = struct.unpack('B', byte)[0]
    temp = temp | (1 << bit)
    return struct.pack('B', temp)


def bit_get(byte, bit):
    temp = struct.unpack('B', byte)[0]
    return (temp & (1 << bit))


def bit_clear(byte, bit):
    temp = struct.unpack('B', byte)[0]
    temp = temp & ~(1 << bit)
    return struct.pack('B', temp)


if __name__ == '__main__':
    print(crc16(b'12345678'))
    print(crc16(b'1234567890'))
