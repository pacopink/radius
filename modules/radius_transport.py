#!/bin/env python
#coding:utf8
import binascii
from DipcPy import *
from DipcPy.dipc import *
from dipc_msg import *
import redis
import socket
import time
from greenlet import greenlet
import pyrad
from pyrad import *
from endpoint_mgr_gr import *
from udp_transceiver_gr import *
from global_conf import *
from global_def import *
from timed_hash import TimedHash
import traceback
import chocker_gr
from omc_kpi import Kpi, KpiTicker

import argparse
import os
import sys
import struct
import signal


### which type of endpoint need to conern ###
concern_dict = {
    'ACCT': ('ACCP', ),
    'AUTT': ('AUTP', ),
}

### which code is accepted ###
accept_code = {
    'ACCT': (4,),
    'AUTT': (1,),
}

concern_type_list = None
accept_code_list = None
terminate = False
context = None
args = None
log = None
udp_server = None 
rp = None 
ep_mgr = None
kpi_ticker = None

msg_type = None
ep_type = None
dest_type = None

def init_sig():
    def signal_handler(sig, frame):
        if sig == signal.SIGINT or sig == signal.SIGTERM:
            global terminate 
            terminate = True
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)

class RadiusServer(UdpTransceiver):
    def __processing__(self, packet):
        '''To process UDP packet received as a Radius Request'''
        data = packet[0]
        host = packet[1][0]
        port = packet[1][1]
        msg = DipcMsg()
        key = msg.pack_header(host, port, data[0:20])
        msg.encode(data) #pack a message to be sent
        log.db("UDP recv from host[%s:%d]"%(host, port))

        #if a cached reply found, it should be a re-try, then resend the cached reply
        if context.expire(key, 10)==True and context[key].has_key('reply'):
            context.expire(key, 10) #set the ttl to 10 sec if there is other retry
            self.send((context[key]['reply'], (host, port)))
            log.db("Resend Reply")
            kpi_ticker.increase_kpi('RADIUS_REQUEST_RESEND_RCV')
            return
        #otherwise treat it as a new request
        try:
            #decode radius msg
            rpack = pyrad.packet.Packet(packet=data)
            #code validation
            if rpack.code not in accept_code_list:
                kpi_ticker.increase_kpi('INVALID_REQ_RCV')
                log.write_log(INFO, 0, "Recv radius msg with unacceptable code [%s]"%data.encode('hex'))
                #print("Recv radius msg with unacceptable code [%s]"%data.encode('hex'))
                return
            #check Username existence
            if not rpack.has_key(1):
                kpi_ticker.increase_kpi('INVALID_REQ_RCV')
                log.write_log(INFO, 0, "Recv radius msg without UserName [%s]"%data.encode('hex'))
                #print("Recv radius msg without UserName [%s]"%data.encode('hex'))
                return
            user_name = rpack[1][0]
            #get available processor
            dln = ep_mgr.get_available_ep(ep_type=dest_type, key=user_name)
            if dln == None:
                if ep_type == "AUTT":
                    kpi_ticker.increase_kpi('FAILED_TO_PROCESS_ACCESS')
                else:
                    kpi_ticker.increase_kpi('FAILED_TO_PROCESS_ACCOUNT')
                log.write_log(ERROR, 0, "No available [%s] Endpoint to send, discard[%s]"%(dest_type, data.encode('hex')))
                #print("No available [%s] Endpoint to send, discard[%s]"%(dest_type, data.encode('hex')))
                return
            #check if the msg has been sent to the processor
            if context.has_key(key) and context[key].has_key('processor'):
                if dln == context[key]['processor']:
                    kpi_ticker.increase_kpi('RADIUS_REQUEST_RESEND_RCV')
                    #go to the same processor, no need to send again
                    #print ("Already processing no need to send again")
                    return
            #send the msg
            ep_mgr.send_msg(msg_type, dln, msg.raw_byte) #the first 0-31:padded host, 32-35:port, 36-55:first-20byet, 56-:msg
            #save to context, set expiry
            if context.expire(key, 20) == True:
                #already exists
                context[key]['processor'] = dln
            else: 
                #newly ceate
                context.set(key, dict(), expire=20) #cache for 20 sec
                context[key]['processor'] = dln
                context[key]['addr'] = (host, port)

            if ep_type == "AUTT":
                kpi_ticker.increase_kpi('ACCESS_REQ_RCV')
            else:
                kpi_ticker.increase_kpi('ACCOUNT_REQ_RCV')
                    
        except Exception, e:
            #log.write_log(ERROR, 0, "Faild to decode [%s], %s:%s"%(data.encode('hex'), type(e), e.__str__()))
            kpi_ticker.increase_kpi('INVALID_REQ_RCV')
            print("Faild to decode [%s], %s:%s"%(data.encode('hex'), type(e), e.__str__()))
            print ("%s: %s"%(e, traceback.format_exc()))
            return
        
class RadiusDipcMgr(EndPointMgr):
    def __processing__(self, msg):
        '''To process Dipc messages received'''
        log.db("Get msg from [%s] type[%d] len[%d] orig_dst[%s] route_to_backup[%s] queue_time[%d.%d] msg[%s]"%(msg["Sender"], msg["MsgType"], msg["Length"], msg["OrigDest"], msg["RouteToBackup"], msg["QueueTimeSec"], msg["QueueTimeUsec"], msg["Buff"].encode('hex')))

        if msg['MsgType'] != msg_type+1:
            log.write_log(ERROR, 0, "Receive a DIPC msg with invalid type[%s]"%msg['MsgType'].encode('hex'))
            #print("Receive a DIPC msg with invalid type[%d]"%msg['MsgType'])
            return

        key = msg['Buff'][0:56]
        reply = msg['Buff'][56:]
        
        if len(reply)<=0:
            log.write_log(ERROR, 0, "Receive a DIPC msg with invalid buffer[%s]"%msg['Buff'].encode('hex'))
            #print("Receive a DIPC msg with invalid buffer[%s]"%msg['Buff'].encode('hex'))
            return

        try:
            if context.expire(key, 20):
                #if the session can be found, update it and send to the address it cached
                session = context[key]
                session['reply'] = reply
                #print "Before UDP Send"
                #print session['addr']
                #print reply.encode('hex')
                #global udp_server
                udp_server.send((reply, session['addr']))
                log.db("Reply")
                #udp_server.send_udp(reply, session['addr'])
            else:
                log.write_log(ERROR, 0, "Receive a DIPC msg but the context has been expired [%s]"%(msg['Buff'].encode('hex')))
                #print("Receive a DIPC msg but the context has been expired [%s]"%(msg['Buff'].encode('hex')))
        except Exception,e:
            log.write_log(ERROR, 0, "Exception in RadiusDipcMgr processing %s:%s"%(type(e), e))
            #print ("Exception in RadiusDipcMgr processing %s:%s"%(type(e), e))
                
def init_args():
    ''' initialize argument list '''
    VERSION='V01.01.001'
    PROG_NAME='radius_transport.py'
    parser = argparse.ArgumentParser(description='%s %s' % (VERSION, PROG_NAME))
    parser.add_argument('-addr', metavar='<addr to bind>', type=str, default="0.0.0.0", help='radius service bind to this addr')
    parser.add_argument('-port', metavar='<port to bind>', type=int, help='radius service bind to this port', required=True)
    parser.add_argument('-conf',  metavar='<config file>', type=str, help='config file for program', required=True)
    parser.add_argument('-ln',  metavar='<logic name>', type=str, help='logicname for instance', required=True)
    parser.add_argument('-t', metavar='<ACCT|AUTT>', type=str, help='endpoint type', required=True)
    parser.add_argument('-d',  action='store_true', help='turn on debug flag', default=False, dest="debug_flag")
    parser.add_argument('-p',  action='store_true', help='turn on cout flag', default=False, dest="cout_flag")
    parser.add_argument('-logpath',  metavar='<log path>', type=str, help='log path to write log', default="./")
    parser.add_argument('-procmon', action='store_true', help='dummy argument for proc_monitor', default=False)
    parser.add_argument('-version', '-v', action='version', version='%(prog)s '+VERSION)
    
    x = parser.parse_args()
    if x.t not in ('ACCT', 'AUTT'):
        parser.print_help()
        sys.exit(-1)
    global concern_type_list, accept_code_list
    global msg_type, ep_type, dest_type
    ep_type = x.t
    if ep_type == 'AUTT':
        msg_type = MT_AUTT_2_AUTP
        dest_type = 'AUTP'
    else:
        msg_type = MT_ACCT_2_ACCP
        dest_type = 'ACCP'
    concern_type_list = concern_dict[x.t]
    accept_code_list = accept_code[x.t]
    return x

def init_logger(args):
    '''initialize the logger'''
    log = logger()
    log_path = os.path.join(args.logpath, "transport_%s.log"%args.ln)
    ret = log.init(log_path, "transport", args.ln)
    if ret != SUCCESS:
        print "Failed to initial logger"
        sys.exit(-1)
    log.set_debug(args.debug_flag)
    log.set_cout(args.cout_flag)
    log.write_log(INFO, SUCCESS, "-------- startup, log init --------")
    log.write_log(INFO, SUCCESS, "logicname[%s]"%args.ln)
    return log
    

def init_udp_transceiver(args, log):
    '''initialize the RadiusServer(UdpTransceiver)'''
    #make sure the address want to bind is allocated in local host
    if args.addr != "0.0.0.0":
        last_warn = 0
        watcher = AddrWatcher(args.addr)
        while  not watcher.go_or_wait():
            if terminate:
                raise Exception("Get terminate signal while waiting for address to bind") 
            now = time.time()
            if now - last_warn >= 10:
                sys.stderr.write("The address [%s] is not existing in local host, wait and retry ...\n"%args.addr)
                log.write_log(INFO, SUCCESS, "The address [%s] is not existing in local host, wait and retry ...\n"%args.addr)
                last_warn = now
    
    try:
        trans = RadiusServer(host = args.addr, port = args.port, auto_process=True)
    except Exception,e:
        log.write_log(ERROR, 0, "Failed to init_udp_transceiver: %s"%e)
        sys.exit(-1)
    log.write_log(INFO, SUCCESS, "Start UDP port on [%s:%d]"%(args.addr, args.port))
    return trans

def msg_loop():
    '''The message loop of radius_transport'''
    last_time = time.time()
    chocker = chocker_gr.Chocker()
    while not terminate and not udp_server.dead and not ep_mgr.dead:
        #initialize the idle flag to true
        udp_server.idle = True
        ep_mgr.idle = True

        #do business
        udp_server.switch()
        ep_mgr.switch()

        #output KPI statistics
        if kpi_ticker.is_tick2record():
            kpi_ticker.output_mq()

        #smart chocker to see if need to take a rest
        chocker.idle_switch(udp_server.idle and ep_mgr.idle)

        #report myself status
        if time.time() - last_time > 10:
            log.write_log(INFO, SUCCESS, "DIPC QUEUE DEPTH: %d"%ep_mgr.dipc.queue_depth())
            log.write_log(INFO, SUCCESS, "UDP RECV QUEUE: %d"%udp_server.recvq.qsize())
            log.write_log(INFO, SUCCESS, "UDP SEND QUEUE: %d"%udp_server.sendq.qsize())
            last_time = time.time()

def main():
    '''The main thread of radius process'''
    global args, log, udp_server, rp, ep_mgr, context, kpi_ticker
    try:
        args = init_args()
        init_sig()
        log = init_logger(args)
        rp = redis.BlockingConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
        context = TimedHash()
        context.start()
        ep_mgr = RadiusDipcMgr(args.t, args.ln, concern_type_list, rp, log) 
        udp_server = init_udp_transceiver(args, log)

        if not udp_server.start():
            log.write_log(ERROR, SUCCESS, "Failed to start UdpTransceiver")
            context.stop()
            sys.exit(1)

        if not ep_mgr.start():
            log.write_log(ERROR, SUCCESS, "Failed to start EndPointMgr")
            udp_server.stop()
            context.stop()
            sys.exit(1)

        #initial KPI ticker
        kpi_ticker = KpiTicker(interval=KPI_REPORT_INTERVAL, ticker_name=args.ln, prog_name=PROG_NAME)
        for (k, v) in KPI_OID.items():
            kpi_ticker.add_kpi(Kpi(k, v))

        msg_loop() #execute msg loop         

        log.write_log(INFO, SUCCESS, "Stopping UDP server")
        udp_server.stop()
        log.write_log(INFO, SUCCESS, "Stopping EndpointMgr")
        ep_mgr.stop()
        log.write_log(INFO, SUCCESS, "Stopping TimedHash")
        context.stop()
        log.write_log(INFO, SUCCESS, "~~~~ Exit ~~~~")
    except Exception, e:
        log.write_log(ERROR, SUCCESS, "main exception %s:%s"%(type(e), e))
        log.write_log(ERROR, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
        print ("%s: %s"%(e, traceback.format_exc()))
    finally:
        if context!=None:
            context.stop()
        if udp_server!=None:
            udp_server.stop()
        if ep_mgr!=None:
            ep_mgr.stop()
        
if __name__=="__main__":
    main()
