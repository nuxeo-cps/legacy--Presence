 # (C) Copyright 2004 Unilog <http://www.unilog.com>
# Author: Thierry Delprat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# Implement Presence Cache Management as Globals Vars
# Implement Garbage collector as a separated thread
#
# $Id$
# $Author$

import thread
import ThreadLock
import time

from AccessControl import ClassSecurityInfo
from AccessControl.SimpleObjectPolicies import allow_type
from zLOG import LOG, ERROR, DEBUG
from thread import start_new_thread

####################################################################""
gRAMPresenceCacheData={}
gPresenceCleanerThreads={}

# global lock
gPresenceCacheLock = ThreadLock.allocate_lock()

def getPresenceCacheManager(SiteKey,TimeOut=20):
    """ Returns the Presence Cache Manager associated to a Site 
        Create it if not allready exists
    """
    gPresenceCacheLock.acquire()
    retVal=None
    try:
        if SiteKey in gRAMPresenceCacheData.keys():
            retVal=gRAMPresenceCacheData[SiteKey]
        else:
            retVal=RAMPresenceManager(TimeOut)
            gRAMPresenceCacheData[SiteKey]=retVal
            
            # Init cleaning thread
            StartTimeOutCleaner(SiteKey)
    finally:
        gPresenceCacheLock.release()
        return retVal


def TimeOutCleaner(SiteKey):
    """ do the cleaning """
    while(1):
        LOG('PresenceTool',DEBUG,'Cache Cleanning for SiteKey=%s ' % SiteKey)
        SM=getPresenceCacheManager(SiteKey)
        sklist=SM.keys()[:]
        for sk in sklist:
            presence=SM[sk]
            if time.time() - presence['ModificationTime'] > (SM.TimeOut*60):
                del SM[sk]
                LOG('PresenceTool',DEBUG,'Presence %s delete' % sk)    
        LOG('PresenceTool',DEBUG,'Presence Cleanning asleep for %d s' % (SM.TimeOut*60))
        time.sleep(SM.TimeOut*60)
    
def StartTimeOutCleaner(SiteKey):
    """ launch a thread to destroy expired presences"""
    thread_id=start_new_thread(TimeOutCleaner,(SiteKey,))
    gPresenceCleanerThreads[SiteKey]=thread_id    


class RAMPresenceManager:
    """ Handles Presence Cache for one site 
        {
        JID1 : PresenceDataDico1,
        JID2 : PresenceDataDico2,
        }
    """
        
    def __init__(self,TimeOut):
        self.TimeOut=TimeOut
        self.Presence={}
        self.PresenceLock=ThreadLock.allocate_lock()        
        
    ###################################
    # Implement Dictionary Interface
    
    def __delitem__(self,key):
        self.PresenceLock.acquire()
        try:
            del self.Presence[key]
        finally:
            self.PresenceLock.release()
        
    def __getitem__(self,key):
        self.PresenceLock.acquire()
        PresenceItem=None
        try:
            if key in self.Presence.keys():
                PresenceItem=self.Presence[key]
            else:
                PresenceItem=None
        finally:
            self.PresenceLock.release()
            return PresenceItem

    def __setitem__(self,key,value):
        self.PresenceLock.acquire()
        try:
            self.Presence[key]=value
        finally:
            self.PresenceLock.release()
       
    def keys(self):
        return self.Presence.keys()
    
    def get(self,key,default_value=None):
        PresenceItem=self.__getitem__(key)
        if PresenceItem==None:
            PresenceItem=default_value
        return PresenceItem
      
    
    def has_key(self,key):
        """ """
        return self.Presence.has_key(key)
    
