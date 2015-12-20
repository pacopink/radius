#!/bin/env python
import eap_util

#(ret, fk) = eap_util.fips186_2prf("b2e7a348f2eaf846cbcacc98a809ea7dfe1e94fc".decode('hex'))
#if ret == 1:
#    print fk.encode('hex')
#else:
#    print "error"
#
#(ret, fk) = eap_util.fips186_2prf("b2e7a348f2eaf846cbcacc98a809ea7dfe1e94".decode('hex'))
#if ret == 1:
#    print fk.encode('hex')
#else:
#    print "error"
#

def get_eapsim_keys(mk):
    (ret, fk) = eap_util.fips186_2prf(mk)
    result = dict()
    if ret == 0 and len(fk)!=160:
        return (0, result)
    result['K_encr'] = fk[0:16]
    result['K_aut'] = fk[16:32]
    result['msk'] = fk[32:96]
    result['emsk'] = fk[96:160]
    return (1, result)

def testtest(mk):
    (ret, keys) = get_eapsim_keys(mk)
    if ret == 0:
        print "ERROR"
   
    for (k,v) in keys.items():
        print "%s = [%s]"%(k, v.encode('hex'))


testtest("b2e7a348f2eaf846cbcacc98a809ea7dfe1e94fc".decode('hex'))
testtest("b2e7a348f2eaf846cbcacc98a809ea7dfe1e94".decode('hex'))
testtest("b2e7a348f2eaf846cbcacc98a809ea7dfe1e0000".decode('hex'))






