#!/bin/env python
#coding:utf8
''' kpi_collector will termly poll kpi record messages from MQ, aggregate and write to a KPI file per interval minutes
'''
from DipcPy import *
import argparse
import os
import sys
import struct
import signal
import traceback
from omc_kpi import *
from global_def import *
import time


terminate = False
args = None
log = None
rp = None 
udp_server = None 
dict_obj = None
disconn_mgr = None
disconn_poller = None
cdr_writer = None


def init_sig():
    '''initialize handling for singnals'''
    def signal_handler(sig, frame):
        if sig == signal.SIGINT or sig == signal.SIGTERM:
            global terminate 
            terminate = True
        if sig == signal.SIGUSR1:
            pass
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)

                
def init_args():
    ''' initialize argument list '''
    VERSION='V01.01.001'
    PROG_NAME='kpi_collector'
    parser = argparse.ArgumentParser(description='%s %s' % (VERSION, PROG_NAME))
    parser.add_argument('-ln',  metavar='<logic name>', type=str, help='logicname for instance', required=True)
    parser.add_argument('-d',  action='store_true', help='turn on debug flag', default=False, dest="debug_flag")
    parser.add_argument('-p',  action='store_true', help='turn on cout flag', default=False, dest="cout_flag")
    parser.add_argument('-i',  metavar='<interval minute>', type=int, help='interval', default=15)
    parser.add_argument('-procmon', action='store_true', help='dummy argument for proc_monitor', default=False)
    parser.add_argument('-logpath',  metavar='<log path>', type=str, help='log path to write log', default="./")
    parser.add_argument('-outpath',  metavar='<kpi path>', type=str, help='path to write kpi_file', default="./")
    parser.add_argument('-version', '-v', action='version', version='%(prog)s '+VERSION)
    x = parser.parse_args()
    return x

def init_logger(args):
    ''' initialize logger '''
    log = logger()
    log_path = os.path.join(args.logpath, "kpi_colletor_%s.log"%args.ln)
    ret = log.init(log_path, "kpi_collector", args.ln)
    if ret != SUCCESS:
        print "Failed to initial logger"
        sys.exit(-1)
    log.set_debug(args.debug_flag)
    log.set_cout(args.cout_flag)
    log.write_log(INFO, SUCCESS, "-------- startup, log init --------")
    log.write_log(INFO, SUCCESS, "logicname[%s]"%args.ln)
    return log
    
def main():
    ''' the main process '''
    global args, log
    try:
        args = init_args()
        init_sig()
        log = init_logger(args)
        kpi_collector = KpiMqCollector(path=args.outpath, program_name=PROG_NAME, interval_minute=args.i)
        #dummy_ticker make sure there is at least a counter=0 record in the KPI output file
        dummy_ticker = KpiTicker(interval=KPI_REPORT_INTERVAL, ticker_name="dummy", prog_name=PROG_NAME)
        for (k, v) in KPI_OID.items():
            dummy_ticker.add_kpi(Kpi(k, v))

        while not terminate:
            #dummy_ticker make sure there is at least a counter=0 record in the KPI output file
            if dummy_ticker.is_tick2record():
                dummy_ticker.output_mq()

            #collect KPI record from MQ, output to file when time inverval reached
            kpi_collector.collect()
            for file in kpi_collector.timed_output():
                log.write_log(INFO, SUCCESS, "Output file [%s]"%file)
            time.sleep(1)
        print "kpi_collector terminated"
    except Exception, e:
        print "main exception %s:%s"%(type(e), e)
        print ("%s: %s"%(e, traceback.format_exc()))
        
if __name__=="__main__":
    SingletonAssure('kpi_collector')
    main()
