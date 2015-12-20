#!/bin/env python
import redis
from cdr_writer import CdrWriter

class RedisQueue(object):
    '''Wrapper class of a redis list to be a message queue'''
    def __init__(self, redis_pool, queue_name):
        '''Initialization. 
        parameter:
            redis_pool: pass in a redis_pool to use
            queue_name: the name of the redis list to be used as a queue'''
        self.rp = redis_pool
        self.r = redis.Redis(connection_pool=self.rp)
        self.queue_name = queue_name

    def enqueue(self, msg):
        '''Enqueue a msg to queue tail.
        parameter:
            msg: the msg string'''
        return self.r.lpush(self.queue_name, msg)

    def dequeue(self):
        '''Dequeue a msg from queue head
            no parameter, return None if the queue is empty'''
        return self.r.rpop(self.queue_name)

    def dequeue_n(self, n):
        '''To dequene N msgs from queue head in a batch,
        parameter:
            n: The number of msgs you expected to retrieve from queue
        return:
            a list of msgs with n elements will be returned, if there is less than n msg in the queue, None will be filled in place'''
        if n<1:
            return None
        p = self.r.pipeline()
        p.multi()
        for i in xrange(0, n):
            p.rpop(self.queue_name)
        return p.execute()

    def get_queue_depth(self):
        '''Return the depth of the queue'''
        return self.r.llen(self.queue_name)

class AcctSessionEventQueue(RedisQueue):
    '''The PROTAL_ACCT_SESSION_EVENT list in redis, which is used as a queue for RS to notify account session event to CP'''
    def __init__(self, redis_pool):
        super(AcctSessionEventQueue, self).__init__(redis_pool, "PROTAL_ACCT_SESSION_EVENT")

    def notify(self, event_msg):
        '''RS will call this to enqueue a account session event
        parameter:
            event_msg: the account session event string'''
        self.r.lpush(self.queue_name, event_msg)
    

class DisconnectQueue(RedisQueue):
    '''The DISCONN_QUEUE list in redis'''
    def __init__(self, redis_pool):
        super(DisconnectQueue, self).__init__(redis_pool, "DISCONN_QUEUE") 

    def disconnect(self, username, mac):
        '''enqueue a disconnect request to the queue
        parameter:
            username: the username of the session to disconnect
            mac: the calling-station-id of the session to disconnnect'''
        self.enqueue("%s$%s"%(mac, username))

    def get_request(self):
        '''try to poll 20 request from queue at once, returns a 20 element list'''
        return self.dequeue_n(20) 


class AcctSession(object):
    '''Wrapper of SESSION_[username] hash in redis'''
    def __init__(self, redis_pool):
        self.rp = redis_pool
        self.r = redis.Redis(connection_pool=self.rp)
        self.prefix = "SESSION_"

    def save_session(self, username, mac, nas_ip, nas_port, ss, session_id, multi_session_id):
        '''To save a session information with key SESSION_[username]
        parameter:
            username: username of the session
            mac: calling-station-id of the session
            nas_ip: the NAS that holds this session
            nas_port: the disconnection port of the NAS
            ss: secret of the NAS
            session_id: session id of the session
            multi_session_id: multi_session_id of the session'''
        self.r.hset(self.prefix+username, mac, "%s$%s$%d$%s$%s$%s"%(CdrWriter.get_timestamp(), nas_ip, nas_port, ss, session_id, multi_session_id))
        return True

    def find_sessions_by_username(self, username):
        '''find sessions' MAC by username
        parameter:
            username: username to find sessions
        return:
            return a list of MACs of sessions'''
        return self.r.hkeys(self.prefix+username)

    def find_session_by_username_mac(self, username, mac):
        '''find session by username and MAC
        paramter:
            username: username to find session
            mac: mac to find session
        return:
            the detailed session information string if found, otherwise, None is returned'''
        s = self.r.hget(self.prefix+username, mac)
        if s:
            return s
        else:
            return None

    def delete_session_by_username_mac(self, username, mac):
        '''delete a session by username + MAC
        parameter:
            username: username to find session
            mac: mac to find session
        return:
            the number of element which is deleted'''
        return self.r.hdel(self.prefix+username, mac)

    def delete_item_by_username(self, username):
        '''delete all session of a username
        parameter:
            username: username to find session
        return:
            the number of element which is deleted'''
        return self.r.delete(username)


class RedisHashBuffer(dict):
    '''a buffer of redis objects, for some Redis information that not changed frequently,
this class will load the information and keep it as dictionary in memory for application to lookup,
reload method is provided to reload from Redis'''
    def __init__(self, redis_pool, prefix):
        self.rp = redis_pool
        self.r = redis.Redis(connection_pool=self.rp)
        self.prefix = prefix

    def reload(self):
        '''Reload the buffer from redis'''
        if self.r.ping():
            self.clear()
            self.load()
            return True
        else:
            return False
            

    def load(self):
        '''Load the buffer from redis'''
        keys = self.r.keys('%s*'%self.prefix)
        l = len(self.prefix)
        for k in keys:
            #print k
            self[k[l:]] = self.r.hgetall(k)

    def save(self):
        '''Save the buffer to redis'''
        r = self.r
        for k in self.keys():
            r.hmset(self.prefix+k, self[k])

    def clear_db(self):
        '''Clear all items with the prefix from redis'''
        self.clear()
        ks = self.r.keys('%s*'%self.prefix)
        if len(ks) > 0:
            self.r.delete(*ks)

    def save_from_dict(self, dd):
        '''Do a clear_db, then save the dict passed in to Redis
        paramter:
            dd: the dictionary to be set to the Redis and the buffer
        '''
        self.clear()
        self.update(dd)
        #print self
        self.save()

class UserProfile(RedisHashBuffer):
    '''The PROFILE_[UserType] RedisHashBuffer'''
    def __init__(self, redis_pool):
        super(UserProfile, self).__init__(redis_pool, "PROFILE_") 
    

class RadiusClient(RedisHashBuffer):
    '''The RADCLI_[UserType] RedisHashBuffer'''
    def __init__(self, redis_pool):
        super(RadiusClient, self).__init__(redis_pool, "RADCLI_") 

class PortalUserInfo(RedisHashBuffer):
    '''The PORTAL__[UserType] RedisHashBuffer, in actual system, this is shall not be buffered, this class just for testing usage'''
    def __init__(self, redis_pool):
        super(PortalUserInfo, self).__init__(redis_pool, "PORTAL_") 

        
            
if __name__=="__main__":
    from global_conf import *
    import redis
    rp = redis.BlockingConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)


    def test_SessionDisconn():
        disconn_q = DisconnectQueue(rp)
        acct_sess = AcctSession(rp)    

        print "Add 3 sessions"
        acct_sess.save_session("paco", "MAC1", "192.168.0.1", 3678, "secret", "S1", "MS1")
        acct_sess.save_session("paco", "MAC2", "192.168.0.1", 3678, "secret", "S2", "MS2")
        acct_sess.save_session("paco", "MAC3", "192.168.0.1", 3678, "secret", "S3", "MS3")
        print "Try to find all sessions, and send disconnect request"
        for i in acct_sess.find_sessions_by_username("paco"):
            print "\tto disconnect [%s] [%s]"%("paco", i) 
            disconn_q.disconnect("paco", i) 
    
        for i in disconn_q.get_request():
            if i == None:
                break
            print "get disconnect request %s"%i
            (mac, username) = i.split("$")
            print "Try to find the disconnecting session and delete"
            print acct_sess.find_session_by_username_mac(username, mac)
            print acct_sess.delete_session_by_username_mac(username, mac)
        
        print "Try to find all sessions of the deleted, there should be not found"
        print acct_sess.find_sessions_by_username("paco")

    def test_ReqDisconn(usr):
        import time
        disconn_q = DisconnectQueue(rp)
        acct_sess = AcctSession(rp)    

        print "Try to find all sessions, and send disconnect request"
        for i in acct_sess.find_sessions_by_username(usr):
            print "\tto disconnect [%s] [%s]"%(usr, i) 
            disconn_q.disconnect(usr, i) 

        while disconn_q.get_queue_depth()>0:
            print "waiting for process ..."
            time.sleep(1) 
        print "Queue empty, all request are processed"

        

    def test_RadiusClient():
        rc = RadiusClient(rp)
        rc.clear_db()

        dd = {
            '127.0.0.1': {
                'SECRET':'abc123',
                'REQ_MESSAGE_AUTHENTICATOR':'N',
                'DISCONN_PORT':3788,
            },
            '192.168.237.133': {
                'SECRET':'abc123',
                'REQ_MESSAGE_AUTHENTICATOR':'Y'
            },
            '192.168.237.131': {
                'SECRET':'abc123',
                'REQ_MESSAGE_AUTHENTICATOR':'N'
            },
            '192.168.237.128': {
                'SECRET':'*#07#',
                'REQ_MESSAGE_AUTHENTICATOR':'Y'
            },
            '192.168.0.2': {
                'SECRET':'ctm',
                'REQ_MESSAGE_AUTHENTICATOR':'Y'
            },
        }

        print dd
        rc.save_from_dict(dd)
        rc.clear()
        rc.load()
        print rc
        print "================================="
    
    def test_UserProfile():
        visitor_profile = {
            "Idle-Timeout":600,                     #600 second idle timeout
            "Session-Timeout":1800,                 #30 min session
            "WISPr-Bandwidth-Max-Up":1024,          #Uplink speed limit
            "WISPr-Bandwidth-Max-Down":4*1024,      #Down speed limit
        }

        prf = {
            'VISITOR':visitor_profile,
        }
        up = UserProfile(rp)
        up.clear_db()
        print prf
        up.save_from_dict(prf)
        up.reload()
        print up
        print "================================="

    def test_PortalUserInfo():
        por = {
            '85267076042': {
                'TYPE':'VISITOR',
                'CODE':'ericsson',
            },
            'paco': {
                'TYPE':'VISITOR',
                'CODE':'ericsson',
            },
            'jason': {
                'TYPE':'VISITOR',
                'CODE':'ericsson',
            },
            'harvey': {
                'TYPE':'VISITOR',
                'CODE':'ericsson',
            },
        }
        pu = PortalUserInfo(rp)
        pu.clear_db()
        print por 
        pu.save_from_dict(por)
        pu.reload()
        print pu
            

    def test_RedisQueue():
        q = RedisQueue(rp, "DISCONN_QUEUE")
        for i in xrange(0, 10):
            q.enqueue(i)

        print q.dequeue()
        print q.dequeue_n(20)
            
             
        
    #test_SessionDisconn()
    test_ReqDisconn("paco")
    #test_RadiusClient()
    #test_PortalUserInfo()
    #test_UserProfile()
