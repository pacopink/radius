#!/bin/env python
#coding:utf8
import struct
import hmac
import hashlib
import eap_util

def get_message_authenticator(shared_key, buffer):
    h = hmac.HMAC(key=shared_key)
    h.update(buffer)
    return h.digest()

def xor(a, b):
    if (len(a) == len(b)):
        al = struct.unpack("%dB"%len(a), a)
        bl = struct.unpack("%dB"%len(b), b)
        cl = list()
        for i in xrange(0, len(al)):
            cl.append(al[i]^bl[i])
        return struct.pack("%dB"%len(cl), *cl)
    else:
        return 0


def get_pap_encrypt_pwd(shared_key, auth, buff):
    '''
    Call the shared secret S and the pseudo-random 128-bit Request
    Authenticator RA. Break the password into 16-octet chunks p1, p2,
    etc. with the last one padded at the end with nulls to a 16-octet
    boundary. Call the ciphertext blocks c(1), c(2), etc. We’ll need
    intermediate values b1, b2, etc.
    b1 = MD5(S + RA) c(1) = p1 xor b1
    b2 = MD5(S + c(1)) c(2) = p2 xor b2
    . .
    . .
    . .
    bi = MD5(S + c(i-1)) c(i) = pi xor bi
    The String will contain c(1)+c(2)+...+c(i) where + denotes
    concatenation.
    '''
    #print "shared_key=[%s]"%shared_key
    #print "auth      =[%s]"%auth.encode('hex')
    #print "buff      =[%s]"%buff

    l = len(buff)
    ll = (l+15)/16*16
    buff2 = buff
    if ll>l:
        buff2 = struct.pack("%ds%dx"%(l, ll-l), buff)

    h = hashlib.md5()
    last_c = ''
    p_list = list()
    for i in xrange(0, ll/16):
        k = shared_key+last_c
        if last_c == '':
            k = shared_key+auth
        h.update(k)
        c = h.digest()
        p_list.append(xor(c, buff2[i*16:i*16+16]))
        last_c = c

    return ''.join(p_list)

def get_chap_rsp(chap_id, password, challenge):
    '''
    Md5(chapId+password+chapChallenge)
    '''
    s = chap_id+password+challenge
    h = hashlib.md5()
    h.update(s)
    return h.digest()

   

def get_mk(id, kc, nonce_mt, version_list, selected_version):
    '''
    RFC4186
    On EAP-SIM full authentication, a Master Key (MK) is derived from the
    underlying GSM authentication values (Kc keys), the NONCE_MT, and
    other relevant context as follows.
    MK = SHA1(Identity|n*Kc| NONCE_MT| Version List| Selected Version)
    In the formula above, the "|" character denotes concatenation.
    "Identity" denotes the peer identity string without any terminating
    null characters. It is the identity from the last AT_IDENTITY
    attribute sent by the peer in this exchange, or, if AT_IDENTITY was
    not used, it is the identity from the EAP-Response/Identity packet.
    The identity string is included as-is, without any changes. As
    discussed in Section 4.2.2.2, relying on EAP-Response/Identity for
    conveying the EAP-SIM peer identity is discouraged, and the server
    SHOULD use the EAP-SIM method-specific identity attributes.
    The notation n*Kc in the formula above denotes the n Kc values
    concatenated. The Kc keys are used in the same order as the RAND
    challenges in AT_RAND attribute. NONCE_MT denotes the NONCE_MT value
    (not the AT_NONCE_MT attribute, but only the nonce value). The
    Version List includes the 2-byte-supported version numbers from
    AT_VERSION_LIST, in the same order as in the attribute. The Selected
    Version is the 2-byte selected version from AT_SELECTED_VERSION.
    Network byte order is used, just as in the attributes. The hash
    function SHA-1 is specified in [SHA-1]. If several EAP/SIM/Start
    roundtrips are used in an EAP-SIM exchange, then the NONCE_MT,
    Version List and Selected version from the last EAP/SIM/Start round
    are used, and the previous EAP/SIM/Start rounds are ignored.
    '''
    print "get_mk:"
    print "\tid=[%s]"%id
    print "\tkc=[%s]"%kc.encode('hex')
    print "\tnonce_mt=[%s]"%nonce_mt.encode('hex')
    print "\tversion_list=[%s]"%version_list.encode('hex')
    print "\tselected_version=[%s]"%selected_version.encode('hex')
    buff = id+kc+nonce_mt+version_list+selected_version
    h = hashlib.sha1()
    h.update(buff)
    return h.digest()

def get_eapsim_keys(mk):
    (ret, fk) = eap_util.fips186_2prf(mk)
    result = dict()
    if ret == 0 and len(fk)!=160:
        return (0, result)
    result['k_encr'] = fk[0:16]
    result['k_aut'] = fk[16:32]
    result['msk'] = fk[32:96]
    result['emsk'] = fk[96:160]
    return (1, result)

def get_mac(k_aut, eap_pack, nonce_or_sres):
    h=hmac.HMAC(key=k_aut, digestmod=hashlib.sha1)
    h.update(eap_pack+nonce_or_sres)
    return h.digest()[0:16]

if __name__=="__main__":
    shared_key='testing123'
    pwd = 'ericsson'
    auth = 'b392a15e1b61db6be800068550d95855'.decode('hex')
    print get_pap_encrypt_pwd(shared_key, auth, pwd).encode('hex')
    print "147b9aaa6de5775df0ddfa623620f55c"

    mac="75cdf13a0678a3388df80422009edc24"
    mk ="b2e7a348f2eaf846cbcacc98a809ea7dfe1e94fc"
    (ret, res) = get_eapsim_keys(mk.decode('hex'))
    k_aut = res['k_aut']
    #eap_pack = "028a002c120a000010010001070500002f29d6c910cbf5a7381411c8669af3c50e03000665617073696d0000"
    eap_pack = "018b0050120b0000010d0000abcd1234abcd1234abcd1234abcd1234bcd1234abcd1234abcd1234abcd1234acd1234abcd1234abcd1234abcd1234ab0b05000075cdf13a0678a3388df80422009edc24".replace(mac,"0"*len(mac))
    nonce_mt = "2f29d6c910cbf5a7381411c8669af3c5"
    print "k_aut    = [%s]"%k_aut.encode('hex')
    print "req calc mac = [%s]"%get_mac(k_aut, eap_pack.decode('hex'), nonce_mt.decode('hex')).encode('hex')
    print "req mac      = [%s]"%mac
    


    SRES1 = '1234abcd'
    SRES2 = '234abcd1'
    SRES3 = '34abcd12'
    sres = SRES1+SRES2+SRES3
    mac = "35227418da109ed2e8cb5c8cbf752995"
    eap_pack = "028b001c120b00000b05000035227418da109ed2e8cb5c8cbf752995".replace(mac, "0"*len(mac))

    print "res calc mac = [%s]"%get_mac(k_aut, eap_pack.decode('hex'), sres.decode('hex')).encode('hex')
    print "res mac      = [%s]"%mac

