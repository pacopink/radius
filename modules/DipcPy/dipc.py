#!/usr/bin/env python
#Wrapper classes for dipc_interface and logger from DipcPy.so
from DipcPy import *
import os
import sys

def get_str_from_cmd(cmd):
    '''get the result string from cmdline'''
    p = os.popen(cmd)
    strip = p.readline().strip()
    try:
        p.close()
    except Exception, e:
        print e
        
    return strip

def SingletonAssure(name):
    path = "%s/work"%os.getenv('OCG_HOME')
    if not os.path.lexists(path):
        print "Path %s not exists, cannot read PID file to check, exit!!"%(path) 
        sys.exit(1)
    #try to get pid
    pid_file = "%s/.pid_%s"%(path, name)
    #print "PID_FILE: %s"%pid_file
    IMPOSSIBLE_STRING = 'XYZ!@#$'
    pid = IMPOSSIBLE_STRING #initialize it with an impossible string 
    try:
        f = open(pid_file, 'r')
        pid = f.readline().strip()
        f.close()
    except:
        pass
        
    '''if current instance is the singletone instance in current system, pass, if not, sys.exit(0)'''
    cmd = "ps -ef|grep %s|grep %s|grep -v grep|grep -v vi|grep -v more|grep -v \"/bin/*sh\"|wc -l"%(pid, name)
    #print cmd
    if int(get_str_from_cmd(cmd))>=1:
        print "Another %s is running with pid %s, this program shall run in singlton mode, so exist myself"%(name, pid)
        sys.exit(1)
    else:
        f = open(pid_file, 'w')
        f.write(str(os.getpid()))
        f.close()

def safe_str(ss):
    """!!!IMPORTANT!!!  this function will return with a valid Python str object without '\0' bye in the mid to avoid passing string with "\0" in mid to C/C++ extend function like write_log and cause unexpected TypeError exception"""
    return ss.split("\0")[0]

class dipc_interface(object):
    def __init__(self):
        self._base = DipcNew()
    def init(self, logic_name, work_dir):
        return DipcInit(self._base, logic_name, work_dir)
    def add_concerned_endpoint(self, endpoint):
        return DipcAddConcernEndPoint(self._base, endpoint)
    def remove_concerned_endpoint(self, endpoint):
        return DipcRemoveConcernEndPoint(self._base, endpoint)
    def get_concerned_endpoint_status(self, endpoint):
        return DipcGetConcernEndPointStatus(self._base, endpoint)
    def send_msg(self, msg_type, dest, data_to_send, send_to_bak = True):
        return DipcMsgSend(self._base, msg_type, dest, send_to_bak, data_to_send, len(data_to_send))
    def recv_msg(self):
        return DipcMsgRecv(self._base)
    def get_backup_endpoint(self, primary_endpoint_name):
        return DipcGetBackupEndPoint(self._base, primary_endpoint_name)
    def is_local_logicname(self, primary_endpoint_name):
        return DipcIsLocalLogicalName(self._base,endpoint)
    def is_in_service(self):
        return DipcIsInService(self._base)
    def close(self):
        return DipcClose(self._base)
    def queue_depth(self):
        return DipcRecvQueueDepth(self._base)

class logger(object):
    def __init__(self):
        self._base = LogNew()
    def init(self, path, prog, instance):
        return LogInit(self._base, path, prog, instance)
    def write_log(self, level, code, msg):
        return LogWrite(self._base, level, code, msg)
    def db(self, msg):
        return LogDbMsg(self._base, msg)
    #def log_info(self, msg):
    #    return LogWrite(self._base, INFO, SUCCESS, msg)
    #def log_debug(self, msg):
    #    return LogWrite(self._base, DEBUG, SUCCESS, msg)
    def set_debug(self, flag=True):
        return LogDebug(self._base, flag)
    def set_cout(self, flag=True):
        return LogCout(self._base, flag)

class sim_ipc_itf2(object):
    def __init__(self):
        self._base = SimIpcNew(2)
    def add_connection(self, hostname, port):
        return SimIpcAddConnection(self._base, hostname, port)
    def start(self):
        return SimIpcStart(self._base)
    def stop(self):
        return SimIpcStop(self._base)
    def send_itf2_res(self, connection_id, logicname, session_id, result_code):
        return SimIpcSendItf2Res(self._base, connection_id, logicname, session_id, result_code)
    def recv_itf2_req(self):
        return SimIpcRecvItf2Req(self._base)

class timer(object):
    ''' the timer wrapper, the id is encode to hex string, and decode back
        to adapt for some Python string with '\0' that in C++ will get exception'''
    def __init__(self):
        self._base = ConstructTimer()
    def __del__(self):
        DeconstructTimer(self._base)
    def activate(self, id, timer_type=0, expire=1, event_type=0):
        #convert to hex string, to avoid '\0'
        return ActivateTimer(self._base, id.encode('hex'), timer_type, expire, event_type) 
    def deactivate(self, id, timer_type=0):
        #convert to hex string, to avoid '\0'
        return DeactivateTimer(self._base, id.encode('hex'), timer_type)
    def delete(self, id):
        #convert to hex string, to avoid '\0'
        return DeleteTimer(self._base, id.encode('hex'))
    def get_event(self):
        e = GetTimerEvent(self._base)
        if e:
            e['id'] = e['id'].decode('hex') #encode the id back
        return e         



if __name__=="__main__":
    #log = logger()
    #ret=log.init("./test.log", "LaLaLa", "DoDoDo")
    #log.set_debug(True)
    #log.set_cout(True)
    #print "Init result:%d"%ret
    #print locals
    #log.write_log(DEBUG, DIPC_SUCCESS, "hello logger") 
    #log.write_log(INFO, DIPC_SUCCESS, "hello logger") 
    #log.write_log(WARNING, DIPC_SUCCESS, "hello logger") 
    #log.write_log(ERROR, DIPC_SUCCESS, "hello logger") 

    #dipc = dipc_interface()
    #dipc.init("dup_checker", "/ocg/work/")
    #print "Backup Endpoint [%s]"%dipc.get_backup_endpoint("RHEL6U4.dup_checker")
    ##dipc.add_concerned_endpoint("ps-ocg1.dup_checker")
    ##print dipc.get_concerned_endpoint_status("ps-ocg1.dup_checker")
    ##dipc.send_msg(0, 1024, "ps-ocg1.dup_checker", "Hello")

    import time
    tm = timer()
    print "%f"%time.time()
    tm.activate(id="abcd", timer_type=1, expire=2, event_type=10)
    tm.activate(id="\0\0abcd\0\0", timer_type=1, expire=2, event_type=10)
    tm.activate(id="efgh", timer_type=1, expire=5, event_type=10)
    tm.activate("ddfsd", timer_type=1, expire = 10, event_type=30)
    while True:
        x = tm.get_event()
        if x == None:
            #print "XXXX"
            time.sleep(0.01)
            continue
        print "%f"%time.time()
        print x
        if x['ev'] == 30:
            break;
        elif x['ev'] == 10:
            tm.delete(x['id'])
            tm.deactivate("efgh", timer_type=1)
        else:
            continue
