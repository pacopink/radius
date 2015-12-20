#!/bin/env python
#coding:utf8

import struct
from global_def import *

class DipcMsg(object):
    '''Dipc message wrapper'''
    def __init__(self, msg = None):
        self.raw_byte = ''
        self.host = ''
        self.port = 0
        self.character = ''
        self.header = ''
        self.body = ''
        self.msg_type = 0
        self.sender = ''
        #if msg is passed in, decode it
        if msg:
            self.decode(msg)

    def decode(self, msg):
        '''decode a received dicp msg
        parameter:
            msg: a msg dict that recieved from a dipc_interface'''
        self.raw_byte = msg['Buff']
        self.sender = msg['Sender']
        self.msg_type = msg['MsgType']
        if len(self.raw_byte)<56:
            raise Exception("get dipc msg from [%s] with invalid length type[%s]:[%s]"%(self.sender, self.msg_type, self.raw_byte.encode('hex')))
        self.header = self.raw_byte[0:56]
        self.body = self.raw_byte[56:]
        self.unpack_header(self.header)

    def encode(self, body=None, header=None):
        '''endcode a dipc msg to send
        parameter:
            body: the message body
            header: the 56 byte message header'''
        if (header != None):
            self.header = header
        if (body != None):
            self.body = body
        #print("DipcMsg.encode header[%s]"%self.header.encode('hex'))
        #print("DipcMsg.encode body  [%s]"%self.body.encode('hex'))
        self.raw_byte = self.header+self.body
        return self.raw_byte
        
    def unpack_header(self, header=None):
        '''unpack a 56 byte header to self.host, self.port, self.character
        paramter:
            header: the 56 byte msg header'''
        if header != None:
            self.header = header
        (self.host, self.port, self.character) = struct.unpack("=32sI20s", self.header)
        self.host = self.host[0:self.host.find("\0")] #get rid of the padding bytes
        return (self.host, self.port, self.character)

    def pack_header(self, host, port, character):
        '''pack host, port, characther to a 56 byte header string'''
        #32byte host with pading + 4byte port + 20 byte radius request characteristict(fisrt 20bytes of req msg)
        self.host = host
        self.port = port
        self.character = character
        self.header = struct.pack("=%ds%dxI"%(len(self.host), 32-len(self.host)), self.host, self.port)+self.character
        return self.header


class DisconnMsg(DipcMsg):
    '''Decrepit class, radius_disconn no more use dipc to receive disconnect request'''
    def __init__(self, msg = None):
        self.nas_addr = ''
        self.nas_port = 0
        self.secret= ''
        self.acct_session_id = None
        self.acct_multi_session_id = None
        super(DisconnMsg, self).__init__(msg) 

    def pack_body(self, nas_addr, nas_port, secret, acct_session_id, acct_multi_session_id=None):
        #32byte host with pading + 4byte port + 20 byte radius request characteristict(fisrt 20bytes of req msg)
        self.nas_addr = nas_addr 
        self.nas_port = nas_port
        self.secret = secret
        self.acct_session_id = acct_session_id
        self.acct_multi_session_id = acct_multi_session_id

        self.body = encode_variant(nas_addr)
        self.body += encode_uint(nas_port)
        self.body += encode_variant(secret)
        self.body += encode_variant(acct_session_id)
        if acct_multi_session_id:
            self.body += encode_variant(acct_multi_session_id)
        return self.body

    def decode(self, msg):
        super(DisconnMsg, self).decode(msg) 
        if self.msg_type == MT_ACCP_2_DISCONN:
            #print for test
            print self.unpack_body()

    def unpack_body(self, body=None):
        if body != None:
            self.body = body
        ss = self.body
        (self.nas_addr, ss) = decode_variant(ss)
        (self.nas_port, ss) = decode_uint(ss)
        (self.secret, ss) = decode_variant(ss)
        (self.acct_session_id, ss) = decode_variant(ss)
        if len(ss)>0:
            (self.acct_multi_session_id, ss) = decode_variant(ss)
        return (self.nas_addr, self.nas_port, self.secret, self.acct_session_id, self.acct_multi_session_id)

def encode_uint(i):
    return struct.pack("=I",i)

def decode_uint(ss):
    (v, ) = struct.unpack("=I", ss[0:4])
    remain = ss[4:]
    return (v, remain)

def encode_variant(ss):
    l = len(ss)
    return struct.pack("=H%ds"%l, l, ss)

def decode_variant(ss):
    (l, ) = struct.unpack("=H", ss[0:2])
    v = ss[2:2+l]
    remain = ss[2+l:]
    return (v, remain)

if __name__=="__main__":
    m = DisconnMsg()
    m.pack_header("127.0.0.1", 12343, "\0"*20)
    m.pack_body("192.168.0.1",3799,"*#06#", "ADFDEIWJFKDF", "MUL**********1")
    x = m.encode()
    
    print len(x[0:56])
    n = DisconnMsg()
    print n.unpack_header(x[0:56])
    print n.unpack_body(x[56:])
    
