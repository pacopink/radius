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
import Queue

QUEUE_NAME="PROTAL_ACCT_SESSION_EVENT"

class AccountTaskMgr(greenlet):
    def __init__(self, redis_pool, ep_mgr, cdr_writer, log):
        #Global Context
        self.rp = redis_pool             #the redis pool
        self.ep_mgr = ep_mgr             #the ep_mgr to send out msg
        self.timer = timer()             #the timer to set next wait up
        self.cdr_writer = cdr_writer     #the cdr_writer to write cdr
        self.log = log                   #the logger
        self.task_dict = dict()
        self.idle = True
        #2 Redis objects
        self.acct_event_queue = AcctSessionEventQueue(self.rp)
        self.acct_session_hash = AcctSession(self.rp)
        
        #redis buffer
        self.radius_client_rs = RadiusClient(redis_pool)
        self.user_profile_rs = UserProfile(redis_pool)
        self.reload_redis_buffers()
        
    def reload_redis_buffers(self):
        self.reload_flag = True
        ret1 = self.radius_client_rs.reload()
        if not ret1:
            self.log.write_log(WARNING, 0, "Reload Radius Client info from Redis failed, waiting for retry")
        ret2 = self.user_profile_rs.reload()
        if not ret2:
            self.log.write_log(WARNING, 0, "Reload User Profile from Redis failed, waiting for retry")

        #if all reload successfully, reset the flag to false
        if (ret1 and ret2):
            self.log.write_log(INFO, 0, "Reload All Info from Redis successful")
            self.reload_flag = False

    def run(self):
        last_reload_time =  time.time()
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
            self.parent.switch()

            #if reload_flag is on and 10s after last reload try
            now = time.time()
            if self.reload_flag and now - last_reload_time>10:
                self.reload_redis_buffers()
                last_reload_time = now

    def resume_task(self, key, recv_msg_type, recv_msg, subkey=None, sender=None):
        '''当通过key与此task关联的msg到来，调用此方法继续task的执行'''
        self.timer.delete(key) #delete timer at first
        try:
            task = self.task_dict[key]
            task.recv_msg_type = recv_msg_type
            task.recv_msg = recv_msg
            task.subkey = subkey
            if sender:
                task.sender = sender #update sender
            #if task not ended at this switch, save to dict and wait for msg event or timer event
            task.switch()
            #if task finished, clean up
            if task.dead:
                self.task_dict.__delitem__(key)
        except KeyError:
            self.log.write_log(WARNING, SUCCESS, "recv msg_type [%s] key [%s] msg [%s], but not found auth task"%recv_msg_type, key.encode('hex'), recv_msg.encode('hex'))

            
    def new_task(self, key, from_host, sender, pack, kpi_ticker):
        '''新请求到来，生成一个新的task并执行之,如果执行的结果不是完成而是挂起，
            保存task，等待期待的msg到达被resume或者是超时被处理掉'''
        #new a task with the key and shared_key
        task = AccountTask(key, from_host)
        task.rp = self.rp
        task.ep_mgr = self.ep_mgr
        task.timer = self.timer
        task.cdr_writer = self.cdr_writer
        task.log = self.log
        task.sender_autt = sender
        task.pack = pack
        task.radius_client_rs = self.radius_client_rs
        task.user_profile_rs = self.user_profile_rs
        task.acct_event_queue = self.acct_event_queue
        task.acct_session_hash = self.acct_session_hash
        task.kpi_ticker = kpi_ticker
        
        #if task not ended at first switch, save to dict and wait for msg event or timer event
        task.switch()
        #如果未完成只是挂起了，需要保存起来，等待resume或者超时
        if not task.dead:
            self.task_dict[task.key] = task

class AccountTask(greenlet):
    def __init__(self, key, from_host):
        #Global Context
        self.rp = None                   #the redis pool
        self.ep_mgr = None               #the ep_mgr to send out msg
        self.timer = None                #the timer to set next wait up
        self.cdr_writer = None           #the cdr_writer to write cdr
        self.log = None                  #the logger
        self.radius_client_rs = None
        self.user_profile_rs = None
        self.key = key                   #the key pass in for Authenticator if need to set timer
        self.subkey = None
        self.from_host = from_host
        self.acct_event_queue = None
        self.acct_session_hash = None
        self.kpi_ticker = None

        #Variables to get recvd msg
        self.recv_msg_type = None
        self.recv_msg = None
        self.timer_event = None

        #Local Context
        self.pack = None
        self.username = ''
        self.mac = ''
        self.user_type = 'UNKNOWN'
        self.user_info = None      #User Profile Info from Redis
        self.cli = None            #Radius Client Info from Redis

    def save_session(self):
        '''Save current session to Redis'''
        try:
            nas_addr = self.pack["NAS-IP-Address"][0]
        except:
            nas_addr = self.from_host
        try:
            nas_port = int(self.cli['DISCONN_PORT'])
        except:
            nas_port = 3799  #if not configured, use the default port
        secret = self.pack.secret

        try:
            acct_session_id = self.pack["Acct-Session-Id"][0]
        except:
            acct_session_id = None
            self.log.write_log(WARNING, 0, "Failed to disconnect a session without Acct-Session-Id Attribute")
            return

        try:
            acct_multi_session_id = self.pack["Acct-Multi-Session-Id"][0]
        except:
            acct_multi_session_id = None

        disc_msg = DisconnMsg()
        disc_msg.header = self.key
        #print "========== ARGS ========="
        #print nas_addr
        #print type(nas_addr)
        #print nas_port
        #print type(nas_port)
        #print secret
        #print type(secret)
        #print acct_session_id
        #print type(acct_session_id)
        #print acct_multi_session_id
        #print type(acct_multi_session_id)
        self.acct_session_hash.save_session(self.username, self.mac, nas_addr, nas_port, secret, acct_session_id, acct_multi_session_id)

    def report_event_2_cp(self):
        try:
            status = self.pack["Acct-Status-Type"][0]
            if status not in ('Start', 'Stop'):
                #only report start/stop event
                #print "XXXXXXXXXX: status [%d]"%status_type
                return
        except:
            print "XXXXXXXXXX: no Acct-Status-Type attribute"
            print self.pack
            return

        try:
            acct_session_id = self.pack["Acct-Session-Id"][0]
        except:
            acct_session_id = '' 

        try:
            acct_multi_session_id = self.pack["Acct-Multi-Session-Id"][0]
        except:
            acct_multi_session_id = ''
    
        ts = self.cdr_writer.get_timestamp()
        #print "XXXXXXXXXX: put to queue"
        self.acct_event_queue.notify("%s$%s$%s$%s$%s$%s"%(self.mac.replace('-',''), self.username, status, ts, acct_session_id, acct_multi_session_id))

    def send2mirror(self):
        #get first available MIRROR endpoint
        dln = self.ep_mgr.get_available_ep_fix('MIRROR')  
        if dln:
            self.ep_mgr.send_msg(MT_ACCT_2_ACCP, dln, self.key+self.pack.raw_packet)

    def run(self):
        #if msg_authenticator not correct, discard the request silently
        if not self.check_msg_authenticator():
            self.kpi_ticker.increase_kpi('ACCOUNT_INVALID')
            self.log.write_log(DEBUG, 0, "VerifyAcctRequest failed")
            #also write a record
            self.cdr_writer.record((self.pack, None, '', 'Authenticator check failed'))
            return
        
        #only send msg_authenticator check passed msg to mirror 
        self.send2mirror()

        ret = self.account(self.pack)
        reply = None
        if ret[0]:
            reply = self.pack.CreateReply()
            reply.code = CODE_ACCOUNT_RESPONSE
            self.ep_mgr.send_msg(MT_ACCP_2_ACCT, self.sender_autt , self.key+reply.Pack()) #the key shall be add in prefix
            self.kpi_ticker.increase_kpi("ACCOUNT_ACK_SND")
            self.cdr_writer.record((self.pack, reply, self.user_type, ''))
        else:
            self.kpi_ticker.increase_kpi('ACCOUNT_INVALID')
            self.cdr_writer.record((self.pack, reply, self.user_type, ret[1]))
            return
        

        #report start/stop event to Captive Portal
        self.report_event_2_cp()
        #update session status to Redis
        try:
            if self.pack["Acct-Status-Type"][0] == 'Stop':
                self.acct_session_hash.delete_session_by_username_mac(self.username, self.mac)
            else:
                self.save_session()
        except:
            print ("%s: %s"%(e, traceback.format_exc()))

    def check_msg_authenticator(self):
        try:
            #print "self.from_host [%s]"%self.from_host.encode('hex')
            cli = self.radius_client_rs[self.from_host]
            self.log.db("find client:%s"% cli.__repr__())
            secret = cli['SECRET']
            try:
                need_message_auth = (cli['REQ_MESSAGE_AUTHENTICATOR'] == 'Y')
            except:
                need_message_auth = False 
            self.pack.secret = secret
            self.cli = cli
        except Exception,e:
            print ("%s: %s"%(e, traceback.format_exc()))
            self.log.write_log(WARNING, SUCCESS, "cannot find client information from host [%s]"%self.from_host)
            return False

        if not self.pack.VerifyAcctRequest():
            self.log.write_log(DEBUG, 0, "invalid authenticator value discard msg")
            return False
        else:
            return True
        
    def get_user_info(self):
        try:
            r = redis.Redis(connection_pool=self.rp)
            self.user_info = r.hgetall("PORTAL_"+self.username)
            self.log.db("find user_info: %s"% self.user_info.__repr__())
            self.user_type = self.user_info["TYPE"]
            return True
        except Exception,e:
            print ("%s: %s"%(e, traceback.format_exc()))
            self.log.write_log(WARNING, SUCCESS, "Failed to get_user_info for [%s][%s]"%(self.mac, self.username))
            return False
        
    def account(self, pack):
        #get username and MAC from attributes
        try:
            self.username = self.pack[ATTR_USER_NAME][0]
        except KeyError:
            return (False, "UserName not exist in access request")

        try:
            self.mac = self.pack[ATTR_CALLING_STATION_ID][0]
        except KeyError:
            return (False, "Calling-Station-ID not exist in access request")

        #get the user info from Portal, use MAC + Username as key
        if not self.get_user_info():
            return (False, "Failed to find user info")

        #get user_profile from type
        try:
            self.profile = self.user_profile_rs[self.user_type]
            return (True, "OK")
        except KeyError:
            self.log.write_log(WARNING, SUCCESS, "Unknown user profile for type:%s"%self.user_type)
            return (False, "Unknown user profile for type:%s"%self.user_type)
