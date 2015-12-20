#!/usr/bin/env python 
import ConfigParser 
import re

#play a trick, overide defaut section pattern from '[header]' to '%header' to get untified with OCG
ConfigParser.ConfigParser.SECTCRE = re.compile(r'^%(?P<header>.*$)')
 
class ConfigParserEx(ConfigParser.ConfigParser): 
    '''Config file parser class'''
    def __repr__(self): 
        str = '' 
        sections = self.sections() 
        for s in sections: 
            str += "%%%s\n" % s 
            items = self.items(s) 
            for i,j in items: 
                str += "%s=%s\n" % (i,j) 
        return str 
    def verify(self): 
        ''' Verify after read to be overide in specified case''' 
        pass 
    def read(self, filenames): 
        ConfigParser.ConfigParser.read(self, filenames) 
        self.verify() 
    def readfp(self, fp, filename=None): 
        ConfigParser.ConfigParser.readfp(self, fp, filename) 
        self.verify() 
