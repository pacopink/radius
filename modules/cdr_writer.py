#!/bin/env python
''' the base class of cdr writer to write cdr to file, the cdr file is switched per file_switch_duration minute'''
import Queue
import time
import os
import traceback
from greenlet import greenlet

class CdrWriter(greenlet):
    '''the base class of cdr writer to write cdr to file, the cdr file is switched per file_switch_duration minute'''
    def __init__(self):
        '''parameters can be changed:
            file_switch_duration: the switch interval of files in minute, default value is 60
            filename_pattern: the output file name pattern, default is "CDR_$TIMESTAMP.cdr", the $TIMESTAMP part will be replaced with the actual timestamp'''
        self.path ="./"
        self.file_switch_duration=60 #60 min
        self.q = Queue.Queue(maxsize=1024*1024)
        self.fd = None
        self.next_switch_time=0
        self.timestamp = 0
        self.terminate = False
        self.current_filename = ''
        self.current_tmp = ''
        self.filename_pattern = "CDR_$TIMESTAMP.cdr"

    def __cdr_to_str__(self, cdr_obj):
        '''for sub-class to serialize the cdr_obj to a cdr string, shall be override'''
        return cdr_obj.__str__()

    def record2queue(self, cdr_obj):
        '''for caller to pass in cdr_obj that to be serialized to a cdr sting'''
        try:
            self.q.put_nowait(cdr_obj)
            return True
        except Queue.Full:
            return False

    def record(self, cdr_obj):
        '''no cached, directly write to file'''
        try:
            self.__write_cdr(cdr_obj)
            self.fd.flush()
        except:
            pass

                
    def run(self):
        '''the main process loop of cdr_writer'''
        self.terminate = False
        last_action = time.time()
        switch_file_f = self.__switch_file_simple
        while not self.terminate:
            now = time.time()
            if now - last_action>=1:
                #write to file per second
                last_action = now    
                switch_file_f()
                self.__batch_write()
            self.parent.switch()

        #do the last batch write and commit it
        switch_file_f()
        self.__batch_write()
        self.__commit_file()

    def stop(self):
        ''' to stop cdr_writer'''
        self.terminate = True
        #commit the file
        while not self.dead:
            self.switch()

    def __write_cdr(self, cdr_obj):
        '''do write a cdr string to cdr file'''
        str_cdr = self.__cdr_to_str__(cdr_obj)
        #print str_cdr
        self.fd.write(str_cdr+"\n")


    def __batch_write(self):
        '''get buffered cdr_obj and write them one by one'''
        while True:
            try:
                cdr = self.q.get_nowait()
                print "__batch_write get a cdr"
                #print cdr
                self.__write_cdr(cdr)
            except Queue.Empty:
                break
            except Exception, e:
                print ("%s: %s"%(e, traceback.format_exc()))
                break
        try:
            self.fd.flush()
        except:
            pass

    @staticmethod
    def get_timestamp(ts=None):
        '''to get the current timestamp in 'YYYYMMDDHHMISS' format'''
        tm = time.localtime(ts)
        return "%04d%02d%02d%02d%02d%02d"%(tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)

    def __next_timestamp(self):
        '''calculate the next time to switch file'''
        min = int(time.time())/60
        floor_min = ((min+self.file_switch_duration-1)/self.file_switch_duration - 1)*self.file_switch_duration
        t = floor_min*60

        if self.timestamp<t or self.fd == None:
            self.timestamp = t
            tm = time.localtime(t)
            return "%04d%02d%02d%02d%02d"%(tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)
        else:
            return None

    def __commit_file(self):
        '''Decrepit: commit a tmp file to a output file'''
        if self.fd:
            self.fd.close()
            self.fd = None
        if len(self.current_tmp) <=0 or len(self.current_filename)<=0:
            return
        else:
            if (not os.path.exists(self.current_tmp)):
                return
            if (os.path.exists(self.current_filename)):
                self.__append_file(self.current_tmp, self.current_filename, remove_src = True)
            else:
                os.rename(self.current_tmp, self.current_filename)

    def __append_file(self, src, dst, remove_src = False):
        '''Decrepit: append a file to another file'''
        fdin = open(src, 'r')
        fdout = open(dst, 'a')
        fdout.write(fdin.read())
        fdin.close()
        fdout.close()
        if remove_src:
            os.remove(src)
        
    def __switch_file(self):
        '''Decrepit: to switch file in a complicated way, seems creates more problem, so it is decrepit'''
        #check if it is time to switch file
        ts = self.__next_timestamp()
        #no need to switch if None
        if ts == None:
            return 
        #commit file before switch file
        self.__commit_file()
        filename = self.filename_pattern.replace("$TIMESTAMP", ts)
        self.current_filename = os.path.join(self.path, filename)
        self.current_tmp = os.path.join(self.path, "."+filename)
        self.fd = open(self.current_tmp, "a")
        return

    def __switch_file_simple(self):
        '''Switch cdr file'''
        #check if it is time to switch file
        ts = self.__next_timestamp()
        #no need to switch if None
        if ts == None:
            return 
        self.__commit_file()
        filename = self.filename_pattern.replace("$TIMESTAMP", ts)
        self.current_filename = os.path.join(self.path, filename)
        self.current_tmp = ''
        self.fd = open(self.current_filename, "a")
        


if __name__=="__main__":
    wt = CdrWriter()
    wt.switch()
    for i in xrange(0,100):
        wt.record(i)
    wt.switch()
    wt.stop()

    print wt.get_timestamp()
    print CdrWriter.get_timestamp()
