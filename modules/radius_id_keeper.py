#!/bin/env python
import random

MAX_ID = 0xff

class RadiusIdKeeper:
    '''to generate/return a radius id in [0, 255] randomly in a predictable time'''
    def __init__(self):
        self.avail_id = list()
        self.used_id = set()
        for i in xrange(0,MAX_ID+1):
            self.avail_id.append(i) 

    def get_id(self):
        try:
            index = random.randrange(0, len(self.avail_id))
            id = self.avail_id.pop(index)
            self.used_id.add(id)
            return id
        except ValueError:
            #print "Len[%d]"%(len(self.avail_id))
            return None

    def return_id(self, id):
        if id<0 or id>MAX_ID:
            #deny invalid return id
            print "DENY return id %d"%id
            return
        try:
            self.used_id.remove(id)
            self.avail_id.append(id)
        except ValueError:
            pass
        except KeyError:
            print "KEYERROR %d"%id
            print self.used_id


if __name__=="__main__":
    id_keeper = RadiusIdKeeper()
    for i in xrange(0, MAX_ID+2):
        id = id_keeper.get_id()
        if id != None:
            print "[%03d] %d"%(i, id) 
        else:
            print "[%03d] No avail id"%i
    for i in xrange(0, MAX_ID+2):
        id_keeper.return_id(i)
    print "--------------------------------------------------"
    for i in xrange(0, MAX_ID+2):
        id = id_keeper.get_id()
        if id != None:
            print "[%03d] %d"%(i, id) 
        else:
            print "[%03d] No avail id"%i
    
        
