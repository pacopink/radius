#!/bin/env python
#coding:utf8
import pyrad
import redis
from pyrad.eap.key_calculate import *
from pyrad.eap import *
from global_def import *
from dipc_msg import *
import traceback
from greenlet import greenlet
from DipcPy import *
from redis_buffer import *
import time
from radius_id_keeper import RadiusIdKeeper

TIMEOUT_EVENT=4999 #just a magic number 

class DisconnTaskMgr(greenlet):
    def __init__(self, redis_pool, udp_server, cdr_writer, log):
        #Global Context
        self.rp = redis_pool             #the redis pool
        self.timer = timer()             #the timer to set next wait up
        self.cdr_writer = cdr_writer     #the cdr_writer to write cdr
        self.udp_server = udp_server
        self.log = log                   #the logger
        self.task_dict = dict()
        self.idle = True
        self.id_keepers = dict()

    def run(self):
        while True:
            '''此循环处理超时未收到期待的msg的事件'''
            ev = self.timer.get_event()
            if ev != None:
                self.idle = False
                key = ev['id']
                task = self.task_dict[key]
                task.timer_event = ev['ev'] #set timeout event
                task.switch()               #process timeout event
                #if task finished, clean up
                if task.dead:
                    self.task_dict.__delitem__(key)
                    self.timer.delete(ev['id'])
                    self.id_keepers["%s:%d"%(task.dst[0], task.dst[1])].return_id(task.pack.id)
            self.parent.switch()


    def resume_task(self, key, repkt): 
        '''当通过key与此task关联的msg到来，调用此方法继续task的执行'''
        self.log.db("resume_task key[%s]"%key) 
        self.timer.delete(key) #delete timer at first
        try:
            task = self.task_dict[key]
            task.recv_pkt = repkt
            #if task not ended at this switch, save to dict and wait for msg event or timer event
            task.switch()
            #if task finished, clean up
            if task.dead:
                self.task_dict.__delitem__(key)
                self.id_keepers["%s:%d"%(task.dst[0], task.dst[1])].return_id(task.pack.id)
                self.log.db("Task Finished [%s]"%key)
            else:
                self.log.db("Task Not Finished [%s]"%key)

        except KeyError:
            self.log.write_log(WARNING, SUCCESS, "recv key [%s] radius msg [%s], but not found auth task"%key, repkt.raw_packet.encode('hex'))
            

    def set_pack_id(self, dst, pack):
        try:
            id = self.id_keepers[dst].get_id()
        except KeyError:
            self.id_keepers[dst] = RadiusIdKeeper()
            id = self.id_keepers[dst].get_id()
        if id != None:
            pack.id = id
            return True
        else:
            return False
            
    def new_task(self, dst, pack, username, mac, kpi_ticker):
        '''新请求到来，生成一个新的task并执行之,如果执行的结果不是完成而是挂起，
            保存task，等待期待的msg到达被resume或者是超时被处理掉'''
        #new a task with the dst 
        task = DisconnTask(dst, pack, self.log)
        task.rp = self.rp
        task.udp_server = self.udp_server
        task.timer = self.timer
        task.cdr_writer = self.cdr_writer
        task.username = username
        task.mac = mac
        task.kpi_ticker = kpi_ticker
        
        #if task not ended at first switch, save to dict and wait for msg event or timer event
        task.switch()
        #如果未完成只是挂起了，需要保存起来，等待resume或者超时
        if not task.dead:
            self.task_dict[task.key] = task

class DisconnTask(greenlet):
    def __init__(self, dst, pack, log):
        #Global Context
        self.rp = None                   #the redis pool
        self.udp_server = None
        self.timer = None                #the timer to set next wait up
        self.log = log                  #the logger
        self.dst = dst
        self.kpi_ticker = None
        self.cdr_writer = None           #the cdr_writer to write cdr
        self.username = ""               #just for CDR
        self.mac = ""                    #just for CDR

        #Variables to get recvd msg
        self.recv_pkt = None
        self.timer_event = None

        #Local Context
        self.pack = pack
        #this is the key for TaskMgr to refer to current task
        self.key = "%s:%d:%d"%(self.dst[0], self.dst[1], self.pack.id)
        self.log.db("DisconnTask key [%s]"%self.key)


    def run(self):
        '''retry for 4 times'''
        for i in xrange(0, 3): 
            if i == 0:
                self.kpi_ticker.increase_kpi('DISCONN_REQ_SND')
            else:
                self.kpi_ticker.increase_kpi("DISCONN_REQ_RETRY")
            self.udp_server.send((self.pack.Pack(), self.dst))
            #initialze the value
            self.recv_pkt = None
            self.timer_event = None
            #activate timer
            self.timer.activate(id=self.key, timer_type=0, expire=5, event_type=TIMEOUT_EVENT)
            self.parent.switch()#switch to parent, it will wake me up when some event happens
            if self.recv_pkt:
                #if wake up for response comes, proceed the response
                self.cdr_writer.record((self.dst, self.pack, self.recv_pkt, self.username, self.mac))
                return
            elif (self.timer_event == TIMEOUT_EVENT):
                #if wake up for timeout, try again
                continue
        #timeout for all retries, finalize it
        self.kpi_ticker.increase_kpi("DISCONN_REQ_TIMOUT")
        self.cdr_writer.record((self.dst, self.pack, None, self.username, self.mac))
        return 
        
