#!/usr/bin/env python
# server.py
#
# Copyright 2003-2004,2007 Wichert Akkerman <wichert@wiggy.net>

import select
import socket
from pyrad import packet
import logging

logger = logging.getLogger('pyrad')

class RadHost:
    """Generic RADIUS capable host.

    :ivar     dict: RADIUS dictionary
    :type     dict: pyrad.dictionary.Dictionary
    :ivar authport: port to listen on for authentication packets
    :type authport: integer
    :ivar acctport: port to listen on for accounting packets
    :type acctport: integer
    """
    def __init__(self, port=1813, dict=None):
        """Constructor

        :param authport: port to listen on for authentication packets
        :type  authport: integer
        :param acctport: port to listen on for accounting packets
        :type  acctport: integer
        :param     dict: RADIUS dictionary
        :type      dict: pyrad.dictionary.Dictionary
        """
        self.dict = dict
        self.port = port

    def CreatePacket(self, **args):
        """Create a new RADIUS packet.
        This utility function creates a new RADIUS authentication
        packet which can be used to communicate with the RADIUS server
        this client talks to. This is initializing the new packet with
        the dictionary and secret used for the client.

        :return: a new empty packet instance
        :rtype:  pyrad.packet.Packet
        """
        return packet.Packet(dict=self.dict, **args)

    def SendPacket(self, fd, pkt):
        """Send a packet.

        :param fd: socket to send packet with
        :type  fd: socket class instance
        :param pkt: packet to send
        :type  pkt: Packet class instance
        """
        fd.sendto(pkt.Pack(), pkt.source)

    def SendReplyPacket(self, fd, pkt):
        """Send a packet.

        :param fd: socket to send packet with
        :type  fd: socket class instance
        :param pkt: packet to send
        :type  pkt: Packet class instance
        """
        fd.sendto(pkt.Pack(), pkt.source)


class RemoteHost:
    """Remote RADIUS capable host we can talk to.
    """

    def __init__(self, address, secret, name, port=1812):
        """Constructor.

        :param   address: IP address
        :type    address: string
        :param    secret: RADIUS secret
        :type     secret: string
        :param      name: short name (used for logging only)
        :type       name: string
        :param  authport: port used for authentication packets
        :type   authport: integer
        :param  acctport: port used for accounting packets
        :type   acctport: integer
        """
        self.address = address
        self.secret = secret
        self.port = port
        self.name = name


class ServerPacketError(Exception):
    """Exception class for bogus packets.
    ServerPacketError exceptions are only used inside the Server class to
    abort processing of a packet.
    """


class RadServer(RadHost):
    """Basic RADIUS server.
    This class implements the basics of a RADIUS server. It takes care
    of the details of receiving and decoding requests; processing of
    the requests should be done by overloading the appropriate methods
    in derived classes.

    :ivar  hosts: hosts who are allowed to talk to us
    :type  hosts: dictionary of Host class instances
    :ivar  _poll: poll object for network sockets
    :type  _poll: select.poll class instance
    :ivar _fdmap: map of filedescriptors to network sockets
    :type _fdmap: dictionary
    :cvar MaxPacketSize: maximum size of a RADIUS packet
    :type MaxPacketSize: integer
    """

    MaxPacketSize = 8192

    def __init__(self, addresses=[], port=1813, hosts=None,
            dict=None):
        """Constructor.

        :param addresses: IP addresses to listen on
        :type  addresses: sequence of strings
        :param  acctport: port to listen on for accounting packets
        :type   acctport: integer
        :param     hosts: hosts who we can talk to
        :type      hosts: dictionary mapping IP to RemoteHost class instances
        :param      dict: RADIUS dictionary to use
        :type       dict: Dictionary class instance
        """
        RadHost.__init__(self, port, dict)
        if hosts is None:
            self.hosts = {}
        else:
            self.hosts = hosts

        for addr in addresses:
            self.BindToAddress(addr)

    def BindToAddress(self, addr):
        """Add an address to listen to.
        An empty string indicated you want to listen on all addresses.

        :param addr: IP address to listen on
        :type  addr: string
        """
        self.fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.fd.bind((addr, self.port))

    def HandlePacket(self, pkt):
        """to be implement in sub-class
        """
        pass

    def _HandlePacket(self, pkt):
        """Process a packet received on the accounting port.
        If this packet should be dropped instead of processed a
        ServerPacketError exception should be raised. The main loop will
        drop the packet and log the reason.

        :param pkt: packet to process
        :type  pkt: Packet class instance
        """
        if pkt.source[0] not in self.hosts:
            raise ServerPacketError('Received packet from unknown host')

        pkt.secret = self.hosts[pkt.source[0]].secret
        if not pkt.code in [packet.AccountingRequest,
                packet.AccountingResponse]:
            raise ServerPacketError(
                    'Received non-accounting packet on accounting port')
        self.HandlePacket(pkt)


    def _GrabPacket(self, pktgen, fd):
        """Read a packet from a network connection.
        This method assumes there is data waiting for to be read.

        :param fd: socket to read packet from
        :type  fd: socket class instance
        :return: RADIUS packet
        :rtype:  Packet class instance
        """
        (data, source) = fd.recvfrom(self.MaxPacketSize)
        pkt = pktgen(data)
        pkt.source = source
        pkt.fd = fd
        return pkt

    def CreateReplyPacket(self, pkt, **attributes):
        """Create a reply packet.
        Create a new packet which can be returned as a reply to a received
        packet.

        :param pkt:   original packet
        :type pkt:    Packet instance
        """
        reply = pkt.CreateReply(**attributes)
        reply.source = pkt.source
        return reply

    def _ProcessInput(self, fd):
        """Process available data.
        If this packet should be dropped instead of processed a
        PacketError exception should be raised. The main loop will
        drop the packet and log the reason.

        This function calls either HandleAuthPacket() or
        HandleAcctPacket() depending on which socket is being
        processed.

        :param  fd: socket to read packet from
        :type   fd: socket class instance
        """
        pkt = self._GrabPacket(lambda data, s=self:
                s.CreatePacket(packet=data), fd)
        self._HandlePacket(pkt)

    def Start(self):
        """Main loop.
        This method is the main loop for a RADIUS server. It waits
        for packets to arrive via the network and calls other methods
        to process them.
        """
        self._serve_forever = True
        while self._serve_forever:
            rfds, wfds, xlist = select.select([self.fd,], [], [], 0.5)
            if len(rfds)>0:
                try:
                    self._ProcessInput(self.fd)
                except ServerPacketError as err:
                    print('Dropping packet: ' + str(err))
                except packet.PacketError as err:
                    print('Received a broken packet: ' + str(err))

    def Stop(self):
        self._serve_forever = False

if __name__=="__main__":
    print "OK"
