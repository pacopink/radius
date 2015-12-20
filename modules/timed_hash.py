#!/bin/env python

from DipcPy import *
import threading
import time

class TimedHash(dict):
    def __init__(self):
        self.timer = timer()
        self.t = None

    def start(self):
        self.flag = True
        self.t = threading.Thread(target = self.svc)
        self.t.start() 

    def stop(self):
        self.flag = False
        if self.t:
            self.t.join()
            self.t = None

    def set(self, id, value, expire=None):
        self[id] = value
        if expire!=None:
            self.timer.activate(id=id, timer_type=0, expire=expire, event_type=0)

    def expire(self, id, expire):
        '''update the timer'''
        if self.has_key(id):
            self.timer.activate(id=id, timer_type=0, expire=expire, event_type=0)
            return True
        else:
            return False
    
    def svc(self):
        while self.flag:
            ev = self.timer.get_event()
            if ev != None:
                try:
                    #print "%f: id[%s]"%(time.time(), ev['id'])
                    self.timer.delete(ev['id'])
                    self.__delitem__(ev['id'])
                except Exception,e:
                    print "TimedHash.svc exception: %s"%e
            else:
                time.sleep(0.1)
            
            

if __name__=="__main__":
    hh = TimedHash()
    hh.start()
    print "%f"%time.time()
    hh.set("A", "AAAAAA")
    hh.set("B\0\0", "BBBBBB", expire = 1)
    hh.set("C", "CCCCCC", expire = 5)
    hh.set("\0\0F\0\0", "FFFFFF", expire = 5)
    hh.set("D", "DDDDDD", expire = 20)
    hh.set("E", "EEEEEE", expire = 0)

    try:
        print "%f"%time.time()
        print hh
        time.sleep(3)
        print "%f"%time.time()
        print hh
        hh.expire("F", 5)
        time.sleep(4)
        print "%f"%time.time()
        print hh
        time.sleep(5)
        print "%f"%time.time()
        print hh
        time.sleep(10)
        print "%f"%time.time()
        print hh
    except:
        pass
    hh.stop()
