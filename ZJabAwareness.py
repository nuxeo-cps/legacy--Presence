# (C) Copyright 2004 Unilog <http://www.unilog.com>
# Author: Maxime.yve
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

from xmpp import Client,Message,Iq,NodeProcessed,debug
import threading
import time

class ZJabAwareness:
    #__________________________________________________________________________
    def __init__(self, JID, password,port="5222",ressource='CPS'):
        """ login is the login of a granted user"""
        login,server=JID.split('@')
        self.server=server
        self.login=login
        self.password=password
        self.ressource=ressource
        self.port=int(port)
        self.jclient=Client(server,debug=[])
        self._awarness={}
        self.lock=threading.Lock()
        self.RefreshTimeStamp=None
    
    #__________________________________________________________________________
    def connect(self):
        """connection and binding with granting jabber user"""
        # connect to server
        if not self.jclient.connect(server=(self.server,self.port)):
            raise IOError('Can not connect to server.')
        # authenticate client
        if not self.jclient.auth(self.login,self.password,self.ressource):
            raise IOError('Can not auth with server.')
        self.jclient.RegisterHandler('iq',self._iqHandler)
    
    #__________________________________________________________________________
    def disconnect(self):
        """ warning this method throw always an exception """
        try:
            self.jclient.disconnect()
        except:
            print "raise when trying to disconnect"
    
    #__________________________________________________________________________
    def getSatusByJID(self, jid):
        """return satus if available and None if not"""
        
        
        return self._awarness.get(jid.lower())
    
    #__________________________________________________________________________
    def refreshStatus(self):
        """send request to the jabber server to update awarness dictionary"""
        # ...if connection is brocken - restore it
        if not self.jclient.isConnected():
            self.jclient.reconnectAndReauth()
        self.jclient.send("""<iq type="get" to="%s">
              <query xmlns="jabber:iq:admin">
                <who/>
              </query>
           </iq>"""%self.server)
        self.jclient.Process(1)        
    
    #__________________________________________________________________________
    def sendNotification(self,jids=[],msg="",subject=None,typ=None):
        """ send notification to a list of user"""
        # ...if connection is brocken - restore it
        
        if not self.jclient.isConnected():
            self.jclient.reconnectAndReauth()
        
        for jid in jids:
            self.jclient.send(Message(jid,msg,typ,subject))
            self.jclient.Process(1)
        
    
    #__________________________________________________________________________
    def _browse_sxml_tree(self, sxml_node):
        for sxml_child in sxml_node.getChildren():
            if sxml_child.getName()=="presence":
                self._extractStatus( sxml_child)
            self._browse_sxml_tree(sxml_child)
    
    #__________________________________________________________________________
    def _extractStatus(self,presence_node):
        res = presence_node.getAttr("from").split("/")
        if len(res)==2:
            who,ressource=res
        else:
            who,ressource=res[0],"No ressource"
        
        # see if it exists a more optimized method in simplexml API!!!
        status="Unknown Status, but connected"
        for node in presence_node.getChildren():
            if node.getName()=="status":
                status=node.getData()
                # in jabber protocole : only one satus tag
                # can be present in presence tag
                break
        self._awarness[who.lower()]=(status,ressource)

    #__________________________________________________________________________
    def _iqHandler(self,conn,iq_node):
        self.lock.acquire()
        try:
            self._awarness.clear()
            self._browse_sxml_tree(iq_node)
            self.RefreshTimeStamp=time.time()
        finally:
            self.lock.release()


if __name__=="__main__":
    zaw=ZJabAwareness("max@192.168.2.158","h2h")
    
    zaw.connect()
    zaw.refreshStatus()
    
    print "Satus for toto :",zaw.getSatusByJID("toto@192.168.2.158")
    print "Satus for max :",zaw.getSatusByJID("max@192.168.2.158")
    print "Satus for tiry :",zaw.getSatusByJID("tiry@192.168.2.158")
    print "Satus for tata :",zaw.getSatusByJID("tata@192.168.2.158")
    
    zaw.sendNotification(["tata@192.168.2.158","tiry@192.168.2.158"],"glop")
    print "notifs sent"
    zaw.disconnect()