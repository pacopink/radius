#!/bin/env python
import struct
import pyrad
import hmac
import pyrad.packet
import pyrad.dictionary
from pyrad.eap import eap
from pyrad.eap import key_calculate
from pyrad.eap.eap_def import *

x = "04c600a4419ceec8604109aa57b89d62174d93cc01067061636f1f1330302d32332d31342d32352d44352d32342c1335334239313438322d3030303030303039324c3078363333303633333533323330333233323336363633303635333033303332333333313334333233353634333533323334333533333332363636333635333836323330333733363337280600000001501244c67a2c4162941326068af3ec27f688"

import os
path = '/radius/dictionary'
dict_list=list()
def ff(arg, dirname, fnames):
    if dirname == path:
        for f in fnames:
            if f[0:1] == '.':
                continue
            dict_list.append(os.path.join(dirname, f))

os.path.walk(path, ff, None)
print dict_list
dict_obj = pyrad.dictionary.Dictionary(*dict_list)


pkt = pyrad.packet.AcctPacket(secret="*#06#", packet=x.decode("hex"))
print pkt
print "[%s]"%pkt[80][0].encode('hex')
buffer = pkt.raw_packet.replace(pkt[80][0], "\0"*16)
expect_msg_auth = key_calculate.get_message_authenticator(pkt.secret, buffer)
print "[%s]"%expect_msg_auth.encode('hex')
print pkt.Pack().encode('hex')

##########################3
pkt = pyrad.packet.AcctPacket(dict=dict_obj, code=40, secret="*#06#")
print pkt.code
pkt.AddAttribute('Acct-Session-Id','53B91482-00000009')
pkt.AddAttribute('Acct-Multi-Session-Id', '633063353230323236663065303032333134323564353234353332666365386230373637'.decode('hex'))
pkt.AddAttribute('State', '633063353230323236663065303032333134323564353234353332666365386230373637'.decode('hex'))
pkt.AddAttribute('User-Name', 'paco')
pkt.authenticator='\0'*16
print pkt.Pack().encode('hex')
print pkt.authenticator.encode('hex')
print "***"
print pkt.dict
print pkt.code
print pkt.id
if pkt.has_key('State'):
    print pkt['State'][0].encode('hex')
