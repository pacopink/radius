#!/usr/bin/env python
import time
import threading
from pyrad import udp_transceiver

host = "127.0.0.1"
port = 1812
addr = (host, port)
m = 10
n = 1
max_delay=0.0
send_c = 0
recv_c = 0

class CliTrans(udp_transceiver.UdpTransceiver):
    def __processing__(self, packet):
        global recv_c
        print "[%f] Client RECV:"%time.time()
        print packet
        recv_c+=1

client = CliTrans()
client.start()

req = "018d004ab392a15e1b61db6be800068550d9585501067061636f0212147b9aaa6de5775df0ddfa623620f55c0406c0a8f880050600000000501213a6f53d748911fba204784a989dc19e"

#client.send((req.decode('hex'), addr))
#print "[%f] Send REQ"%time.time()

t = time.time()
for i in xrange(0, n):
    for j in xrange(0, m):
        client.send((req.decode('hex'), addr))
    time.sleep(0.1)    


while True:
    print "recv_c [%d]"%recv_c
    if recv_c == m*n:
        break
    time.sleep(1)
    if time.time()-t>20:
        break

client.stop()
