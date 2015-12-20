#!/bin/env python
from pyrad import *
import traceback

res = "024d00a870838ba4c34051ac9c865321fd4de4c71a3a000001371134e553c77457a7e26e1707d56a1c97c83b7d9bc2fb3835fab6f6089e51f71a4983709e8961eb3636544c9de3a224bdc1a286501a3a000001371034e9fe87ac457c947b0450ca386fb535d9f61fc531e14ebc4b71b1c88d075ad3a4d4fe8d42a0d35a9c05a33c5426ec25c08d854f06038c00045012116f7418e7f306a58a10f42f97d07caa010865617073696d"

d = dictionary.Dictionary("../dictionary/radius_dictionary", "../dictionary/dictionary.wispr", "../dictionary/dictionary.ruckus")
p = packet.Packet(dict=d, packet=res.decode('hex'))
p['Ruckus-SSID'] = "SSSIII"
p['WISPr-Bandwidth-Max-Up'] = 1024*1024
p['WISPr-Bandwidth-Max-Down'] = 4*1024*1024
print p
for k in p.keys():
    try:
        #print k
        #print type(k)
        if isinstance(k, str):
            print "Key:[%s]"%k
        elif isinstance(k, tuple):
            print "Key:[%s]"%"-".join(map(str, k))
        else:
            print "XXXXXXX"
            print k
            print type(k)

        for j in p[k]:
            print type(j)
            if isinstance(j, str):
                print "Value:[%s]"%j
            else:
                print "YYYYY"
                print j
                print type(j)
        print ""
    except Exception,e:
        print ("%s: %s"%(e, traceback.format_exc()))

print p.has_key('User-Name')
