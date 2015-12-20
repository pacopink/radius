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
from disconn_mgr import DisconnTaskMgr
from radius_cdr_writer import DisconnCdrWriter 
from redis_buffer import *
from omc_kpi import Kpi, KpiTicker

import argparse
import os
import sys
import struct
import signal

terminate = False
args = None
log = None
rp = None 
udp_server = None 
dict_obj = None
disconn_mgr = None
disconn_poller = None
cdr_writer = None
kpi_ticker = None

def init_sig():
    def signal_handler(sig, frame):
        if sig == signal.SIGINT or sig == signal.SIGTERM:
            global terminate 
            terminate = True
        if sig == signal.SIGUSR1:
            pass
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)

class DisconnUdpServer(UdpTransceiver):
    def __processing__(self, packet):
        try:
            data = packet[0]
            (addr, port) = packet[1]
            pkt = pyrad.packet.Packet(dict=dict_obj, packet=data)
            log.db("Recv msg from [%s:%d] [%s]"%(addr, port, data.encode('hex')))
        except:
            log.db("BackTrace %s: %s"%(e, traceback.format_exc()))
            return

        #only allow code for Disconnect-Ack or Disconnect-Nak
        if pkt.code not in (41, 42):
            log.write_log(WARNING, 0, "Receive pack not Disconnect-ACK/NAK, discard [%s]"%data.encode('hex'))
            return
        key = "%s:%d:%d"%(addr, port, pkt.id) #the key of this request
        log.db("Make key [%s]"%key)
        disconn_mgr.resume_task(key, pkt)
        if pkt.code == 41:
            log.db("DISCONN_ACK_RCV")
            kpi_ticker.increase_kpi("DISCONN_ACK_RCV")
        else:
            log.db("DISCONN_NACK_RCV")
            kpi_ticker.increase_kpi("DISCONN_NACK_RCV")

class DisconnPoller(greenlet):
    '''Poll disconnect request from Redis List, lookup for the session details and create disconnect request packet to run disconnect task'''
    def stop(self):
        self.stop_flag = True
        self.last_warning = int(time.time())
    def run(self):
        self.stop_flag = False
        self.db_warning = False
        disconn_queue = DisconnectQueue(rp)
        acct_session_hash = AcctSession(rp)

        while not self.stop_flag:
            self.idle = True
            #check if I am active node instance
            if args.addr != "0.0.0.0":
                last_warn = 0
                watcher = AddrWatcher(args.addr)
                while  not watcher.go_or_wait():
                    if terminate:
                        break
                    now = time.time()
                    if now - last_warn >= 10:
                        log.write_log(INFO, SUCCESS, "The address [%s] is not existing in local host, dont poll, wait and retry ...\n"%args.addr)
                        last_warn = now

            #start poll
            try:
                for req in disconn_queue.get_request(): 
                    if req == None:
                        break
                    self.idle = False #if any request, not idle loop
                    try:
                        log.write_log(INFO, 0, "Get Disconnect REQ[%s]"%(req))
                        (mac, username) = req.split("$")
                    except:
                        log.write_log(WARNING, 0, "Failed to decode request")
                        continue
                    session = acct_session_hash.find_session_by_username_mac(username, mac)
                    if session:
                        log.write_log(INFO, 0, "Get session details %s"%session)
                        (timestamp, nas_ip, nas_port, secret, session_id, multi_session_id) = session.split('$')
                        dst = nas_ip+":"+nas_port
                        #construct a packet for COA-DISCONN
                        pkt = packet.AcctPacket(dict=dict_obj, secret=secret, code=40, authenticator='\0'*16)
                        pkt.AddAttribute('Acct-Session-Id', session_id)
                        if len(multi_session_id)>0:
                            pkt.AddAttribute('Acct-Multi-Session-Id', multi_session_id)
                        while disconn_mgr.set_pack_id(dst, pkt) == None:
                            #try to assign ID to packet, if failed, it is too busy, return CPU to other greenlet and wait for available
                            self.parent.switch()
                        disconn_mgr.new_task((nas_ip, int(nas_port)), pkt, username, mac, kpi_ticker)
                    else:
                        kpi_ticker.increase_kpi('DISCONN_FAILED_TO_FIND_SESSION')
                        log.write_log(WARNING, 0, "Failed to find session details for [%s]"%req)
                if self.db_warning:
                    self.db_warning = False
                    log.write_log(CLEAN, ERR_DB_CONN, "DisconnPoller.run warning clean")
            except Exception,e:
                last_active = time.time()
                #log.write_log(ERROR, ERR_DB_CONN, "DisconnPoller.run Exception:[%s], wait 10s to retry ..."%e)
                log.write_log(ERROR, ERR_DB_CONN, "DisconnPoller.run Exception:[%s:%s], wait 10s to retry ..."%(e, traceback.format_exc())) 
                self.db_warning = True
                while True:
                    if time.time()-last_active<10:
                        self.parent.switch()
                    else:
                        break
            self.parent.switch()
        log.write_log(INFO, 0, "DisconnPoller terminated")
                
def init_args():
    ''' initialize argument list '''
    VERSION='V01.01.001'
    PROG_NAME='radius_disconn'
    parser = argparse.ArgumentParser(description='%s %s' % (VERSION, PROG_NAME))
    parser.add_argument('-ln',  metavar='<logic name>', type=str, help='logicname for instance', required=True)
    parser.add_argument('-d',  action='store_true', help='turn on debug flag', default=False, dest="debug_flag")
    parser.add_argument('-p',  action='store_true', help='turn on cout flag', default=False, dest="cout_flag")
    parser.add_argument('-addr', metavar='<addr to bind>', type=str, default="0.0.0.0", help='radius service bind to this addr')
    parser.add_argument('-procmon', action='store_true', help='dummy argument for proc_monitor', default=False)
    parser.add_argument('-logpath',  metavar='<log path>', type=str, help='log path to write log', default="./")
    parser.add_argument('-cdr',  metavar='<cdr path>', type=str, help='cdr path to write cdr', required=True)
    parser.add_argument('-dictpath',  metavar='<dict path>', type=str, help='dictionary path', default="./")
    parser.add_argument('-dictfile', action='append', metavar='<dictionary file>', type =str, nargs=1, help='radius dictionary file', required=True)
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
    log_path = os.path.join(args.logpath, "disconn_%s.log"%args.ln)
    ret = log.init(log_path, "radius_disconn", args.ln)
    if ret != SUCCESS:
        print "Failed to initial logger"
        sys.exit(-1)
    log.set_debug(args.debug_flag)
    log.set_cout(args.cout_flag)
    log.write_log(INFO, SUCCESS, "-------- startup, log init --------")
    log.write_log(INFO, SUCCESS, "logicname[%s]"%args.ln)
    return log

def init_udp_transceiver(args, log):
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
        trans = DisconnUdpServer(host = args.addr, auto_process=True)
    except Exception,e:
        log.write_log(ERROR, 0, "Failed to init_udp_transceiver: %s"%e)
        sys.exit(-1)
    return trans


def msg_loop():
    last_time = time.time()
    chocker = chocker_gr.Chocker(rest_time=0.2, rest_threshold=1000)
    while not terminate and not udp_server.dead and not cdr_writer.dead and not disconn_poller.dead:
        disconn_mgr.idle = True
        udp_server.idle = True
        disconn_poller.idle = True
        #do business
        cdr_writer.switch()
        disconn_poller.switch()
        udp_server.switch()
        disconn_mgr.switch()
        #check if idle sleep
        chocker.idle_switch(disconn_mgr.idle and udp_server.idle and disconn_poller.idle)
        #output KPI statistics
        if kpi_ticker.is_tick2record():
            kpi_ticker.output_mq()

        if time.time() - last_time >= 10:
            if (disconn_mgr.idle and udp_server.idle and disconn_poller.idle):
                print "idle"
            log.write_log(INFO, SUCCESS, "UDP RECV QUEUE: %d"%udp_server.recvq.qsize())
            log.write_log(INFO, SUCCESS, "UDP SEND QUEUE: %d"%udp_server.sendq.qsize())
            last_time = time.time()
    
def main():
    global args, log, rp, udp_server, disconn_mgr, disconn_poller, cdr_writer, kpi_ticker
    try:
        args = init_args()
        init_sig()
        log = init_logger(args)
        udp_server = init_udp_transceiver(args, log)
        rp = redis.BlockingConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
        cdr_writer = DisconnCdrWriter(path=args.cdr, filename_pattern="DISCONN_%s_$TIMESTAMP.txt"%args.ln)  
        disconn_mgr = DisconnTaskMgr(redis_pool=rp, udp_server=udp_server, cdr_writer=cdr_writer, log=log)
        disconn_poller = DisconnPoller()

        if not udp_server.start():
            log.write_log(ERROR, SUCCESS, "Failed to start UdpTransceiver")
            sys.exit(1)
        log.write_log(INFO, SUCCESS, "Start UDP port on [%s:%d]"%(udp_server.host, udp_server.port))

        #initial KPI ticker
        kpi_ticker = KpiTicker(interval=KPI_REPORT_INTERVAL, ticker_name=args.ln, prog_name=PROG_NAME)
        for (k, v) in KPI_OID.items():
            kpi_ticker.add_kpi(Kpi(k, v))

        msg_loop() #execute msg loop

        disconn_poller.stop()
        log.write_log(INFO, SUCCESS, "Stopping UDP server")
        udp_server.stop()
        log.write_log(INFO, SUCCESS, "~~~~ Exit ~~~~")
    except Exception, e:
        log.write_log(ERROR, SUCCESS, "main exception %s:%s"%(type(e), e))
        log.write_log(ERROR, SUCCESS, "%s: %s"%(e, traceback.format_exc()))
        print ("%s: %s"%(e, traceback.format_exc()))
    finally:
        if disconn_poller:
            disconn_poller.stop()
        if udp_server:
            udp_server.stop()
        
if __name__=="__main__":
    main()
