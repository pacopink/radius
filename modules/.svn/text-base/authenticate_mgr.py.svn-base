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

supported_type = ['VISITOR',]
need_to_check_mac_type = ['VISITOR',]

class AuthenticateTaskMgr(greenlet):
    def __init__(self, redis_pool, ep_mgr, cdr_writer, log):
        #Global Context
        self.rp = redis_pool             #the redis pool
        self.ep_mgr = ep_mgr             #the ep_mgr to send out msg
        self.timer = timer()             #the timer to set next wait up
        self.cdr_writer = cdr_writer     #the cdr_writer to write cdr
        self.log = log                   #the logger
        self.task_dict = dict()
        self.idle = True
        
        #redis buffer
        self.radius_client_rs = RadiusClient(redis_pool)
        self.user_profile_rs = UserProfile(redis_pool)
        self.reload_redis_buffers()
        self.disconnect_queue = DisconnectQueue(redis_pool)
        self.acct_session_hash = AcctSession(redis_pool)
        
    #def __del__(self):
    #    self.timer.stop()

    def reload_redis_buffers(self):
        self.last_reload = time.time() #record the last try time, to control retry interval
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
            if self.reload_flag and time.time - self.last_reload>10:
                self.reload_redis_buffers()

    def resume_task(self, key, recv_msg_type, recv_msg):
        '''当通过key与此task关联的msg到来，调用此方法继续task的执行'''
        self.timer.delete(key) #delete timer at first
        try:
            task = self.task_dict[key]
            task.recv_msg_type = recv_msg_type
            task.recv_msg = recv_msg
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
        task = AuthenticateTask(key, from_host)
        task.rp = self.rp
        task.ep_mgr = self.ep_mgr
        task.timer = self.timer
        task.cdr_writer = self.cdr_writer
        task.log = self.log
        task.sender_autt = sender
        task.pack = pack
        task.radius_client_rs = self.radius_client_rs
        task.user_profile_rs = self.user_profile_rs
        task.disconnect_queue = self.disconnect_queue
        task.acct_session_hash = self.acct_session_hash
        task.kpi_ticker = kpi_ticker
        
        #if task not ended at first switch, save to dict and wait for msg event or timer event
        task.switch()
        #如果未完成只是挂起了，需要保存起来，等待resume或者超时
        if not task.dead:
            self.task_dict[task.key] = task

class AuthenticateTask(greenlet):
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
        self.from_host = from_host
        self.kpi_ticker = None

        #Variables to get recvd msg
        self.recv_msg_type = None
        self.recv_msg = None
        self.timer_event = None

        #Local Context
        self.pack = None
        self.username = ''
        self.mac = ''
        self.user_info = None
        self.user_type = 'UNKNOWN'
        #Redis Adapters to be passed in via task manager
        self.disconnect_queue = None
        self.acct_session_hash = None

        #Authentication Methods
        self.auth_method = 'UNKNOWN'

    def send2mirror(self):
        #get first available MIRROR endpoint
        dln = self.ep_mgr.get_available_ep_fix('MIRROR')  
        if dln:
            self.ep_mgr.send_msg(MT_AUTT_2_AUTP, dln, self.key+self.pack.raw_packet)

    def run(self):
        #if msg_authenticator not correct, discard the request silently
        if not self.check_msg_authenticator():
            self.kpi_ticker.increase_kpi('ACCESS_INVALID')
            #also write a record
            self.cdr_writer.record((self.pack, None, None, self.user_type))
            return
        
        #only send msg_authenticator check passed msg to mirror 
        self.send2mirror()

        ret = self.authenticate(self.pack)
        reply = self.pack.CreateReply()
        if ret[0]:
            self.disconnect_existing_session() #disconnect existing sessions before accept
            reply.code = CODE_ACCESS_ACCEPT
            #set profile when accept, use try block to skip exception
            self.log.db("PROFILE: %s"%self.profile)
            try:
                reply['Idle-Timeout'] = int(self.profile['Idle-Timeout'])
            except:
                pass
            try:
                reply['Session-Timeout'] = int(self.profile['Session-Timeout'])
            except:
                pass
            try:
                reply['WISPr-Bandwidth-Max-Up'] = int(self.profile['WISPr-Bandwidth-Max-Up'])
            except:
                pass
            try:
                reply['WISPr-Bandwidth-Max-Down'] = int(self.profile['WISPr-Bandwidth-Max-Down'])
            except:
                pass


            self.kpi_ticker.increase_kpi('ACCESS_ACCEPT_SND')
        else:
            reply.code = CODE_ACCESS_REJECT
            reply['Reply-Message'] = ret[1]
            self.kpi_ticker.increase_kpi('ACCESS_REJECT_SND')

        self.log.db("Auth response sent user[%s] code[%d]"%(self.username, reply.code))
        self.ep_mgr.send_msg(MT_AUTP_2_AUTT, self.sender_autt , self.key+reply.Pack()) #the key shall be decoded
        self.cdr_writer.record((self.pack, reply, self.user_type, self.auth_method))

    def check_msg_authenticator(self):
        try:
            #print "self.from_host [%s]"%self.from_host.encode('hex')
            cli = self.radius_client_rs[self.from_host]
            #print cli
            secret = cli['SECRET']
            try:
                need_message_auth = (cli['REQ_MESSAGE_AUTHENTICATOR'] == 'Y')
            except:
                need_message_auth = False
            self.pack.secret = secret
        except Exception,e:
            print ("%s: %s"%(e, traceback.format_exc()))
            self.log.write_log(WARNING, SUCCESS, "cannot find client information from host [%s]"%self.from_host)
            return False

        try:
            #print self.pack
            msg_auth = self.pack['Message-Authenticator'][0]
        except (AttributeError, KeyError):
            if need_message_auth:
                self.log.write_log(WARNING, SUCCESS, "client [%s] requires Message-Authenticator verification, but packet does not contains this attribute"%self.from_host)
                return False
            else:
                #msg_auth not required
                return True

        buffer = self.pack.raw_packet.replace(self.pack['Message-Authenticator'][0], "\x00"*16)
        expect_msg_auth = get_message_authenticator(secret, buffer)
        if expect_msg_auth == msg_auth:
            return True
        else:
            self.log.write_log(WARNING, SUCCESS, "client [%s] Message-Authenticator does not match expect[%s] but get[%s], discard it"%(self.from_host, expect_msg_auth, msg_auth))
            return False
        
    def get_user_info(self):
        try:
            r = redis.Redis(connection_pool=self.rp)
            #self.log.write_log(INFO, SUCCESS, "KEY: %s"%"PORTAL_"+self.mac+":"+self.username)
            #self.user_info = r.hgetall("PORTAL_"+self.mac+":"+self.username)
            self.log.db("KEY: %s"%"PORTAL_"+self.username)
            self.user_info = r.hgetall("PORTAL_"+self.username)
            #print self.user_info
            self.user_type = self.user_info["TYPE"]
            return True
        except Exception,e:
            print ("%s: %s"%(e, traceback.format_exc()))
            self.log.write_log(WARNING, SUCCESS, "Failed to get_user_info for [%s][%s]"%(self.mac, self.username))
            return False
        
    def authenticate(self, pack):
        #get username and MAC from attributes
        try:
            self.username = self.pack[ATTR_USER_NAME][0]
        except KeyError:
            return (False, "UserName not exist in access request")

        try:
            self.mac = self.pack[ATTR_CALLING_STATION_ID][0]
        except KeyError:
            return (False, "Calling-Station-ID not exist in access request")

        #get the user info from Portal, use PORTAL_[Username] as key
        if not self.get_user_info():
            return (False, "Failed to find user info")

        #get user_profile from type
        try:
            self.profile = self.user_profile_rs[self.user_type]
        except KeyError:
            self.profile = None
            self.log.write_log(WARNING, SUCCESS, "Unknown user profile for type:%s"%self.user_type)
            return (False, "Unknown user profile for type:%s"%self.user_type)

        #dynamically bind function to get password or authentication vector(AV)
        get_credential_f = eval("self.get_%s_pass"%self.user_type) #by default, get password
        #bind function of authentication method
        if self.pack.has_key(ATTR_USER_PASSWORD):
            self.auth_method = 'pap'
        elif self.pack.has_key(ATTR_CHAP_PASSWORD):
            self.auth_method = 'chap'
        elif self.pack.has_key(ATTR_EAP_MESSAGE):
            self.auth_method = 'eap_sim'
            #if EAP-SIM, shall get AV, not password
            get_credential_f = eval("self.get_%s_auth_vector"%self.user_type)
        else:
            return (False, "No password or EAP message to perform authentication")
        #auth_method_f = self.auth_methods[self.auth_method]
        auth_method_f = eval("self.%s_auth"%self.auth_method)

        #try to get credential
        try:
            x = get_credential_f()
            if x == None:
                return (False, "Failed to get credential")
        except AttributeError, e: 
            self.log.write_log(WARNING, SUCCESS, "Underfined function to get credential: %s"%e)
            self.log.write_log(INFO, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
            return (False, "Failed to get credential")
        #run authentication method with the credential
        try:
            return auth_method_f(x)
        except AttributeError, e:
            self.log.write_log(WARNING, SUCCESS, "Underfined function to authentication: %s"%e)
            self.log.write_log(INFO, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
            return (False, "Unsupported user type")

    def get_VISITOR_pass(self):
        try:
            return self.user_info["CODE"]
        except KeyError:
            return None
        
    def pap_auth(self, password):
        try:
            pwd = self.pack.PwDecrypt(self.pack[ATTR_USER_PASSWORD][0])
            #print "----------- PASSWORD -------------"
            #print pwd
            #print self.pack[ATTR_USER_PASSWORD][0].encode('hex')
            #print self.pack.PwCrypt(pwd).encode('hex')
        
            if pwd == password:
                return (True, "OK")
            else:
                return (False, "Password not match")
        except Exception, e:
            self.log.write_log(INFO, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
            return (False, "Failed to verify password")
        

    def chap_auth(self, password):
        try:
            try:
                challenge = self.pack[ATTR_CHAP_CHALLENGE][0]
            except:
                challenge = self.pack.authenticator

            chap_id = self.pack[ATTR_CHAP_PASSWORD][0][0:1]
            resp_digest = self.pack[ATTR_CHAP_PASSWORD][0][1:]

            if resp_digest == get_chap_rsp(chap_id, password, challenge):
                return (True, "OK")
            else:
                return (False, "Password not match")
        except Exception, e:
            self.log.write_log(INFO, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
            return (False, "Failed to verify password")

    def eap_sim_auth(self, av):
        return (False, "EAP-SIM not supported")

    def disconnect_existing_session(self):
        try:
            #get all online session MAC for this user
            #send disconnect request for all sessions that MAC != current MAC
            for session_mac in self.acct_session_hash.find_sessions_by_username(self.username):
                #if session_mac == self.mac:
                #    continue
                self.disconnect_queue.disconnect(self.username, session_mac)
        except:
            pass
