#!/bin/env python
import struct
from eap_def import *

class eap_sim_attr:
    def __init__(self):
        self.attr_type = 0
        self.attr_len = 0
        self.data = ''
        self.actual_len = 0 
        self.attr_value = ''
        self.version_list = ''
        self.selected_version = 0
        self.rand_list=''

    def decode(self, raw):
        msg_len = len(raw)
        if(msg_len<4):
            return -1

        offset = 0
        (self.attr_type, self.attr_len, reserve)  = struct.unpack('>BBH', raw[offset:offset+4])
        offset+=4
        if (self.attr_len*4) > msg_len:
            return -1
        self.data = raw[offset:offset+(self.attr_len-1)*4]
        if (self.attr_type == EAP_AT['SELECTED_VERSION']):
            self.selected_version = reserve
        if (self.attr_type == EAP_AT['VERSION_LIST']):
            self.actual_len = reserve
            self.version_list = struct.unpack(">"+"H"*(self.actual_len/2), raw[offset:offset+(self.actual_len)])
        if (self.attr_type == EAP_AT['RAND']):
            x = (self.attr_len-1)/4
            self.rand_list = list()
            for i in xrange(0,x):
                self.rand_list.append(self.data[i*16:i*16+16])

        return self.attr_len*4

    def dump(self):
        print ""
        print "ATTR_TYPE[%s]"%translate_eap(AT_EAP, self.attr_type)
        print "ATTR_LEN[%d]"%self.attr_len
        print "ATTR_DATA_HEX[%s]"%self.data.encode('hex')
        if (self.attr_type == EAP_AT['SELECTED_VERSION']):
            print "ATTR_SELECTED_VERSION: %d"%self.selected_version
        if (self.attr_type == EAP_AT['VERSION_LIST']):
            print "ATTR_ACT_LEN[%d]"%self.actual_len
            print "ATTR_VERSION: %s"%(",".join(map(str, self.version_list)))
        if (self.attr_type == EAP_AT['RAND']):
            for r in self.rand_list:
                print "RAND[%s]"%(r.encode('hex'))


class eap_msg(dict):
    def __init__(self):
        self.raw_msg=''
        self.code = 0
        self.id = 0
        self.len = 0
        self.type = 0
        self.subtype = 0
        self.data = ''
        self.attrs = list()
        self.attr_dict = dict()

    def decode(self, raw_msg):
        self.raw_msg = raw_msg
        msg_len = len(self.raw_msg)
        if (msg_len<4):
            return -1
        offset = 0
        (self.code, self.id, self.len) = struct.unpack('>BBH', raw_msg[offset:offset+4])
        if (self.len != msg_len):
            print "eap_msg get len[%d] <> input raw_msg len[%d]"%(self.len, msg_len)
            return -1
        offset += 4
        print "OFFSET[%d] MSG_LEN[%d]"%(offset, msg_len)
        if (offset == msg_len):
            return offset

        (self.type,) = struct.unpack('B', raw_msg[offset:offset+1])
        offset += 1
        self.data = raw_msg[offset:]
        if self.type == EAP_TYPE['IDENTIFY']:
            return msg_len
        elif (self.type == EAP_TYPE['SIM']):
            (self.subtype, reserve) =  struct.unpack('>BH', raw_msg[offset:offset+3])
            offset += 3
            self.data = raw_msg[offset:]
            while ((msg_len-offset)>0):
                attr = eap_sim_attr()
                consumed = attr.decode(raw_msg[offset:])
                if (consumed>0):
                    self.attrs.append(attr)
                    self[translate_eap(AT_EAP, attr.attr_type)] = attr
                else:
                    print "failed to consume eap attribute [%d]"%consumed
                offset += consumed
            return offset
        else:
            return -1

    def dump(self):
        print ""
        print "CODE[%s]"%translate_eap(CODE_EAP, self.code)
        print "ID[%d]"%self.id
        print "LEN[%d]"%self.len
        print "TYPE[%s]"%translate_eap(TYPE_EAP, self.type)
        print "SUBTYPE[%s]"%translate_eap(SUBTYPE_EAP, self.subtype)
        if (self.type == EAP_TYPE['IDENTIFY']):
            print "DATA[%s]"%(self.data)
        else:
            print "HEX_DATA[%s]"%(self.data.encode('hex'))
        for a in self.attrs:
            a.dump()

        
