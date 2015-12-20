#!/bin/env python
import syslog
import sys
import os
import time

#the path of redis-server
REDIS_SRV = '/usr/local/bin/redis-server'
#the path of redis-cli
REDIS_CLI = '/usr/local/bin/redis-cli'
#the redis config file
REDIS_CONFIG='/etc/redis.conf'
#the pid file for redis
REDIS_PID = '/var/run/redis.pid'
#the vip managed via keepalived
VIP='139.122.10.149'
#the redis port
PORT=6379
#the authen for both redis nodes, they should be the same, set to None if no requireauth configured
AUTH='ericsson'

if len(sys.argv) < 2 or sys.argv[1] not in ('start', 'stop', 'restart', 'status', 'master', 'slave'):
    print "redis-server related command"    
    print "Usage: redis-control.py <start|stop|restart>"
    print "redis-cli related command"
    print "Usage: redis-control.py <status|master|slave>"
    sys.exit(-1)
action = sys.argv[1]

def get_str_from_cmd(cmd):
    p = os.popen(cmd)
    strip = p.readline().strip()
    p.close()
    return strip
        
def check_redis_server():
    if (os.path.isfile(REDIS_PID)):
        cmd = 'ps -ef|grep `cat %s`|grep redis-server|grep -v grep|wc -l'%REDIS_PID
        #print cmd
        i = int(get_str_from_cmd(cmd))
        #print i
        if (i==1):
            return True
        else:
            return False
    else:
        return False

def do_start():
    cmd = '%s %s>/dev/null 2>&1;echo $?'%(REDIS_SRV, REDIS_CONFIG)
    #print cmd
    i = int(get_str_from_cmd(cmd))
    time.sleep(0.5)
    if check_redis_server():
        syslog.syslog("Redis started, pid [%s]"%get_str_from_cmd('cat %s'%REDIS_PID))
    else:
        syslog.syslog("Redis start failed")
        sys.exit(1)
    
def do_stop():
    cmd = "killall %s"%REDIS_SRV
    get_str_from_cmd(cmd)
    time.sleep(0.3)
    if check_redis_server():
        time.sleep(1)
        if check_redis_server():
            cmd = "killall -9 %s"%REDIS_SRV
            time.sleep(0.5)
            if check_redis_server():
                syslog.syslog("Failed to stop Redis")
                sys.exit(1)
    syslog.syslog("Redis stopped")
    
def check_vip():
    cmd = 'ip addr|grep %s|grep -v grep|wc -l'%VIP
    #print cmd
    i = int(get_str_from_cmd(cmd))
    #print i
    return i>0

if __name__=='__main__':
    syslog.openlog("redis-control.py", syslog.LOG_PID|syslog.LOG_PERROR)
    if action == 'start':
        if check_redis_server():
            syslog.syslog("Redis already started, pid[%s]"%get_str_from_cmd('cat %s'%REDIS_PID))
            sys.exit(0)
        else:
            do_start()
            sys.exit(0)
    elif action == 'stop':
        if check_redis_server():
            do_stop()
            sys.exit(0)
        else:
            syslog.syslog("Redis not running")
            sys.exit(0)
    elif action == 'restart':
        do_stop()
        do_start()
        sys.exit(0)
    elif action == 'status':
        if check_redis_server():
            cmd = REDIS_CLI+" -h localhost -p %d "%PORT
            if AUTH != None:
                cmd += " -a "+AUTH
            cmd += " INFO"
            p = os.popen(cmd)
            for i in p.readlines():
                print(i.strip())
            p.close()
            sys.exit(0)
        else:
            syslog.syslog("Redis is not running in localhost")
            sys.exit(1)
    elif action == 'master':
        if check_redis_server():
            cmd = REDIS_CLI+" -h localhost -p %d "%PORT
            if AUTH != None:
                cmd += " -a "+AUTH
            cmd += " SLAVEOF NO ONE"
            p = os.popen(cmd)
            syslog.syslog("Try to set local Redis to Master ...")
            for i in p.readlines():
                syslog.syslog(i.strip())
            p.close()
            sys.exit(0)
        else:
            "Redis is not running in localhost, cannot set to master"
            sys.exit(1)
    elif action == 'slave':
        if check_vip():
            syslog.syslog("Localhos has the VIP: %s, local Redis cannot be slave"%VIP)
            sys.exit(1)
        if check_redis_server():
            cmd = REDIS_CLI+" -h localhost -p %d "%PORT
            if AUTH != None:
                cmd += " -a "+AUTH
            cmd += " SLAVEOF %s %d"%(VIP, PORT)
            p = os.popen(cmd)
            syslog.syslog("Try to set local Redis to Master ...")
            for i in p.readlines():
                syslog.syslog(i.strip())
            p.close()
            sys.exit(0)
        else:
            syslog.syslog("Redis is not running in localhost, cannot set to slave")
            sys.exit(1)
