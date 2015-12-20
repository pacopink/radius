#!/bin/env python
#coding:utf8
import binascii
from DipcPy import *
from DipcPy.dipc import *
import threading
import redis
import socket
import time
from endpoint_mgr import *
from global_conf import *
from pyrad import *
import pyrad
from timed_hash import TimedHash
import traceback

import argparse
import os
import sys
import struct

 
class MyServer(udp_transceiver.UdpTransceiver):
    def __processing__(self, packet):
        data = packet[0]
        host = packet[1][0]
        port = packet[1][1]
        addr = struct.pack("=%ds%dxI"%(len(host), 32-len(host)), host, port)
        key = addr+data[0:20] #make addr + first 20 byte as key len= 32+4+20 = 56
        key_hex = key.encode('hex') #to avoid '\0'

        print "[%f] RECV PKG"%time.time()
        print packet

        print "SEND OK ERICSSON"
        self.send(("OK ERICSSON", (host, port)))


server = MyServer(host = '127.0.0.1', port = 1812)
server.start()

try:
    while True:
        time.sleep(1)
except:
    pass

server.stop()
