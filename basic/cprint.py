#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""colour print tool
by Kobe Gong. 2017-8-21
"""

import datetime
import os
import re
import sys
import threading

import APIs.common_APIs as common_APIs

if sys.platform == 'linux':
    pass
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


class cprint:
    @common_APIs.need_add_lock(cprint_lock)
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


if __name__ == '__main__':
    p = cprint('test')
    p.debug_p("this is ok?")
    p.error_p("this is ok?")
    p.warn_p("this is ok?")
    p.notice_p("this is ok?")
    p.common_p("this is ok?")
