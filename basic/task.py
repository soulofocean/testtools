#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""task handle
by Kobe Gong. 2018-1-2
"""

import logging
import os
import re
import struct
import sys
import threading
import time

from basic.log_tool import MyLogger

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


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
    def show(arg):
        print(arg)
    task_sche = Task()
    task_sche.add_task('task test', 'show', 3, 5, 'hello world')
    task_sche.add_task('task test2', show, 4, 2, 'go to die')
    task_sche.add_task('show task', task_sche.show_tasks, 100, 2)
    task_sche.show_tasks()
    task_sche.task_proc()
