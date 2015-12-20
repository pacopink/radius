#!/bin/env python
#coding:utf8

import binascii
from DipcPy import *
from DipcPy.dipc import *
import redis
import socket
import time
import traceback
from greenlet import greenlet
import os


class EndPointMgr(greenlet):
    '''A DIPC endpoint manager class'''
    def __init__(self, mytype, ln, concern_list, redis_pool, log):
        '''
        ln: local logic name
        concern_list: concerned EP type list, mgr will find those EPs from Redis
        r_pool: redis connection pool
        log: logger
        '''
        self.mytype = mytype
        self.hostname = socket.gethostname()
        self.ln = ln
        self.self_fullname = self.hostname+"."+self.ln
        self.concern_list = concern_list
        self.redis_connection_pool = redis_pool
        self.pools = dict()
        self.db_warning = False
        for i in self.concern_list:
            self.pools[i] = EndPointPool() 
        self.log = log
        self.terminate = False
        ocg_home = os.getenv('OCG_HOME')
        if ocg_home:
            self.work_path = ocg_home+"/work"
        else:
            raise Exception("Cannot find evnironment variable 'OCG_HOME'")
        self.dipc = None

        self.idle = True

    def start(self):
        '''Initialize a dipc_interface instance'''
        self.dipc = dipc_interface()
        ret = self.dipc.init(self.ln, self.work_path)
        if ret != SUCCESS:
            self.log.write_log(ERROR, ERR_IPC_INIT_SOCKET, "failed to init dipc_interface, exit")
            return False
        else:
            return True

    def run(self):
        '''run self.svc and self.svc_topo in 2 greenlet'''
        gr_process = greenlet(self.svc)
        gr_topo = greenlet(self.svc_topo)

        while not gr_topo.dead and not gr_process.dead:
            gr_topo.switch()
            gr_process.switch()
            self.parent.switch()
        
    def stop(self):
        '''Deregister self logic name from redis and terminate manager'''
        self.terminate = True
        self.dipc.close()
        try:
            r = redis.Redis(connection_pool=self.redis_connection_pool)
            key = "DIPC_"+self.mytype
            r.srem(key, self.self_fullname)
        except Exception,e:
            self.log.write_log(DEBUG, 0, "failed to deregister EP from Redis [%s]"%e)
            pass

    def __processing__(self, msg):
        '''the method to process received message, for user to override'''
        pass

    def svc(self):
        '''try to receive msg which are send to myself, call self.__processing__ to process'''
        while not self.terminate:
            try:
                msg = self.recv_msg()
                if msg != None:
                    self.__processing__(msg)
                    self.idle = False
                else:
                    self.parent.switch()
            except Exception,e:
                self.log.write_log(ERROR, 0, "EndpointMgr.svc %s: %s"%(type(e), e))
                self.log.write_log(ERROR, 0, "%s: %s"%(e, traceback.format_exc()))

    def svc_topo(self):
        '''periodically update dipc topology update, register self ln to redis, read concerned ep list from redis and do add concern'''
        last_active = time.time()
        interval = 2
        abnormal_interval = 10
        while not self.terminate:
            #if interval not reached, do nothing
            if time.time()-last_active<interval:
                self.parent.switch()
                continue
            #if interval reached, update last_active time, and do business
            last_active = time.time()
            try:
                r = redis.Redis(connection_pool=self.redis_connection_pool)
                #register self EP to Redis 
                key = "DIPC_"+self.mytype
                r.sadd(key, self.self_fullname)
                #update concern list by type
                for ct in self.concern_list:
                    key = "DIPC_"+ct
                    eps = r.smembers(key)
                    epl = list(eps)
                    for ep in epl:
                        #shall skip myself
                        if self.self_fullname == ep:
                            continue
                        self.dipc.add_concerned_endpoint(ep)
                        self.dipc.add_concerned_endpoint(ep)
                        #ep_b = self.dipc_interface.get_backup_endpoint(ep)
                        #if ep_b:
                        #    self.dipc.add_concerned_endpoint(ep_b)
                        #self.pools[ct].register(ep_b)
                        self.pools[ct].register(ep) 
                    for ep in self.pools[ct].whole_list:
                        if not ep in eps:
                            self.pools[ct].deregister(ep) 
                            self.dipc.remove_concerned_endpoint(ep)
                            continue
                        if self.dipc.get_concerned_endpoint_status(ep) == CONNECTED:
                            self.pools[ct].add_to_alive_ep_list(ep)
                        else:
                            self.pools[ct].remove_from_alive_ep_list(ep)
                    self.log.write_log(DEBUG, 0, "[%s] %s %s"%(ct, self.pools[ct].__str__(), self.pools[ct].whole_list.__str__()))
                if self.db_warning:
                    self.db_warning = False
                    self.log.write_log(CLEAN, ERR_DB_CONN, "Redis connection regain")
            except Exception, e:
                self.log.write_log(ERROR, 0, "EndpointMgr.svc Exception:[%s]"%e)
                self.db_warning = True
                self.log.write_log(ERROR, ERR_DB_CONN, "Redis connection lost ... sleep for 10s then retry")
                print ("%s: %s"%(e, traceback.format_exc()))
                while True:
                    if time.time()-last_active<abnormal_interval:
                        self.parent.switch()
                    else:
                        break
            except:
                print ("%s: %s"%(e, traceback.format_exc()))

    def get_available_ep(self, ep_type, key=None):
        '''get available_ep from pool of endpoint type
           if key == None, us round robin, else use hash'''
        if not self.pools.has_key(ep_type):
            return None

        ep = None
        p = self.pools[ep_type]
        while ep == None and not p.is_alived_ep_list_empty():
            if key:
                ep = p.hash_get(key)
            else:
                ep = p.rr_get()
            #get a EP then check its status, if not CONNECTED, get another
            if ep and self.dipc.get_concerned_endpoint_status(ep) != CONNECTED:
                p.remove_concerned_endpoint(ep)
                ep = None
        return ep

    def get_available_ep_fix(self, ep_type, head=True):
        '''get available ep in fixed position
        parameter:
            ep_type: the ep_type to get ep
            head: if True, get the head ep, else, get the tail ep'''
        if not self.pools.has_key(ep_type):
            return None
        ep = None
        p = self.pools[ep_type]
        while ep == None and not p.is_alived_ep_list_empty():
            if head:
                ep = p.head_get()
            else:
                ep = p.tail_get()
            if ep and self.dipc.get_concerned_endpoint_status(ep) != CONNECTED:
                p.remove_concerned_endpoint(ep)
                ep = None
        return ep

    def recv_msg(self):
        '''Decrepit: try to get a msg, as all received msg shall be processed via self.__processing__, no need to call this'''
        return self.dipc.recv_msg()

    def send_msg(self, msg_code, receiver_ln, msg_body):
        '''send a message to a destination logic name
        parameter:
            msg_code: the INT msg code
            receiver_ln: the logic name of receiver
            msg_body: the body of msg, should be a string'''
        return self.dipc.send_msg(msg_code, receiver_ln, msg_body)
        

class EndPointPool(list):
    '''endpoint pool class, for EndPointMgr to hold a set of endpoints of a certain endpoint type'''
    def __init__(self):
        '''initial an empty pool'''
        self.current_index = 0
        self.whole_list = list()

    def register(self, ep):
        '''add an endpoint to the pool
        parameter:
            ep: endpoint logic name to add to the pool'''
        if (ep in self.whole_list):
            return
        self.whole_list.append(ep)
        self.whole_list.sort()
        return

    def deregister(self, ep):
        '''remove an enpoint from the pool
        parameter:
            ep: endpoint logic name to remove from the pool'''
        try:
            self.remove(ep)
        except ValueError:
            pass

        try:
            self.whole_list.remove(ep)
        except ValueError:
            pass

    def is_alived_ep_list_empty(self):
        '''check if there is no alived ep'''
        return len(self)==0

    def remove_from_alive_ep_list(self, ep):
        '''remove an endpoint from alived_ep_list'''
        try:
            self.remove(ep)
        except ValueError:
            pass

    def add_to_alive_ep_list(self, ep):
        '''add an endpoint from alived_ep_list'''
        if (ep in self):
            return
        self.append(ep)
        self.sort()
        

    def head_get(self):
        '''get the first alived endpoint'''
        l = len(self)
        if (l==0):
            return None
        else:
            return self[0] 

    def tail_get(self):
        '''get the last alived endpoint'''
        l = len(self)
        if (l==0):
            return None
        else:
            return self[l-1] 

    def rr_get(self):
        '''get alived endpoint in round robin way'''
        l = len(self)
        if (l==0):
            return None
        else:
            if self.current_index>=l:
                self.current_index = 0
            i = self.current_index
            self.current_index += 1
            return self[i]

    def hash_get(self, key):
        '''using key to make a hash to choice a alived endpoint to return
        parameter:
            key: the string to make hash'''
        l = len(self)
        if l==0:
            return None
        if l==1:
            return self[0]
        i = binascii.crc32(key)%l
        return self[i]


if __name__=="__main__":
    import argparse
    import os
    import sys

    def init_args():
        ''' initialize argument list '''
        VERSION='V01.01.001'
        PROG_NAME='endpoint_test'
        parser = argparse.ArgumentParser(description='%s %s' % (VERSION, PROG_NAME))
        parser.add_argument('-conf',  metavar='<config file>', type=str, help='config file for program', required=True)
        parser.add_argument('-ln',  metavar='<logic name>', type=str, help='logicname for instance', required=True)
        parser.add_argument('-type', metavar='<my endpoint type>', type=str, help='endpoint type', default=False)
        parser.add_argument('-d',  action='store_true', help='turn on debug flag', default=False, dest="debug_flag")
        parser.add_argument('-p',  action='store_true', help='turn on cout flag', default=False, dest="cout_flag")
        parser.add_argument('-procmon', action='store_true', help='dummy argument for proc_monitor', default=False)
        parser.add_argument('-version', '-v', action='version', version='%(prog)s '+VERSION)
        parser.add_argument('-concern', action='append', metavar='<concern dipc end point type>', type =str, nargs=1, help='concerned type', required=True)
        return parser.parse_args()


    args = init_args()
    print args
    concern_list = list()
    for c in args.concern:
        concern_list.append(c[0])
    #Namespace(concern=[['AUTP'], ['CDR']], conf='aaa.conf', cout_flag=True, debug_flag=True, ln='EP001', procmon=False, type='AUTT')
    log = logger()
    log_path = os.path.normpath(os.path.dirname(__file__))
    log_path = os.path.join(log_path, "%s.log"%args.ln)
    ret = log.init(log_path, args.ln, "")
    log.set_debug(args.debug_flag)
    log.set_cout(args.cout_flag)
    log.write_log(INFO, SUCCESS, "-------- startup, log init --------")
    log.write_log(INFO, SUCCESS, "logicname[%s]"%args.ln)

    redis_host = 'localhost'
    redis_port = 6379
    redis_db = 0 
    redis_auth = None
    rp = redis.BlockingConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
    
    #def __init__(self, mytype, ln, concern_list, redis_pool, log, work_path="/ocg/work"):
    ep_mgr = EndPointMgr(args.type, args.ln, concern_list, rp, log) 
    if not ep_mgr.start():
        log.write_log(ERROR, SUCCESS, "Failed to start EndPointMgr")
        sys.exit(1)
    
    try:
        while True:
            time.sleep(0.5)
    except:
        pass 
    ep_mgr.stop()
            
