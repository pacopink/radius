#!/bin/env python
#coding:utf8
from DipcPy import *
from DipcPy.dipc import *
from dipc_msg import *
import threading
import redis
import socket
import time
import pyrad
import chocker_gr
from pyrad import *
from endpoint_mgr_gr import *
from udp_transceiver_gr import *
from global_conf import *
from global_def import *
import traceback
import mirror_dest_conf

import argparse
import os
import sys
import struct
import signal

### which type of endpoint need to conern ###
concern_type_list = ()

### I am a Authentication Processor ###
my_dipc_type = 'MIRROR'

terminate = False
args = None
log = None
rp = None 
ep_mgr = None
udp_server = None 


def init_sig():
    def signal_handler(sig, frame):
        if sig == signal.SIGINT or sig == signal.SIGTERM:
            global terminate 
            terminate = True
        if sig == signal.SIGUSR1:
            #clear sk_hash upon signal SIGUSR1
            if log:
                log.write_log(INFO, 0, "Signal SIGUSR1 received, reload mirror_dest_conf")
            reload(mirror_dest_conf)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)

class MirrorUdpServer(UdpTransceiver):
    def __processing__(self, packet):
        print "Shouldn't receive any packet here, if recevied, just discard"

class MirrorDipcMgr(EndPointMgr):
    def __processing__(self, msg):
        try:
            msg2 = DipcMsg(msg) #decode msg
            #print msg["Buff"].encode('hex')
        except Exception, e:
            #log the error and discard msg
            log.write_log(ERROR, 0, e.__str__)
            return
        
        if msg2.msg_type == MT_AUTT_2_AUTP:
            #mirror Access request
            for addr in mirror_dest_conf.auth_dest_list:
                try:
                    udp_server.send((msg2.body, addr))
                except Exception,e:
                    print ("%s: %s"%(e, traceback.format_exc()))

        elif msg2.msg_type == MT_ACCT_2_ACCP:
            #mirror Accounting request
            for addr in mirror_dest_conf.acct_dest_list:
                try:
                    udp_server.send((msg2.body, addr))
                except Exception,e:
                    print ("%s: %s"%(e, traceback.format_exc()))
        else:
            log.write_log(WARNING, 0, "Receive invalid message type[%d] from [%s] [%s]"%(msg2.msg_type, msg2.sender, msg2.raw_bytes.encode('hex')))
                
def init_args():
    ''' initialize argument list '''
    VERSION='V01.01.001'
    PROG_NAME='radius_mirror'
    parser = argparse.ArgumentParser(description='%s %s' % (VERSION, PROG_NAME))
    parser.add_argument('-ln',  metavar='<logic name>', type=str, help='logicname for instance', required=True)
    parser.add_argument('-d',  action='store_true', help='turn on debug flag', default=False, dest="debug_flag")
    parser.add_argument('-p',  action='store_true', help='turn on cout flag', default=False, dest="cout_flag")
    parser.add_argument('-procmon', action='store_true', help='dummy argument for proc_monitor', default=False)
    parser.add_argument('-logpath',  metavar='<log path>', type=str, help='log path to write log', default="./")
    parser.add_argument('-version', '-v', action='version', version='%(prog)s '+VERSION)
    x = parser.parse_args()

    return x

def init_logger(args):
    log = logger()
    log_path = os.path.join(args.logpath, "mirror_%s.log"%args.ln)
    ret = log.init(log_path, "radius_mirror", args.ln)
    if ret != SUCCESS:
        print "Failed to initial logger"
        sys.exit(-1)
    log.set_debug(args.debug_flag)
    log.set_cout(args.cout_flag)
    log.write_log(INFO, SUCCESS, "-------- startup, log init --------")
    log.write_log(INFO, SUCCESS, "logicname[%s]"%args.ln)
    return log

def init_udp_transceiver(args, log):
    try:
        trans = MirrorUdpServer(auto_process=True)
    except Exception,e:
        log.write_log(ERROR, 0, "Failed to init_udp_transceiver: %s"%e)
        sys.exit(-1)
    return trans


def msg_loop():
    last_time = time.time()
    chocker = chocker_gr.Chocker(rest_time=0.05, rest_threshold=1000)
    while not terminate and not ep_mgr.dead and not udp_server.dead:
        ep_mgr.idle = True
        udp_server.idle = True
        #do business
        ep_mgr.switch()
        udp_server.switch()
        #check if idle sleep
        chocker.idle_switch(ep_mgr.idle and udp_server.idle)
        if time.time() - last_time > 10:
            log.write_log(INFO, SUCCESS, "DIPC QUEUE DEPTH: %d"%ep_mgr.dipc.queue_depth())
            log.write_log(INFO, SUCCESS, "UDP RECV QUEUE: %d"%udp_server.recvq.qsize())
            log.write_log(INFO, SUCCESS, "UDP SEND QUEUE: %d"%udp_server.sendq.qsize())
            last_time = time.time()
    
def main():
    global args, log, rp, ep_mgr, udp_server
    try:
        args = init_args()
        init_sig()
        log = init_logger(args)
        rp = redis.BlockingConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
        udp_server = init_udp_transceiver(args, log)
        ep_mgr = MirrorDipcMgr(my_dipc_type, args.ln, concern_type_list, rp, log) 

        if not udp_server.start():
            log.write_log(ERROR, SUCCESS, "Failed to start UdpTransceiver")
            sys.exit(1)
        log.write_log(INFO, SUCCESS, "Start UDP port on [%s:%d]"%(udp_server.host, udp_server.port))
        if not ep_mgr.start():
            log.write_log(ERROR, SUCCESS, "Failed to start EndPointMgr")
            sys.exit(1)

        msg_loop() #execute msg loop

        log.write_log(INFO, SUCCESS, "Stopping EndpointMgr")
        ep_mgr.stop()
        log.write_log(INFO, SUCCESS, "Stopping UDP server")
        udp_server.stop()
        log.write_log(INFO, SUCCESS, "~~~~ Exit ~~~~")
    except Exception, e:
        log.write_log(ERROR, SUCCESS, "main exception %s:%s"%(type(e), e))
        log.write_log(ERROR, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
        print("main exception %s:%s"%(type(e), e))
        print("%s: %s"%(e, traceback.format_exc()))
    finally:
        if ep_mgr:
            ep_mgr.stop()
        if udp_server:
            udp_server.stop()
        
if __name__=="__main__":
    main()
