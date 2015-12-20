import time
from greenlet import greenlet
'''Filename: Smart chocker greenlet to detect system load and let 
    instanse to sleep to lower the CPU usage'''

class Chocker(greenlet):
    def __init__(self, rest_time=0.01, rest_threshold=1000):
        self.rest_time = rest_time
        self.rest_threshold = rest_threshold
        self.idle_status = True

    def run(self):
        consecutive_idle_count = 0
        while True:
            # increase the consecutive idle counter, or clear it
            if self.idle_status:
                consecutive_idle_count += 1
            else:
                consecutive_idle_count = 0
            #if idle count exceed the threshold, take a rest
            if consecutive_idle_count>=self.rest_threshold:
                #print 'chock'
                time.sleep(self.rest_time)
            #pass CPU back to parent
            self.parent.switch()

    def idle_switch(self, idle_status):
        self.idle_status = idle_status
        self.switch()
