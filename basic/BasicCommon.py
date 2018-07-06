#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'ZengXu'
__mtime__ = '2018-7-5'
"""
import functools
import binascii
import struct
import crcmod
import sys
import re
import threading
import logging
import traceback
import os
import time

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

if re.search(r'linux', sys.platform):
    import coloredlogs
    coloredlogs.DEFAULT_DATE_FORMAT = ''
    coloredlogs.DEFAULT_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'
else:
    import ctypes



# Windows CMD命令行 字体颜色定义 text colors
FOREGROUND_BLACK = 0x00  # black.
FOREGROUND_DARKBLUE = 0x01  # dark blue.
FOREGROUND_DARKGREEN = 0x02  # dark green.
FOREGROUND_DARKSKYBLUE = 0x03  # dark skyblue.
FOREGROUND_DARKRED = 0x04  # dark red.
FOREGROUND_DARKPINK = 0x05  # dark pink.
FOREGROUND_DARKYELLOW = 0x06  # dark yellow.
FOREGROUND_DARKWHITE = 0x07  # dark white.
FOREGROUND_DARKGRAY = 0x08  # dark gray.
FOREGROUND_BLUE = 0x09  # blue.
FOREGROUND_GREEN = 0x0a  # green.
FOREGROUND_SKYBLUE = 0x0b  # skyblue.
FOREGROUND_RED = 0x0c  # red.
FOREGROUND_PINK = 0x0d  # pink.
FOREGROUND_YELLOW = 0x0e  # yellow.
FOREGROUND_WHITE = 0x0f  # white.

# Windows CMD命令行 背景颜色定义 background colors
BACKGROUND_BLUE = 0x10  # dark blue.
BACKGROUND_GREEN = 0x20  # dark green.
BACKGROUND_DARKSKYBLUE = 0x30  # dark skyblue.
BACKGROUND_DARKRED = 0x40  # dark red.
BACKGROUND_DARKPINK = 0x50  # dark pink.
BACKGROUND_DARKYELLOW = 0x60  # dark yellow.
BACKGROUND_DARKWHITE = 0x70  # dark white.
BACKGROUND_DARKGRAY = 0x80  # dark gray.
BACKGROUND_BLUE = 0x90  # blue.
BACKGROUND_GREEN = 0xa0  # green.
BACKGROUND_SKYBLUE = 0xb0  # skyblue.
BACKGROUND_RED = 0xc0  # red.
BACKGROUND_PINK = 0xd0  # pink.
BACKGROUND_YELLOW = 0xe0  # yellow.
BACKGROUND_WHITE = 0xf0  # white.

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12

cprint_lock = threading.Lock()

if re.search(r'linux', sys.platform):
    pass
else:
    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)


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


# create CRC16
def crc16(data, reverse=False):
    if isinstance(data, type(b'')):
        pass
    else:
        data = data.encode('utf-8')
    a = binascii.b2a_hex(data)
    s = binascii.unhexlify(a)
    crc16 = crcmod.predefined.Crc('crc-ccitt-false')
    crc16.update(s)
    if reverse == False:
        return struct.pack('>H', crc16.crcValue)
    else:
        return struct.pack('<H', crc16.crcValue)


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


class cprint:
    @need_add_lock(cprint_lock)
    def set_colour(self, color):
        if re.search(r'linux', sys.platform):
            pass  # print('\033[%sm' % self.style[color], end='')
        else:
            ctypes.windll.kernel32.SetConsoleTextAttribute(
                std_out_handle, color)

    def reset_colour(self):
        if re.search(r'linux', sys.platform):
            pass  # print('\033[0m', end='')
        else:
            self.set_colour(FOREGROUND_WHITE)

    def __init__(self, value=' '):
        self.style = {
            FOREGROUND_BLUE: '34',
            FOREGROUND_GREEN: '32',
            FOREGROUND_YELLOW: '33',
            FOREGROUND_PINK: '35',
            FOREGROUND_RED: '31',
            FOREGROUND_WHITE: '37',
        }
        self.name = value

    def common_p(self, string):
        self.set_colour(FOREGROUND_YELLOW)
        print(string)
        self.reset_colour()
        return

    def notice_p(self, string):
        self.set_colour(FOREGROUND_GREEN)
        print(string)
        self.reset_colour()

    def yinfo_p(self, string):
        self.set_colour(FOREGROUND_YELLOW)
        print(string)
        self.reset_colour()

    def debug_p(self, string):
        self.set_colour(FOREGROUND_BLUE)
        print(string)
        self.reset_colour()
        return
        mode = '%s' % self.style['mode'][mode] if mode in self.style['mode'] else self.style['mode']['default']
        fore = '%s' % self.style['fore'][fore] if fore in self.style['fore'] else ''
        back = '%s' % self.style['back'][back] if back in self.style['back'] else ''
        style = ';'.join([s for s in [mode, fore, back] if s])
        style = '\033[%sm' % style
        end = '\033[%sm' % self.style['default']['end']

        try:
            raise Exception
        except:
            f = sys.exc_info()[2].tb_frame.f_back
        print("%s%s [%s line:%s] %s%s" % (style, datetime.datetime.now(), repr(
            os.path.abspath(sys.argv[0])), f.f_lineno, self.name + string, end))

    def warn_p(self, string):
        self.set_colour(FOREGROUND_PINK)
        print(string)
        self.reset_colour()

    def error_p(self, string):
        self.set_colour(FOREGROUND_RED)
        print(string)
        self.reset_colour()

class MyLogger:
    def __init__(self, path, clevel=logging.DEBUG, cenable=True, flevel=logging.DEBUG, fenable=True, rlevel=logging.DEBUG, renable=False):
        if re.search(r'linux', sys.platform):
            coloredlogs.install(level=clevel)

        self.cprint = cprint()
        self.p = logging.getLogger(path)
        self.p.setLevel(logging.DEBUG)
        #fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%m-%d %H:%M:%S')
        self.fmt = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s')

        # 设置CMD日志
        if cenable == True and re.search(r'linux', sys.platform):
            pass
        else:
            self.sh = logging.StreamHandler()
            self.sh.setFormatter(self.fmt)
            self.sh.setLevel(clevel)
            self.p.addHandler(self.sh)

        # 设置文件日志
        if fenable == True:
            self.fh = logging.FileHandler(path)
            self.fh.setFormatter(self.fmt)
            self.fh.setLevel(flevel)
            self.p.addHandler(self.fh)

        # 定义一个RotatingFileHandler，最多备份5个日志文件，每个日志文件最大10M
        if renable == True:
            self.rh = logging.Handler.RotatingFileHandler(
                'system.log', maxBytes=10 * 1024 * 1024, backupCount=5)
            self.rh.setFormatter(self.fmt)
            self.rh.setLevel(rlevel)
            self.p.addHandler(self.rh)

    def set_level(self, clevel=logging.DEBUG):
        self.critical('Change log level to %s' % (str(clevel)))
        self.p.setLevel(clevel)

    def set_fmt(self, fmt=logging.Formatter('')):
        self.sh.setFormatter(fmt)
        self.fh.setFormatter(fmt)
        self.rh.setFormatter(fmt)

    def recover_fmt(self):
        self.sh.setFormatter(self.fmt)
        self.fh.setFormatter(self.fmt)
        self.rh.setFormatter(self.fmt)

    def debug(self, message):
        s = traceback.extract_stack()
        msg_prefix = '[' + \
            os.path.basename(s[-2][0]) + ': ' + str(s[-2][1]) + '] '

        self.cprint.set_colour(FOREGROUND_BLUE)
        self.p.debug(msg_prefix + message)
        self.cprint.reset_colour()

    def info(self, message):
        s = traceback.extract_stack()
        msg_prefix = '[' + \
            os.path.basename(s[-2][0]) + ': ' + str(s[-2][1]) + '] '

        self.cprint.set_colour(FOREGROUND_GREEN)
        self.p.info(msg_prefix + message)
        self.cprint.reset_colour()

    def yinfo(self, message):
        s = traceback.extract_stack()
        msg_prefix = '[' + \
            os.path.basename(s[-2][0]) + ': ' + str(s[-2][1]) + '] '

        self.cprint.set_colour(FOREGROUND_YELLOW)
        self.p.info(msg_prefix + message)
        self.cprint.reset_colour()

    def warn(self, message):
        s = traceback.extract_stack()
        msg_prefix = '[' + \
            os.path.basename(s[-2][0]) + ': ' + str(s[-2][1]) + '] '

        self.cprint.set_colour(FOREGROUND_PINK)
        self.p.warn(msg_prefix + message)
        self.cprint.reset_colour()

    def error(self, message):
        s = traceback.extract_stack()
        msg_prefix = '[' + \
            os.path.basename(s[-2][0]) + ': ' + str(s[-2][1]) + '] '

        self.cprint.set_colour(FOREGROUND_RED)
        self.p.error(msg_prefix + message)
        self.cprint.reset_colour()

    def critical(self, message):
        s = traceback.extract_stack()
        msg_prefix = '[' + \
            os.path.basename(s[-2][0]) + ': ' + str(s[-2][1]) + '] '

        self.cprint.set_colour(FOREGROUND_RED)
        self.p.critical(msg_prefix + message)
        self.cprint.reset_colour()

class Task():
    def __init__(self, name='default-task', logger=None):
        self.tasks = {}
        self.lock = threading.RLock()
        if logger:
            self.LOG = logger
        else:
            self.LOG = MyLogger(name + '.log', clevel=logging.DEBUG)
        self.need_stop = False

    def stop(self):
        self.need_stop = True
        self.LOG.warn('Thread %s stoped!' % (__name__))

    def add_task(self, name, func, run_times=1, interval=5, *argv):
        self.lock.acquire()
        if name and func and int(run_times) >= 1 and int(interval) >= 1:
            pass
        else:
            self.LOG.error("Invalid task: %s, run_times: %d, internal: %d" %
                           (name, int(run_times), int(interval)))
        self.LOG.info("To add task: %s, run_times: %d, internal: %d" %
                      (name, int(run_times), int(interval)))
        self.tasks[name] = {
            'func': func,
            'run_times': int(run_times),
            'interval': int(interval),
            'now_seconds': 0,
            'argv': argv,
            'state': 'active',
            'name': name
        }
        self.lock.release()

    def del_task(self, name):
        self.lock.acquire()
        self.LOG.warn("To delete task:%s" % (name))
        if name in self.tasks:
            del self.tasks[name]
        self.lock.release()

    def show_tasks(self):
        if self.tasks:
            for task in self.tasks:
                self.LOG.info(task + ":")
                for item in sorted(self.tasks[task]):
                    self.LOG.yinfo("    " + item.ljust(20) + ':' +
                                   str(self.tasks[task][item]).rjust(20))
        else:
            self.LOG.warn("No task...")

    def task_proc(self):
        while self.need_stop == False:
            if len(self.tasks) == 0:
                self.LOG.debug("No task!\n")

            '''
            for task in self.tasks:
                if self.tasks[task]['state'] == 'inactive':
                    self.del_task(task)
            '''
            try:
                self.lock.acquire()
                for task in self.tasks:
                    if self.tasks[task]['state'] != 'active':
                        continue
                    self.tasks[task]['now_seconds'] += 1
                    if self.tasks[task]['now_seconds'] >= self.tasks[task]['interval']:
                        if callable(self.tasks[task]['func']):
                            # self.LOG.info("It is time to run %s: " % (
                            #    task) + self.tasks[task]['func'].__name__ + str(self.tasks[task]['argv']))
                            self.tasks[task]['func'](
                                *(self.tasks[task]['argv']))
                        elif callable(eval(self.tasks[task]['func'])):
                            # self.LOG.info("It is time to run %s: " % (
                            #    task) + self.tasks[task]['func'] + str(self.tasks[task]['argv']))
                            eval(self.tasks[task]['func'] + '(*' +
                                 str(self.tasks[task]['argv']) + ')')
                        else:
                            self.LOG.error(
                                "Uncallable task: %s, will disable it!")
                            self.tasks[task]['state'] = 'inactive'
                        self.tasks[task]['now_seconds'] = 0
                        self.tasks[task]['run_times'] -= 1
                        if self.tasks[task]['run_times'] == 0:
                            self.LOG.info("stop task:%s" % (task))
                            self.tasks[task]['state'] = 'inactive'
                    else:
                        pass
                self.lock.release()
                time.sleep(0.01)

            except RuntimeError:
                pass

if __name__ == '__main__':
    pass
