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
# $Id$
# $Author$

from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from Globals import DTMLFile
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from zLOG import LOG, ERROR, DEBUG,INFO
import time
from PresenceCache import getPresenceCacheManager

from Products.CMFCore.utils import UniqueObject,getToolByName
from Products.CMFCore.CMFCorePermissions import View,ManagePortal

from ZJabAwareness import ZJabAwareness


## global dico for storing instance of ZJabAwareness
gJabberAdapters={}

class PresenceTool(UniqueObject, SimpleItem):
    """ Presence Tool using Jabber
    """

    id = 'portal_presence'
    meta_type = 'Presence Tool'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    manage_options = (( {'label':'Jabber Servers Admin Users',
                          'action':'manage_ServerAdmin'}
                       ,
                       {'label':'Presence Cache',
                          'action':'manage_Cache'}
                       ,
                       {'label':'User Jabber Attributes',
                          'action':'manage_JabbAttr'}
                       ,                       
                       )                     
                     )

    ####################################################
    #
    #   ZMI Skins
    #
    security.declareProtected(ManagePortal, 'manage_ServerAdmin')
    manage_ServerAdmin = DTMLFile('zmi/manage_ServerAdmin', globals())

    security.declareProtected(ManagePortal, 'manage_Cache')
    manage_Cache = DTMLFile('zmi/manage_Cache', globals())

    security.declareProtected(ManagePortal, 'manage_JabbAttr')
    manage_JabbAttr = DTMLFile('zmi/manage_JabbAttr', globals())

    manage_main=manage_ServerAdmin
    
    ####################################################
    # ZMI API
    #
    # Server Parameters Management
    # 
    def manage_getServerSettings(self,REQUEST=None):
        """ return Mapping for Server / Admin(Login/password) """
        ServerSettings=getattr(self,"_ServerSettings",{})
        return ServerSettings
    
    def manage_setServer(self,JID,Password,Port):
        """ add or update a Server Setting """
        ServerSettings=self.manage_getServerSettings()
        Server=JID.split('@')[1]
        ServerSettings[Server]={'JID':JID,'Password':Password,'Port':Port}
        
        self._ServerSettings=ServerSettings
    
    def manage_addServer(self,REQUEST=None):        
        """ add a new server setting """
        if REQUEST:
            JID=REQUEST.get('JID',None)
            Password=REQUEST.get('Password',None)
            Port=REQUEST.get('Port',5222)
            if (JID and Password):
                self.manage_setServer(JID,Password,Port)
            return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_ServerAdmin?manage_tabs_message=Parameters_changed.')     

    
    def manage_changeJabbAttr(self,REQUEST=None):
        """ """
        if REQUEST:
            JID=REQUEST.get('JID',None)
            Password=REQUEST.get('Password',None)
            self._JIDAttr=JID
            self._PasswordAttr=Password
            return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_JabbAttr?manage_tabs_message=Parameters_changed.')    
    
    def manage_changeCacheParams(self,REQUEST):
        """ change Cache TimeOut """
        if REQUEST:
            CacheTimeOut=REQUEST.get('TimeOut',None)
            CacheTimeOut=float(CacheTimeOut)
            self._CacheTimeOut=CacheTimeOut
            return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_Cache?manage_tabs_message=Parameters_changed.')        

    def manage_DumpCache(self):
        """ dump the cache """
        SiteId=getToolByName(self,'portal_url').getPortalObject().getId()
        PCM=getPresenceCacheManager(SiteId,self.getCacheTimeOut())        
        return PCM.Presence
    
    def manage_getCacheEntryCount(self):
        """ return numbre of cached entries """
        try:
            return len(self.manage_DumpCache())
        except:
            return 0
    
    def manage_flushCache(self,REQUEST=None):
        """ flush presence cache """
        Pcache=self.manage_DumpCache()
        Pcache.clear()
        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_Cache?manage_tabs_message=Cache flushed.')        
        
    ## Parameters retrieval API :)
    
    def getJIDAttr(self):
        """ """
        return getattr(self,'_JIDAttr','')
    
    def getPasswordAttr(self):
        """ """
        return getattr(self,'_PasswordAttr','')    

    def getCacheTimeOut(self):
        """ """
        TimeOut=getattr(self,'_CacheTimeOut',20)
        return TimeOut

    ####################################################    
    #
    # Presence API
    #     
    
    
    security.declareProtected(View, 'getUserPresence')
    def getUserPresence(self,UID):
        """ return User Presence """

        ## First get the JID 
        JID=self._getJIDFromUID(UID)
        if JID==None:
            #raise Exception,"Can't find JID Attribute"
            return {'Status':None,'ERROR':"No JID Attribute defined for user" ,'Connected':-1}
        elif JID=="":
            #raise Exception,"JID Attribute is Empty"
            return {'Status':None,'ERROR':"JID Attribute is Empty" ,'Connected':-1}
        
        ## Look in Cache
        PrezInfo=self._getUserPresenceFromCache(JID)
        
        if PrezInfo:
            #Add JID
            PrezInfo['JID']=JID
            return PrezInfo
        
        ## Ask Jabber for Presence Info
        PrezInfo=self._getUserPresenceFromJabberServer(JID) 
        
        ## UpdateCache
        self._setUserPresenceToCache(JID,PrezInfo)                
        
        ## Add JID
        PrezInfo['JID']=JID
        return PrezInfo
    
    security.declareProtected(View, 'sendJabberMessage')
    def sendJabberMessage(self,JIDList,Message,subject=None,typ=None):
        """ send a Jabber message to a list of JID """
        
        if type(JIDList)==type(""):
            JIDList=[JIDList,]
        
        # Split list by Jabber Server    
        SplittedJIDList={}
        for JID in JIDList:
            ServerKey=JID.split('@')[1]
            if ServerKey in SplittedJIDList.keys():
                SplittedJIDList[ServerKey].append(JID)
            else:
                SplittedJIDList[ServerKey]=[JID,]
        
        LOG("PresenceTool",DEBUG,"SplittedJIDList=%s" % str(SplittedJIDList))
        
        # get adapter for each Server
        for Server in SplittedJIDList.keys():
            JIDs=SplittedJIDList[Server]
            Adapter=self._getJabberAdapter(JIDs[0])
            if Adapter==None:
                LOG("PresenceTool",ERROR,"Can't find adapter for Server %s" % Server)
                continue
            else:
                # Send message
                Adapter.sendNotification(JIDs,Message,subject,typ)                    

    ####################################################    
    #
    # Private functions
    # 

    def _getJIDFromUID(self,UID):
        """ return a JID given a UID 
            uses CPS Dierctory
        """
        pDir=getToolByName(self,'portal_directories')
        
        # get Member Directory
        mDir=pDir.members
        
        JID_Key=self.getJIDAttr()
        
        try:
            Member=mDir.getEntry(UID)
            JID=Member[self.getJIDAttr()]
        except KeyError:
            JID=None        
        return JID
    
    def _getJabberAdapter(self,JID):
        """ return the ZJabAwareness for one server """
        Adapter=None
        
        # first get Server info
        ServerSettings=self.manage_getServerSettings()
        Server=JID.split('@')[1]
        
        try:
            MyServerSetting=ServerSettings[Server]
        except KeyError:
            return None
        
        # Do Jabber Request
        AdminLogin=MyServerSetting['JID']
        AdminPassword=MyServerSetting['Password']
        ServerPort=MyServerSetting['Port']
                
        if gJabberAdapters.has_key(Server):
            Adapter=gJabberAdapters[Server]
        else:
            LOG("PresenceTool",DEBUG,"Connecting to Jabber Server %s" % Server)
            LOG("PresenceTool",DEBUG," connect params= %s %s %s " % (AdminLogin,AdminPassword,ServerPort))
            Adapter=ZJabAwareness(AdminLogin,AdminPassword,ServerPort)
            try:
                Adapter.connect()    
            except IOError:
                return None

            gJabberAdapters[Server]=Adapter
        
        # ASK adapter to fetch status from Jabber Server
        # only if last refresh time is < CacheTime/2
        if Adapter.RefreshTimeStamp==None or \
           (time.time()-Adapter.RefreshTimeStamp)>int((self.getCacheTimeOut()/2)*60):
            Adapter.refreshStatus()
            
        return Adapter
            
    
    def _getUserPresenceFromJabberServer(self,JID):   
        """ return Presence Info from Jabber Server """
        
        Adapter=self._getJabberAdapter(JID)        
        
        if Adapter==None:
            return {'Status':None,'ERROR':'Jabber Server Unreachable or not configured','Connected':-1}
                    
        try:
            JabStatus=Adapter.getSatusByJID(JID)
        except IOError:
            JabStatus={'Status':None,'ERROR':'Jabber Server Unreachable','Connected':-1}
            
        if JabStatus==None:
            return{'Status':'Not Connected','Connected':0}
        else:
            return{'Status':JabStatus[0],'Connected':1}        
        
        
    def _getUserPresenceFromCache(self,JID):            
        """ return Presence Info if in cache """
        SiteId=getToolByName(self,'portal_url').getPortalObject().getId()
        PCM=getPresenceCacheManager(SiteId,self.getCacheTimeOut())        
        PresenceInfo=PCM[JID]        
        return PresenceInfo

    def _setUserPresenceToCache(self,JID,PrezInfo):            
        """ set Presence Info into cache """
        SiteId=getToolByName(self,'portal_url').getPortalObject().getId()
        PCM=getPresenceCacheManager(SiteId,self.getCacheTimeOut())     
        # Update TimeStamp
        PrezInfo['ModificationTime']=time.time()
        PCM[JID]=PrezInfo        
                    
InitializeClass(PresenceTool)        