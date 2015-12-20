#!/bin/env python
# coding:utf-8
# This script is a pure python watchdog to monitor programs
# for apgw, mysql_n_omc service, it check the presentation and trigger warning alarm if not.
# for sso_server, it check if localhost is started with mysql_n_omc first, 
#      if yes,
#              it will check the presentation of sso_server, if not present, trigger a warning alarm and try to start it
#      if no, 
#              it will check the presentation of sso_server, if present, kill sso_server in localhost
#
# * * * * * /ocg/bin/sh_caller.sh /ocg/bin/proc_watchdog2.py >> /ocg/log/watchdog.out
#
import os
import re
import time
import sys
import logging
from logging.handlers import RotatingFileHandler


#参数段，可配置
log_path = "/ocg/log"                            #日志文件及afdi文件输出目录
prog_name = "proc_watchdog2"                     #本进程标识名，用于生成日志文件名和afdi文件名，及afdi记录中的label
last_file = "/tmp/___proc_watchdog.laststatus"   #记录上次是否告警状态的文件
oid = ".1.3.6.1.4.1.193.176.3.1.2"               #告警OID
to_stderr = True                                 #是否输出到标准输出
debug = False                                    #是否输出debug level的消息到日志

#监控目标配置段
to_monitor = {
    'apgw':{
        'last_alarm':False,                                                #记录是否已经告警过，避免重复
        'precondition':None,                                               #执行此项检查的前提条件，只有>0时需要执行，否则跳过,None表示无条件执行
        'to_check':'sudo clustat|grep service:apgw|grep started|wc -l',    #检查是否存活的命令，>0为存活，否则为不存活
        'to_start':None,                                                   #启动此项目命令行，None表示不许启动，只需要监控
        'to_stop':None,                                                    #如果precondition不满足，且to_check结果为运行中，执行此命令停止
        'alarm_msg':'RHCS service apgw is not in status of started'},      #告警信息，用于发出的告警中有意义信息的提示
    'mysql_n_omc':{
        'last_alarm':False, 
        'precondition':None, 
        'to_check':'sudo clustat|grep service:mysql_n_omc|grep started|wc -l', 
        'to_start':None, 
        'to_stop':None,
        'alarm_msg':'RHCS service mysql_n_omc is not in status of started'},
    'sso_server':{
        'last_alarm':False, 
        'precondition':'sudo clustat|grep service:mysql_n_omc|grep started|grep $LOCAL|wc -l', 
        'to_check':'ps -ef|grep sso_server.py|grep SSO_SVR|grep sso_server.conf|grep -v grep|grep -v vi|grep -v more|wc -l', 
        'to_stop':"ps -ef|grep sso_server.py|grep SSO_SVR|grep sso_server.conf|grep -v grep|grep -v vi|grep -v more|awk '{printf(\"kill %d\\n\", $2)}'|sh",
        'to_start':"python /ocg/bin/sso_server.py -conf /ocg/config/sso_server.conf -ln SSO_SVR &", 
        'alarm_msg':'sso_server is not running'},
}

class WarningFile:
    '''用于写告警日志'''
    def __init__(self, path, label):
        '''path输出路径, label本进程标识'''
        self.label = label
        self.hostname = (os.popen('hostname').readline()).strip()
        self.path = path
        self.rec = list()

    def WriteWarnning(self, oid, msg):
        self.rec.append("%s|%s|ERROR|%s|%s"%(time.strftime("%Y%m%d%H%M%S"), self.label, oid, msg))

    def WriteClean(self, oid, msg):
        self.rec.append("%s|%s|CLEAN|%s|%s"%(time.strftime("%Y%m%d%H%M%S"), self.label, oid, msg))

    def Flush(self):
        if len(self.rec) <= 0:
            return 0
        else:
            filename = "%s-%s-WARNING-%s.txt"%(self.hostname, self.label, time.strftime("%Y%m%d%H%M%S"))
            filepath = os.path.join(self.path, filename)
            tmpfile = "."+filename
            tmppath = os.path.join(self.path, tmpfile)
            f = open(tmppath, "w")
            f.write('\n'.join(self.rec))
            f.close()
            os.system("mv %s %s"%(tmppath, filepath))
            self.rec = list()

class LastStatus:
    '''用于记录上次告警状态的文件'''
    def __init__(self, filename):
        self.status_file = filename
    def ReadStatus(self):
        try:
            if int(open(self.status_file, "r").readline()) == 0:
                return False
            else:
                return True

        except:
            return False
    def WriteStatus(self, status):
        try:
            if status:
                open(self.status_file, "w").write("1")
            else:
                open(self.status_file, "w").write("0")
        except:
            pass

#检查是否只有自己一个进程在运行,如果不是，则退出自己
def SingletonAssure():
    cmd = "ps -ef|grep %s|grep -v grep|grep -v vi|grep -v more|grep -v \"/bin/*sh\"|wc -l"%(os.path.basename(__file__))
    print cmd
    if int(get_str_from_cmd(cmd))>1:
        print "I am not singleton, kill myself"
        sys.exit(0)

def get_str_from_cmd(cmd):
    #从命令行获取结果
    p = os.popen(cmd)
    strip = p.readline().strip()
    p.close()
    return strip

def fork_daemon(cmdline):
    pid = os.fork()
    if (pid == 0):
        os.chdir('/home/ocg')
        os.setsid()
        os.umask(0)
        os.system(cmdline)
        sys.exit(0)
    else:
        return pid

def Check(name):
    log.info("check proc [%s]"%name)
    monitor = to_monitor[name]
    #check precondition
    if monitor['precondition'] is not None:
        pre = monitor['precondition'].replace('$LOCAL', GetLocalHost())
        log.debug("check preconditon with [%s] = [%d]"%(monitor['precondition'], int(get_str_from_cmd(pre))))
        if int(get_str_from_cmd(pre)) < 1:
            monitor['last_alarm'] = False
            #如果前置条件不满足,检查是否程序还在跑，如果是话stop掉
            if (monitor['to_check'] is not None) and (monitor['to_stop'] is not None):
                log.debug("check proc stat with [%s] = [%d]"%(monitor['to_check'], int(get_str_from_cmd(monitor['to_check']))))
                if int(get_str_from_cmd(monitor['to_check'])) >= 1:
                    log.debug("precondition not fulfilled but to_check ok, stop it")
                    fork_daemon(monitor['to_stop'])
                else:
                    log.warning("precondition not fulfilled and check not running, no need further check")
            return
    #前置条件满足了，检查是否程序在运行，不在则告警
    if monitor['to_check'] is not None:
        log.debug("check proc stat with [%s] = [%d]"%(monitor['to_check'], int(get_str_from_cmd(monitor['to_check']))))
        if int(get_str_from_cmd(monitor['to_check'])) < 1:
            if not monitor['last_alarm']:
                log.error(monitor['alarm_msg'])
                warning_file.WriteWarnning(oid, monitor['alarm_msg'])
                monitor['last_alarm'] = True
        else:
            log.debug("check ok")
            monitor['last_alarm'] = False
    #根据是否需要运行程序，调用to_start 
    if monitor['last_alarm'] and monitor['to_start'] is not None:
        log.info("run [%s] to restart"%monitor['to_start'])
        fork_daemon(monitor['to_start'])
    
    return monitor['last_alarm']

def GetLocalHost():
    r1 = re.compile('^\s*(.*?)\s+\d+\s+(Online.*?)\s*$')
    for i in os.popen("sudo /usr/sbin/clustat").readlines():
        m = r1.match(i)
        if m:
            l = m.groups()
            hostname = l[0]
            status = l[1]
            if (status.find('Local')>=0):
                return hostname
    return "***********NOT_FOUND_LOCAL_HOST*********"


def Init():
    global log, warning_file, last
    log = logging.getLogger()
    warning_file = WarningFile(log_path, prog_name)
    file_handler = RotatingFileHandler(os.path.join(log_path, prog_name+".log"), maxBytes=1024*1024*10, backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(process)-8d %(message)s')
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    if to_stderr:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        log.addHandler(stream_handler)
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    last = LastStatus(last_file)


############### main process ##########################
SingletonAssure()

Init()
log.info("=========== init ok ===========")

while True:
    log.info("wake up to check items") 
    alarm_flag = False
    for item in to_monitor.iterkeys():
        alarm_flag = Check(item) or alarm_flag
    laststatus = last.ReadStatus()
    if not alarm_flag:
        if laststatus:
            #所有满足前置条件的进程都正常，且目前处于告警状态，则发CLEAN, 并更新告警状态
            log.info("All proc need to watch are all healthy")
            warning_file.WriteClean(oid, "All proc need to watch are all healthy")
            last.WriteStatus(False)
        else:
            log.info("All proc need to watch are all healthy")
    elif alarm_flag and not laststatus:
        #发现从非告警状态变为告警状态，更新到状态文件
        last.WriteStatus(True)
    warning_file.Flush()
    time.sleep(10)
