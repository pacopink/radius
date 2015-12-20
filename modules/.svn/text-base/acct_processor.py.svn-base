#!/bin/env python
#coding:utf8
import binascii
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
from global_conf import *
from timed_hash import TimedHash
import traceback
import radius_cdr_writer
from account_mgr import *
from omc_kpi import Kpi, KpiTicker

import argparse
import os
import sys
import struct
import signal

### which type of endpoint need to conern ###
concern_type_list = ('MIRROR',)

### I am a Authentication Processor ###
my_dipc_type = 'ACCP'

terminate = False
reload_sk = False
args = None
log = None
rp = None 
dict_obj = None
ep_mgr = None
cdr_writer = None
acct_mgr = None
kpi_ticker = None


def init_sig():
    def signal_handler(sig, frame):
        if sig == signal.SIGINT or sig == signal.SIGTERM:
            global terminate 
            terminate = True
        if sig == signal.SIGUSR1:
            if log:
                log.write_log(INFO, 0, "Signal SIGUSR1 received, reload redis buffers")
            if acct_mgr:
                acct_mgr.reload_redis_buffers()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)


class AcctDipcMgr(EndPointMgr):
    def __processing__(self, msg):
        #print("Get msg from [%s] type[%d] len[%d] orig_dst[%s] route_to_backup[%s] queue_time[%d.%d] msg[%s]"%(msg["Sender"], msg["MsgType"], msg["Length"], msg["OrigDest"], msg["RouteToBackup"], msg["QueueTimeSec"], msg["QueueTimeUsec"], msg["Buff"].encode('hex')))
        try:
            msg2 = DipcMsg(msg) #decode msg
            #print msg["Buff"].encode('hex')
        except Exception, e:
            #log the error and discard msg
            log.write_log(ERROR, 0, e.__str__)
            return
        
        if msg2.msg_type == MT_ACCT_2_ACCP:
            key = msg2.header
            try:
                #print "[%s]"%msg2.body.encode('hex')
                pkt = packet.AcctPacket(dict=dict_obj, packet=msg2.body)
                if pkt.has_key('State'):
                    #if include State attribute, use it as a key of task
                    #in this case, the msg header must be passed in as a subkey
                    #so that the task can send response with the subkey as header
                    state = pkt['State'][0]
                    acct_mgr.resume_task(state, msg2.msg_type, msg2.body, sender=msg2.sender, subkey=msg2.header)
                else:
                    acct_mgr.new_task(key, msg2.host, msg2.sender, pkt, kpi_ticker)
            except Exception,e:
                #print "Process radius request exception %s:%s"%(type(e), e)
                kpi_ticker.increase_kpi('ACCOUNT_INVALID')
                print ("%s: %s"%(e, traceback.format_exc()))
                return 
        elif msg2.msg_type == MT_EPP_2_ACCP:
            #when adapter returned with a result of EPP
            key = msg2.header.encode('hex')
            acct_mgr.resume_task(key, msg2.msg_type, msg2.body) 
                
def init_args():
    ''' initialize argument list '''
    VERSION='V01.01.001'
    PROG_NAME='auth_processor'
    parser = argparse.ArgumentParser(description='%s %s' % (VERSION, PROG_NAME))
    parser.add_argument('-ln',  metavar='<logic name>', type=str, help='logicname for instance', required=True)
    parser.add_argument('-d',  action='store_true', help='turn on debug flag', default=False, dest="debug_flag")
    parser.add_argument('-p',  action='store_true', help='turn on cout flag', default=False, dest="cout_flag")
    parser.add_argument('-procmon', action='store_true', help='dummy argument for proc_monitor', default=False)
    parser.add_argument('-dictpath',  metavar='<dict path>', type=str, help='dictionary path', default="./")
    parser.add_argument('-dictfile', action='append', metavar='<dictionary file>', type =str, nargs=1, help='radius dictionary file', required=True)
    parser.add_argument('-cdr',  metavar='<cdr path>', type=str, help='cdr path to write cdr', required=True)
    parser.add_argument('-logpath',  metavar='<log path>', type=str, help='log path to write log', default="./")
    parser.add_argument('-version', '-v', action='version', version='%(prog)s '+VERSION)
    x = parser.parse_args()

    dict_files = list()
    for i in x.dictfile:
        dict_files.append(os.path.join(x.dictpath, i[0]))
    try:
        global dict_obj
        dict_obj = dictionary.Dictionary(*dict_files) 
    except Exception,e:
        print "Error when parsing dictionary files: %s"%dict_files.__str__()
        print ("%s: %s"%(e, traceback.format_exc()))
        sys.exit(1)
    return x

def init_logger(args):
    log = logger()
    log_path = os.path.join(args.logpath, "acct_processor_%s.log"%args.ln)
    ret = log.init(log_path, "acct_processor", args.ln)
    if ret != SUCCESS:
        print "Failed to initial logger"
        sys.exit(-1)
    log.set_debug(args.debug_flag)
    log.set_cout(args.cout_flag)
    log.write_log(INFO, SUCCESS, "-------- startup, log init --------")
    log.write_log(INFO, SUCCESS, "logicname[%s]"%args.ln)
    return log

def msg_loop():
    last_time = time.time()
    last_reload = last_time
    chocker = chocker_gr.Chocker()
    while not terminate and not ep_mgr.dead and not cdr_writer.dead:
        ep_mgr.idle = True
        acct_mgr.idle = True
        #do business
        cdr_writer.switch()
        ep_mgr.switch()
        acct_mgr.switch()
        #output KPI statistics
        if kpi_ticker.is_tick2record():
            kpi_ticker.output_mq()
        #check if idle sleep
        chocker.idle_switch(ep_mgr.idle and acct_mgr.idle)

        now = time.time()
        if now - last_time >= 10:
            log.write_log(INFO, SUCCESS, "Accounting Task: %d"%len(acct_mgr.task_dict.keys()))
            log.write_log(INFO, SUCCESS, "DIPC QUEUE DEPTH: %d"%ep_mgr.dipc.queue_depth())
            last_time = now
        if now - last_reload >= 60:
            acct_mgr.reload_redis_buffers()
            last_reload = now
    
def main():
    global args, log, rp, ep_mgr, cdr_writer, acct_mgr, kpi_ticker
    try:
        args = init_args()
        init_sig()
        log = init_logger(args)
        rp = redis.BlockingConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
        print concern_type_list
        ep_mgr = AcctDipcMgr(my_dipc_type, args.ln, concern_type_list, rp, log) 

        if not ep_mgr.start():
            log.write_log(ERROR, SUCCESS, "Failed to start EndPointMgr")
            sys.exit(1)

        cdr_writer = radius_cdr_writer.AcctCdrWriter(path=args.cdr, filename_pattern="ACCT_%s_$TIMESTAMP.txt"%args.ln)
        acct_mgr = AccountTaskMgr(redis_pool=rp, ep_mgr=ep_mgr, cdr_writer=cdr_writer, log=log)

        #initial KPI ticker
        kpi_ticker = KpiTicker(interval=KPI_REPORT_INTERVAL, ticker_name=args.ln, prog_name=PROG_NAME)
        for (k, v) in KPI_OID.items():
            kpi_ticker.add_kpi(Kpi(k, v))

        msg_loop() #execute msg loop

        cdr_writer.stop() #commit cdr
        log.write_log(INFO, SUCCESS, "Stopping EndpointMgr")
        ep_mgr.stop()
        log.write_log(INFO, SUCCESS, "~~~~ Exit ~~~~")
    except Exception, e:
        log.write_log(ERROR, SUCCESS, "main exception %s:%s"%(type(e), e))
        log.write_log(ERROR, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
        print("main exception %s:%s"%(type(e), e))
        print ("%s: %s"%(e, traceback.format_exc()))
    finally:
        if ep_mgr:
            ep_mgr.stop()
        
if __name__=="__main__":
    main()
