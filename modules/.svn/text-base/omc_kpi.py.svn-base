#!/usr/bin/env python
#coding: utf8

import time
import os
import threading
from sysv_ipc import *

############ CONFIG ####################
MQ_KEY = 1874 #MQ for KPI collector
########################################

class KpiException(Exception):
    pass

class Kpi:
    '''A generic KPI counter, with Name, OID, Counter'''
    def __init__(self, name, oid):
        '''parameter:
    name: the comprehensive name of a KPI, KpiTicker will use it as a key
    oid: the oid of a KPI'''
        self.name = name
        self.oid = oid
        self.counter = 0
    def reset(self):
        '''reset the kpi counter to 0'''
        self.counter = 0

class KpiTicker:
    '''Class to hold a set of KPIs, application can increase/decrease/set the KPI counter via Name,
       and is_tick2record API is provided for application to check if it is time to output KPIs,
       if yes, application can call output to write to file or call outputMQ to write to MQ,
       after the output, all KPI counters will be reset to 0.
       The output file name will be: [hostname]-KPI-[prog_name]-[TimeStamp].txt
       The output record will be: [TimeStamp]|[TickerName]|KPI|[OID]|[COUNTER]
'''
    def __init__(self, outpath="./", ticker_name="ticker", prog_name="prog", interval=300, offset=0):
        '''parameters:
    output: the output path, if user call output to write KPI to a file
    ticker_name: the kpi catagory name which will appare in the KPI record
    prog_name: part the kpi file name, if output is invoked
    interval: the interval for this ticker
    offset: the second of offset to interval, default value is 0, example: if interval=300, offset=0, ticker will active @00 second every 5 min, if offset=5,ticker will active @05 second every 5 min.
'''
        self.interval = interval
        self.outpath = outpath
        self.ticker_name = ticker_name
        self.prog_name = prog_name
        self.offset = offset
        self.timer = 0
        self.kpi_table = dict()
        self.hostname = os.environ["HOSTNAME"]
        self.lock = threading.Lock()
        self.mq = None #will be initialized when first time used

        if not (os.path.isdir(self.outpath)):
            raise KpiException("Outpath [%s] not a valid dir"%(self.outpath))
        if self.interval < 1:
            raise KpiException("Invalid interval [%d]"%(self.interval))
    
    def add_kpi(self, kpi):
        '''add a kpi to kpi_table'''
        self.kpi_table[kpi.name] = kpi

    def is_tick2record(self):
        '''check if the interval is reached and the ticker shall take action
it is the user's responsibility to call this function, if the return is true,
it is also the user's responsibility to call output or output_mq to take the actual action'''
        now = time.time()
        if int(now-self.offset)%self.interval < 2 and (now-self.timer)>=self.interval:
            self.timer = now
            return True
        else:
            return False

    def increase_kpi(self, kpi_name, step=1):
        '''Increase a KPI counter by step, default step is 1'''
        self.lock.acquire()
        #if self.kpi_table.has_key(kpi_name):
        self.kpi_table[kpi_name].counter += step
        self.lock.release()

    def decrease_kpi(self, kpi_name, step=1):
        '''Decrease a KPI counter by step, default step is 1'''
        self.lock.acquire()
        #if self.kpi_table.has_key(kpi_name):
        self.kpi_table[kpi_name].counter -= step
        self.lock.release()

    def set_kpi(self, kpi_name, value):
        '''Arbitary set a KPI counter to a value'''
        self.lock.acquire()
        #if self.kpi_table.has_key(kpi_name):
        self.kpi_table[kpi_name].counter = value
        self.lock.release()


    def output(self):
        '''simply write to a KPI file, mainly used for single instance mode'''
        timestring = time.strftime("%Y%m%d%H%M%S", time.localtime(self.timer))
        filename = os.path.join(self.outpath, "%s-KPI-%s-%s.txt"%(self.hostname, self.ticker_name, timestring))
        f = open(filename, "w")
        self.lock.acquire()
        for kpi in self.kpi_table.values():
        #20131017023504|kpi_collector_be|KPI|1.3.6.1.4.1.193.176.10.2.1.3.2|0
            f.write("%s|%s|KPI|%s|%d\n"%(timestring, self.prog_name, kpi.oid, kpi.counter))
            kpi.reset()
        self.lock.release()
        f.close()

    def output_mq(self):
        '''multiple instances can write a KPI statistics to a MQ message, let KpiMqCollector to collect and aggregate to a single file'''
        if self.mq == None:
            self.mq = MessageQueue(MQ_KEY, IPC_CREAT)
        timestring = time.strftime("%Y%m%d%H%M%S", time.localtime(self.timer))
        self.lock.acquire()
        for kpi in self.kpi_table.values():
        #20131017023504|kpi_collector_be|KPI|1.3.6.1.4.1.193.176.10.2.1.3.2|0
            try:
                self.mq.send("%s|%s|KPI|%s|%d"%(timestring, self.prog_name, kpi.oid, kpi.counter), block=False)
            except:
                pass
            kpi.reset()
        self.lock.release()


class KpiMqCollector(object):
    '''Collects KPIs in MQ, and do aggregation and output to a file periodically'''
    def __init__(self, path, program_name, interval_minute=1, delay=5):
        '''Parameters:
    path: the path to output kpi files
    program_name: this string will be part of the kpi filename
    interval_minute: the interval to output kpi file, default value 1
    delay: the max delay of a MQ message, if it is older than now-delay, will be discarded'''
        self.mq = MessageQueue(MQ_KEY, IPC_CREAT)
        self.hostname = os.environ["HOSTNAME"]
        self.program_name = program_name
        self.delay = delay
        self.kpi_accumulator = dict()
        self.path = path
        self.interval_minute = interval_minute

    def collect(self):
        '''collect all KPI record from MQ, ceiling the timestamp to the nearest next time to output KPI file,
aggregated counter via keys'''
        now = int(time.time())
        while True:
            try:
                recv = self.mq.receive(block=False)
                #print recv 
                #('20150701102830|tester1|KPI|1.3.6.1.4.1.193.176.10.2.7.8|8888', 1)
                msg = recv[0]
                v = msg.split('|')
                if len(v) != 5:
                    #if should have 5 fields, if not just skip it
                    continue
                timestamp =  int(time.mktime(time.strptime(v[0], "%Y%m%d%H%M%S")))
                if (now - timestamp>self.delay):
                    #discard msg that exceed the max delay
                    print "DISCARD: [%d][%d]"%(now, timestamp)
                    continue
                #trim the timestamp
                trim_sec = self.interval_minute*60
                timestamp = int(timestamp+trim_sec-1)/trim_sec*trim_sec
                tm = time.localtime(timestamp)
                tm_str = "%04d%02d%02d%02d%02d%02d"%(tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)
                
                #do accumulator
                key = "%s|%s|%s|%s"%(tm_str, v[1], v[2], v[3])
                count = int(v[4])
                if self.kpi_accumulator.has_key(timestamp):
                    if self.kpi_accumulator[timestamp].has_key(key):
                        self.kpi_accumulator[timestamp][key] += count
                    else:
                        self.kpi_accumulator[timestamp][key] = count
                else:
                    print "New Accumulator timetamp[%d]"%timestamp
                    self.kpi_accumulator[timestamp] = dict()
                    self.kpi_accumulator[timestamp][key] = count
                #print self.kpi_accumulator
                #print "***********************************"
            except BusyError, e:
                break

    def timed_output(self):
        '''check timestamp of all itmes in kpi_accumulator, if it is time to output, call _write_file to output it to KPI file and delete it'''
        outfiles = list()
        now = time.time()
        for k,v in self.kpi_accumulator.items():
            if now - k > (self.delay+5):  #here we add 5 more second for safty
                #if time to write to file, write and delete the item
                outfiles.append(self._write_file(k, v))
                del self.kpi_accumulator[k]
        return outfiles


    def _write_file(self, timestamp, kpi_dict):
        '''do write a kpi_accumulator item to KPI file'''
        timestring = time.strftime("%Y%m%d%H%M%S", time.localtime(timestamp))
        filename = os.path.join(self.path, "%s-KPI-%s-%s.txt"%(self.hostname, self.program_name, timestring))
        tmp      = os.path.join(self.path, ".%s-KPI-%s-%s.txt"%(self.hostname, self.program_name, timestring))
        #write to tmp file first
        f = open(tmp, "w")
        k = kpi_dict.keys()
        k.sort()
        for key in k:
            f.write("%s|%d\n"%(key, kpi_dict[key]))
        f.close()
        #commit tmp file
        os.rename(tmp, filename)
        return filename
                
        

if __name__=="__main__":
    kpi_collector = KpiMqCollector(path="./", program_name="radius", interval_minute=1)

    #simulate the KpiTicker of process #1
    kpi_ticker = KpiTicker(interval = 5, ticker_name="tester", prog_name = "tester1")
    kpi_ticker.add_kpi(Kpi("Radius_Acct_Start", "1.3.6.1.4.1.193.176.10.2.7.0"));
    kpi_ticker.add_kpi(Kpi("Radius_Acct_Stop", "1.3.6.1.4.1.193.176.10.2.7.1"));
    kpi_ticker.add_kpi(Kpi("NUM_OF_XXX", "1.3.6.1.4.1.193.176.10.2.7.8"));
    kpi_ticker.add_kpi(Kpi("NUM_OF_COUNT", "1.3.6.1.4.1.193.176.10.2.7.9"));
    #simulate the KpiTicker of process #2
    kpi_ticker2 = KpiTicker(interval = 5, ticker_name="tester", prog_name = "tester1")
    kpi_ticker2.add_kpi(Kpi("Radius_Acct_Start", "1.3.6.1.4.1.193.176.10.2.7.0"));
    kpi_ticker2.add_kpi(Kpi("Radius_Acct_Stop", "1.3.6.1.4.1.193.176.10.2.7.1"));
    kpi_ticker2.add_kpi(Kpi("NUM_OF_XXX", "1.3.6.1.4.1.193.176.10.2.7.8"));
    kpi_ticker2.add_kpi(Kpi("NUM_OF_COUNT", "1.3.6.1.4.1.193.176.10.2.7.10"));

    count1 = 0
    count2 = 0

    while True:
        if kpi_ticker.is_tick2record():
            kpi_ticker.set_kpi("NUM_OF_XXX", 1)
            kpi_ticker.set_kpi("NUM_OF_COUNT", count1)
            kpi_ticker.output_mq()
            count1 = 0
        else:
            count1 += 1
            kpi_ticker.increase_kpi("Radius_Acct_Start")
            kpi_ticker.decrease_kpi("Radius_Acct_Stop")

        if kpi_ticker2.is_tick2record():
            kpi_ticker2.set_kpi("NUM_OF_XXX", 0)
            kpi_ticker2.set_kpi("NUM_OF_COUNT", count2)
            kpi_ticker2.output_mq()
            count2 = 0
        else:
            count2 += 1
            kpi_ticker2.increase_kpi("Radius_Acct_Start")
            kpi_ticker2.decrease_kpi("Radius_Acct_Stop")

        kpi_collector.collect()
        kpi_collector.timed_output()
        time.sleep(0.5)
