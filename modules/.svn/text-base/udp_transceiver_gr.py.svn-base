#!/usr/bin/env python
import sys
from greenlet import greenlet
import socket
import time
import Queue
import netifaces

class AddrWatcher:
    def __init__(self, addr, version=netifaces.AF_INET, wait_time=1):
        self.wait_time = wait_time
        self.addr = addr
        self.version = version

    def go_or_wait(self):
        if self.if_addr_watch(self.addr, self.version):
            return True
        else:
            time.sleep(self.wait_time)
            return False

    @staticmethod
    def if_addr_watch(addr, version=netifaces.AF_INET):
        '''to watch if the specific address is assigned in local machine
            parameter:
                addr: string of IP address
                version: by default is netifaces.AF_INET, it can be netifaces.AF_INET6
            return: 
                True if the address is assigned, otherwise, return False'''

        for i in netifaces.interfaces():
            try:
                for j in netifaces.ifaddresses(i)[version]:
                    try:
                        #print j['addr']
                        if addr == j['addr']:
                            return True
                    except:
                        pass
            except:
                pass
        return False

class UdpTransceiver(greenlet):
    '''UdpTransceiver bind to a udp port to send/recv UDP messages,
    subclass of greenlet to enhance performance'''
    def __init__(self, host=None, port=0, auto_process=True):
        '''Initializate UdpTransceiver. Parameters:
            host: string, bind address/host, default value is None, bind to 0.0.0.0
            port: integer, bind port, default value is 0, bind let system assigns port
            auto_process: if set to true, self.__processing__() will be used to process 
                received messages, otherwise, user shall call self.recv() to retrieve 
                received message to process'''
        self.host = host
        self.port = port
        if (self.host == None):
            self.host = "0.0.0.0"
        self._socket = None
        self.recvq = Queue.Queue(maxsize=1024*100)
        self.sendq = Queue.Queue(maxsize=1024*100)
        self.idle = True
        self.auto_process = auto_process

    def send(self, packet):
        '''Enqueue a to send message to send queue, parameters:
            packet: tuple of (messsage string, (destitation host, destination port))
                message string is the message data to send
                destination host is the string of destination address
                destination port is the integer of destination port'''
        #self._socket.sendto(packet[0], packet[1])
        try:
            self.sendq.put_nowait(packet)
            return True
        except Queue.Full:
            return False

    def recv(self):
        '''if self.auto_process == False, call this to retreive received message in 
            (messsage string, (source host, source port)) tuple, if no message to retrieve
            None will be returned'''
        try:
            return self.recvq.get_nowait()
        except Queue.Empty:
            return None

    def __processing__(self, packet):
        ''' if auto_process == True, all the received packet will be processed by this method,
            leave for sub-class to implement it'''
        pass

    def start(self):
        '''call self.bind() and return True'''
        self.bind()
        return True

    def stop(self):
        '''stop UdpTransceiver, close socket'''
        self.flag = False
        self._CloseSocket()

    def run(self):
        '''Entry point of greenlet, switch to self.recv_svc() and self.send_svc() in sub-greenlet and parent-greenlet
            in loop''' 
        self.flag = True
        gr_r = greenlet(self.recv_svc)
        gr_s = greenlet(self.send_svc)
        while not gr_r.dead and not gr_s.dead:
            self.idle = True
            gr_r.switch()
            gr_s.switch()
            self.parent.switch()


    def send_svc(self):
        '''the task to get sending message from sending Queue and send from socket'''
        while self.flag:
            try:
                #print "send_svc"
                packet = self.sendq.get_nowait()
                self._socket.sendto(packet[0], packet[1]) 
                self.idle=False
            except Queue.Empty:
                self.switch()
            except:
                self.switch()

    def recv_svc(self):
        '''the task to recv Udp message from socket, if self.auto_process is False,
        enqueue to receiving queue, otherwise, invoke self.__processing__() to handle
        the received message'''
        while self.flag:
            try:
                packet = self._socket.recvfrom(4096, socket.MSG_DONTWAIT)
                if self.auto_process:
                    self.__processing__(packet)
                else:
                    while True:
                        try:
                            self.recvq.put_nowait(packet)
                            self.idle=False
                            break
                        except Queue.Full:
                            self.switch()
                            continue
            except Exception, e:
                #print "XXXX %s"%e
                self.switch()

    def _SocketOpen(self):
        '''open UDP socket'''
        if not self._socket:
            self._socket = socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET,
                                    socket.SO_REUSEADDR, 1)

    def _CloseSocket(self):
        '''close UDP socket'''
        if self._socket:
            self._socket.close()
            self._socket = None

    def bind(self):
        """Bind socket to an self.host:self.port.
        """
        self._CloseSocket()
        self._SocketOpen()
        self._socket.bind((self.host, self.port))
        (self.host, self.port) = self._socket.getsockname()
        #self._socket.settimeout(0)


if __name__=="__main__":
    print AddrWatcher.if_addr_watch("192.168.237.130")
    print AddrWatcher.if_addr_watch("192.168.237.131")
    print AddrWatcher.if_addr_watch("192.168.237.132")
    print AddrWatcher.if_addr_watch("192.168.237.133")
    
    from idle_gr import IdleLet
    class EchoSerer(UdpTransceiver):
        def __processing__(self, packet):
            self.send(packet)

    server = EchoSerer(host = "0.0.0.0", port =1812)
    while not server.dead:
        server.switch()
