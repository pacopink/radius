#!/usr/bin/python
# coding:utf-8
import rad_server
from pyrad import dictionary, packet, server
import bsddb
import time
import threading
import select
from omc_kpi import *
from DipcPy import *

class AcctServer(rad_server.RadServer):
    def __init__(self, addresses=[], port=1813, hosts=None, dict=None, db_file="./sso.db", logger=None, kpi=None):
        rad_server.RadServer.__init__(self, addresses, port, hosts, dict)
        self.logger = logger
        self.kpi = kpi
        self._InitDB(db_file)
        
    def _InitDB(self, db_file):
        self._db = bsddb.btopen(db_file, cachesize=100*1024*1024)
        self._lock = threading.Lock()

    def Sync(self):
        self._lock.acquire()
        self._db.sync()
        self._lock.release()

    def GetCount(self, type="Start"):
        self._lock.acquire()
        count = 0
        for rec in self._db.values():
            if rec.find(type)>=0:
                count+=1
        self._lock.release()
        return count

    def Query(self, key):
        self._lock.acquire()
        try:
            result = self._db[key]
        except:
            result = None
        self._lock.release()
        return result
        
    def _HandlePacket(self, pkt):
        """Process a packet received on the accounting port.
        If this packet should be dropped instead of processed a
        ServerPacketError exception should be raised. The main loop will
        drop the packet and log the reason.

        :param pkt: packet to process
        :type  pkt: Packet class instance
        """
        if pkt.code != packet.AccountingRequest:
            if self.kpi:
                self.kpi.IncreaseKpi("Radius_Other_Invail")
            raise ServerPacketError(
                    'Received non-accounting packet on accounting port')

        if pkt.source[0] not in self.hosts:
            if self.kpi:
                if pkt["Acct-Status-Type"][0] =="Start":
                    self.kpi.IncreaseKpi("Radius_Acct_Start_Invail")
                elif pkt["Acct-Status-Type"][0] =="Stop":
                    self.kpi.IncreaseKpi("Radius_Acct_Stop_Invail")
                else:
                    self.kpi.IncreaseKpi("Radius_Other_Invail")
            raise ServerPacketError('Received packet from unknown host')

        if self.kpi:
            if pkt["Acct-Status-Type"][0] =="Start":
                self.kpi.IncreaseKpi("Radius_Acct_Start")
            elif pkt["Acct-Status-Type"][0] =="Stop":
                self.kpi.IncreaseKpi("Radius_Acct_Stop")
            else:
                self.kpi.IncreaseKpi("Radius_Other_Invail")

        pkt.secret = self.hosts[pkt.source[0]].secret
        #print pkt
        #print ">>>"
        #print pkt["Acct-Status-Type"]
        #print "<<<"
        #for i in pkt.keys():
        #    print "%s = %s"%(i, pkt[i])

        msisdn = pkt["Calling-Station-Id"][0].encode()
        if msisdn[0:1] == "+":
            msisdn = msisdn[1:]
        ip = pkt["Framed-IP-Address"][0]
        status = pkt["Acct-Status-Type"][0]
        timestamp = int(time.time())
        
        self._lock.acquire()
        self._db[msisdn] ="%s,%s,%d"%(ip, status, timestamp)
        self._lock.release()

        #try to reply something
        reply=self.CreateReplyPacket(pkt)
        self.SendReplyPacket(pkt.fd, reply)
        #print ">>>>replay"
        #print reply

    def Start(self):
        """Main loop.
        This method is the main loop for a RADIUS server. It waits
        for packets to arrive via the network and calls other methods
        to process them.
        """
        self._serve_forever = True
        timer = 0
        counter = 0
        counter_err = 0
        while self._serve_forever:
            rfds, wfds, xlist = select.select([self.fd,], [], [], 0.1)
            if len(rfds)>0:
                try:
                    self._ProcessInput(self.fd)
                    counter += 1
                except ServerPacketError as err:
                    counter_err += 1
            now = time.time()
            if now%10 < 2 and (now - timer)>=10:
                if self.logger:
                    self.logger.write_log(INFO, SUCCESS, "RADIUS SERVER STATISTICS: normal msg [%d] error msg [%d]"%(counter, counter_err))
                counter = 0
                counter_err = 0
                timer = now

if __name__=="__main__":
    dict_file="dictionary"
    srv=AcctServer(dict=dictionary.Dictionary(dict_file), addresses=["0.0.0.0"], port=1813, 
            hosts = {"127.0.0.1":server.RemoteHost("127.0.0.1", "Kah3choteereethiejeimaeziecumi", "localhost")},
            db_file = "./sso1.db",
            logger = None)
    #srv.hosts["127.0.0.1"]=server.RemoteHost("127.0.0.1", "Kah3choteereethiejeimaeziecumi", "localhost")
    #srv.BindToAddress("")
    #srv.InitDB("./sso.db")

    t = threading.Thread(target=srv.Start)
    t.start()
    try:
        while(True):
            time.sleep(1)
            srv.Sync()
    except:
        srv.Stop()
    t.join()
    srv.Sync()
