import cdr_writer
import time
import traceback

def get_attr(pack, attr_name):
    '''for cdr writer to get radius packet attribute value from pack, and convert to string for cdr writing'''
    try:
        return ','.join(map(str, pack[attr_name])) #convert to str, if multiple values, use ',' to join
    except KeyError:
        return '' #if attribute does not exist, return ''
    except:
        print ("%s: %s"%(e, traceback.format_exc()))
        return ''

class AuthCdrWriter(cdr_writer.CdrWriter):
    '''CDR writer for Radius Authentication'''
    def __init__(self, path, filename_pattern, file_switch_duration=60):
        super(AuthCdrWriter, self).__init__() 
        self.path = path
        self.filename_pattern = filename_pattern
        self.file_switch_duration = file_switch_duration

    def __cdr_to_str__(self, cdr_obj):
        req, reply, user_type, auth_method = cdr_obj
        #initial CDR attributes list
        attrs = list()
        for i in xrange(0, 32):
            attrs.append('')

        #set attribute values
        attrs[0] = self.get_timestamp()
        attrs[1] = 'ACCESS' 
        if auth_method == None:
            attrs[2] = 'invalid'
        else:
            attrs[2] = auth_method
        if reply != None:
            attrs[3] = str(reply.code)
            attrs[4] = get_attr(reply, 'Reply-Message')
        else:
            attrs[3] = '0'
        attrs[5] = get_attr(req, 'User-Name')
	if user_type != None:
	    attrs[6] = user_type
        attrs[7] = get_attr(req, 'Acct-Session-Id')
        attrs[8] = get_attr(req, 'Calling-Station-Id')
        attrs[9] = get_attr(req, 'Called-Station-Id')
        attrs[10] = get_attr(req, 'Framed-IP-Address')
        attrs[11] = get_attr(req, 'NAS-Identifier')
        attrs[12] = get_attr(req, 'NAS-IP-Address')
        attrs[13] = get_attr(req, 'NAS-Port')
        #14 SSID is contained in Called-Station-Id, leave it blank
	if reply != None:
            attrs[15] = get_attr(reply, 'Idle-Timeout')
            attrs[16] = get_attr(reply, 'Session-Timeout')
            attrs[17] = get_attr(reply, 'WISPr-Bandwidth-Max-Up')
            attrs[18] = get_attr(reply, 'WISPr-Bandwidth-Max-Down')
        return '$'.join(attrs)
        
class AcctCdrWriter(cdr_writer.CdrWriter):
    '''CDR writer for Radius Accounting'''
    def __init__(self, path, filename_pattern, file_switch_duration=60):
        super(AcctCdrWriter, self).__init__() 
        self.path = path
        self.filename_pattern = filename_pattern
        self.file_switch_duration = file_switch_duration
        

    def __cdr_to_str__(self, cdr_obj):
        req, reply, user_type, msg = cdr_obj
        #initial CDR attributes list
        attrs = list()
        for i in xrange(0, 32):
            attrs.append('')

        #set attribute values
        attrs[0] = self.get_timestamp()
        attrs[1] = 'ACCOUNT' 
        attrs[2] = get_attr(req, 'Acct-Status-Type')

        if reply != None:
            attrs[3] = str(reply.code)
            #attrs[4] = get_attr(reply, 'Reply-Message')
        else:
            attrs[3] = '0'
            attrs[4] = msg
        attrs[5] = get_attr(req, 'User-Name')
        if user_type != None:
            attrs[6] = user_type
        attrs[7] = get_attr(req, 'Acct-Session-Id')
        attrs[8] = get_attr(req, 'Calling-Station-Id')
        attrs[9] = get_attr(req, 'Called-Station-Id')
        attrs[10] = get_attr(req, 'Framed-IP-Address')
        attrs[11] = get_attr(req, 'NAS-Identifier')
        attrs[12] = get_attr(req, 'NAS-IP-Address')
        attrs[13] = get_attr(req, 'NAS-Port')
        #14 SSID is contained in Called-Station-Id, leave it blank
        attrs[15] = get_attr(req, 'Event-Timestamp')
        if attrs[15] != '':
            attrs[15] = self.get_timestamp(int(attrs[15]))
        if reply != None:
            attrs[16] = get_attr(reply, 'Acct-Session-Time')
            attrs[17] = get_attr(reply, 'Acct-Input-Octets')
            attrs[18] = get_attr(reply, 'Acct-Output-Octets')
            attrs[19] = get_attr(reply, 'Acct-Input-Packets')
            attrs[20] = get_attr(reply, 'Acct-Output-Packets')
        attrs[21] = get_attr(req, 'Acct-Multi-Session-Id')
        return '$'.join(attrs)
        
class DisconnCdrWriter(cdr_writer.CdrWriter):
    '''CDR writer for Radius COA-DISCONN'''
    def __init__(self, path, filename_pattern, file_switch_duration=60):
        super(DisconnCdrWriter, self).__init__() 
        self.path = path
        self.filename_pattern = filename_pattern
        self.file_switch_duration = file_switch_duration

    def __cdr_to_str__(self, cdr_obj):
        dst, pkt, res_pkt, username, mac  = cdr_obj
        res = "timeout"
        if res_pkt:
            if res_pkt.code == 41:
                res = "ACK"
            else:
                res = "NAK"
        try:
            acct_session_id = pkt['Acct-Session-Id'][0]
        except:
            acct_session_id = ''

        try:
            acct_multi_session_id = pkt['Acct-Multi-Session-Id'][0]
        except:
            acct_multi_session_id = ''

        ts = self.get_timestamp()
        return "%s$%s$%d$%s$%s$%s$%s$%s"%(ts, dst[0], dst[1], username, mac, res, acct_session_id, acct_multi_session_id)
        
        
    

