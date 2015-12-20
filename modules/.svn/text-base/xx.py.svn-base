#!/bin/env python
import struct
import pyrad
import hmac
import pyrad.dictionary
import pyrad.packet
from pyrad.eap import eap
from pyrad.eap import key_calculate
from pyrad.eap.eap_def import *
import sys

pp='2959001a8f08979811920bf4297bd89b689c6199310600000006'
pp='2910001a2d71f9ef1f8d71ed90b92abcca2d7100310600000006'
#dict_obj = pyrad.dictionary.Dictionary('/radius/dictionary/radius_dictionary')
ppp = pyrad.packet.Packet(packet=pp.decode('hex'))
print "[%s]"%ppp.__str__()
print "[%d]"%ppp.code
sys.exit(0)




packs = (
  {
  'req':"01a7004703953e2f6ac8e8322073161d24f12270010865617073696d0406ffffffff5012da1681a44704f99567e26d54ff2abca70506000000004f0d02b7000b0165617073696d",
  'res':"0ba7004ee370984d4b567b32d7f365feaa4a0b8e4f16018c0014120a00000f02000200010000110101005012dd61dfcaa3028208fd876af99f84c44c18121f77d4051ffbc65a6b1858aa5b497021"
  },
  {
  'req':"0163007a13a35c49fb96a6c25440ce428a3caf2d010865617073696d0406ffffffff5012cf93951cd4286d5d628f16d9b5bf7fe90506000000004f2e028a002c120a000010010001070500002f29d6c910cbf5a7381411c8669af3c50e03000665617073696d00001812626870e962e262c1a41d1024afe57159",
  'res':"0b63008a2c64632af6bd3e11776fe9d12dc736614f52018b0050120b0000010d0000abcd1234abcd1234abcd1234abcd1234bcd1234abcd1234abcd1234abcd1234acd1234abcd1234abcd1234abcd1234ab0b05000075cdf13a0678a3388df80422009edc245012cf61e8cde389c9c2fe019e69846e22451812626870e963e362c1a41d1024afe57159",
  },
  {
      'req':"014d006a6afab4587ba978f6d7feb0b6a302e255010865617073696d0406ffffffff50123b6142287fcf8d9cd1719ee2093c40d50506000000001812626870e963e362c1a41d1024afe571594f1e028b001c120b00000b05000035227418da109ed2e8cb5c8cbf752995",
      'res':"024d00a870838ba4c34051ac9c865321fd4de4c71a3a000001371134e553c77457a7e26e1707d56a1c97c83b7d9bc2fb3835fab6f6089e51f71a4983709e8961eb3636544c9de3a224bdc1a286501a3a000001371034e9fe87ac457c947b0450ca386fb535d9f61fc531e14ebc4b71b1c88d075ad3a4d4fe8d42a0d35a9c05a33c5426ec25c08d854f06038c00045012116f7418e7f306a58a10f42f97d07caa010865617073696d"
  },
  {
      'req':"0140004b5b788293e5dcbbe4f55e4e002f88565d01067061636f03131764b47f5c71ae57aabba97130924ba39d0406c0a8f88005060000000050124b5b56bf3084d6ed0f4bd1b90ebabb18",
      'res':"024000141cf1a621b9262fe44564d436af262c60"
  },
  )
 
Rand1 = 'abcd1234abcd1234abcd1234abcd1234'
Rand2 = 'bcd1234abcd1234abcd1234abcd1234a'
Rand3 = 'cd1234abcd1234abcd1234abcd1234ab'
KC1 = '0011223344556677'
KC2 = '1021324354657687'
KC3 = '30415263748596a7'
SRES1 = '1234abcd'
SRES2 = '234abcd1'
SRES3 = '34abcd12'
shared_key='testing123'

req_auth = ''

selected_version = 0
version_list = 0
nonce_mt = 0
identify = 0
kc = (KC1+KC2+KC3).decode('hex')



def ProcRadius(buff):
    ss = buff.decode('hex')
    p = pyrad.packet.Packet(secret=shared_key, packet=ss)
    print "\n==============================================="
    print "RADIUS HEX[%s]"%buff
    print "RAW_PACK  [%s]"%p.raw_packet.encode('hex')
    print "SHARED_SCR[%s]"%p.secret
    print "IDENTIFY  [%d]"%p.id
    print "AUTHENTICATOR[%s]"%p.authenticator.encode('hex')
    print "RECAL_AUTH   [%s]"%p.CalculateAuth().encode('hex')
    global req_auth
    req_auth = p.authenticator.encode('hex')
    print p
    if (p.has_key(79)):
        buff2 = p.raw_packet.encode('hex').replace(p[80][0].encode('hex'), "0"*32)
        print "BUFFER2   [%s]"%buff2
        print "EAP_MSG      [%s]"%p[79][0].encode('hex')
        ma = key_calculate.get_message_authenticator(shared_key, buff2.decode('hex'))
        print "RECAL_MSG_AUTH[%s]"%ma.encode('hex')
        print "MSG_AUTH      [%s]"%p[80][0].encode('hex')
        eap_msg = eap.eap_msg()
        print "decode eap result[%d]"%eap_msg.decode(p[79][0])
        eap_msg.dump()
        print eap_msg

        global identify, nonce_mt, selected_version
        if (eap_msg.type == EAP_TYPE['IDENTIFY']):
            identify = eap_msg.data
        if (eap_msg.has_key('NONCE_MT')):
            nonce_mt = eap_msg['NONCE_MT'].data
        if (eap_msg.has_key('SELECTED_VERSION')):
            selected_version = struct.pack(">H", eap_msg['SELECTED_VERSION'].selected_version)

def ProcRadius2(buff, req_auth):
    ss = buff.decode('hex')
    p = pyrad.packet.Packet(secret=shared_key, packet=ss)
    print "\n==============================================="
    print "RADIUS HEX[%s]"%buff
    print "RAW_PACK  [%s]"%p.raw_packet.encode('hex')
    print "SHARED_SCR[%s]"%p.secret
    print "IDENTIFY  [%d]"%p.id
    print "REQ_AUTH     [%s]"%req_auth
    print "AUTHENTICATOR[%s]"%p.authenticator.encode('hex')
    print "RECAL_AUTH   [%s]"%p.CalculateAuthRsp(req_auth.decode('hex')).encode('hex')
    print p
    if (p.has_key(79)):
        buff2 = p.raw_packet.encode('hex').replace(p[80][0].encode('hex'), "0"*32)
        print "BUFFER2   [%s]"%buff2
        print "EAP_MSG      [%s]"%p[79][0].encode('hex')

        buff3 = buff2.replace(p.authenticator.encode('hex'), req_auth) #replace the auth to request auth, before calculate the msg_auth
        ma = key_calculate.get_message_authenticator(shared_key, buff3.decode('hex'))
        print "RECAL_MSG_AUTH[%s]"%ma.encode('hex')
        print "MSG_AUTH      [%s]"%p[80][0].encode('hex')
        eap_msg = eap.eap_msg()
        print "decode eap result[%d]"%eap_msg.decode(p[79][0])
        eap_msg.dump()
        print eap_msg

        global version_list
        if (eap_msg.has_key('VERSION_LIST')):
            format_str = ">"+"H"*len(eap_msg['VERSION_LIST'].version_list)
            print eap_msg['VERSION_LIST'].version_list
            version_list = struct.pack(format_str, *eap_msg['VERSION_LIST'].version_list)

for pack in packs:
    ProcRadius(pack['req'])
    ProcRadius2(pack['res'], req_auth)
    if nonce_mt != 0:
        print key_calculate.get_mk(identify, kc, nonce_mt, version_list, selected_version).encode('hex')
        nonce_mt = 0
