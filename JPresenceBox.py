# (C) Copyright 2004 Unilog <http://www.unilog.com>
# Author: Maxime Yve
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

"""
  ContentBox
"""
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Acquisition import aq_base,aq_parent
from DateTime import DateTime

from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from AccessControl import getSecurityManager

from Products.CPSDefault.BaseBox import BaseBox

from zLOG import LOG, ERROR, DEBUG,INFO

import time

factory_type_information = (
    {'id': 'Jabber Presence Box',
     'title': 'Presentiel Jabber',
     'description': 'Presence Jabber des utilisateur du workspace',
     'meta_type': 'Jabber Presence Box',
     'icon': 'box.gif',
     'product': 'Presence',
     'factory': 'addJPresenceBox',
     'immediate_view': 'JPresenceBox_edit_form',
     'filter_content_types': 0,
     'actions': ({'id': 'view',
                  'name': 'action_view',
                  'action': 'basebox_view',
                  'permissions': (View,)},
                 {'id': 'edit',
                  'name': 'action_edit',
                  'action': 'JPresenceBox_edit_form',
                  'permissions': (ModifyPortalContent,)},
                 ),
     # additionnal cps stuff
     'cps_is_portalbox': 1,
     },
    )


class JPresenceBox(BaseBox):
    """
    Displays list of application according to LDAP Parameters
    """
    meta_type = 'Jabber Presence Box'
    portal_type = 'Jabber Presence Box'


    security = ClassSecurityInfo()

    _properties = BaseBox._properties + (
        {'id': 'presence_tool', 'type': 'string', 'mode': 'w',
         'label': 'presence tool id'},
             
        {'id': 'persistence_timeout', 'type': 'float', 'mode': 'w',
         'label': 'Persistence timeout (minute)'},
             
        {'id': 'searchingPortalType', 'type': 'list', 'mode': 'w',
         'label': 'Searching Portal Type'},
        )
        

    presence_tool="portal_presence"
    searchingPortalType=['Workspace']
    persistence_timeout="1.0"
    #__________________________________________________________________________
    
    def __init__(self, id, category='jpresencebox',
                    presence_tool=presence_tool,**kw):
        
        BaseBox.__init__(self, id, category=category, **kw)
        self.searchingPortalType=['Workspace']
        self.presence_tool="portal_presence"
        self.persistence_timeout="1.0"

    #__________________________________________________________________________
    security.declarePublic('getAppList')
    
    def getPresenceList(self,obj):
        """Get list of online user"""
        wrksp=self._getWorkspace(obj)
        if hasattr(wrksp,"jpresence_dict"):
            tmp_dict=wrksp.jpresence_dict
            presence_dict={}
            for user_str in tmp_dict.keys():
                status=self.portal_presence.getUserPresence(user_str)
                connected=status["Connected"]
                presence_dict[user_str]={}
                presence_user=presence_dict[user_str]
                
                if connected == 1:
                    presence_user['alt']=status['Status'] + " " + status['JID']
                    presence_user['img']='online.gif'
                    
                elif connected == 0:
                    presence_user['alt']=status['Status'] + " " + status['JID']
                    presence_user['img']='offline.gif'
                    
                elif connected == -1:
                    presence_user['alt']="ERROR :"+status['ERROR']
                    presence_user['img']='jabber_error.gif'
                    
                presence_user['user']=user_str
            return presence_dict
        return {}
    #__________________________________________________________________________
    def setUserNavigation(self, obj, user):
        """ """
        wrksp = self._getWorkspace(obj)
        self._cleanWorkspace(wrksp)
        self._addUserToWorkspace(wrksp,user)
        
    
    #__________________________________________________________________________
    def _cleanWorkspace(self,wspace):
        """ """
        if not hasattr(wspace,"jpresence_dict"):
            return
        user_to_clean=[]
        jpres=wspace.jpresence_dict
        ti=time.time
        for key in jpres:
            if jpres[key] < ti():
                
                user_to_clean.append(key)
        
        for key in user_to_clean:
            try:
                del jpres[key]
            except:
                LOG("_cleanWorkspace",DEBUG,"Probably problem with multi user.")
                pass
        
        if user_to_clean:
            wspace._p_changed=1
    #__________________________________________________________________________
    def _getWorkspace(self, obj):
        """ """
        obj_child=None
        counter=1
        ob = None
        while obj is not obj_child and counter < 20:
            counter += 1
            obj_child=obj
            obj=aq_parent(obj)
            
            if hasattr(obj_child,'getContent'):
                ob = obj_child.getContent()
            else:
                ob = obj_child
            portal_type = getattr(ob,"portal_type",None)
            
            # debug only
            self.searchingPortalType=['Workspace']
            
            if portal_type in self.searchingPortalType:
                break
        return ob
    #__________________________________________________________________________
    def _addUserToWorkspace(self,wspace,user):
        """ """
        # to do clean jpresence list when user is deleted or something else
        if wspace is None:
            return
        
        if not hasattr(wspace,"jpresence_dict"):
            wspace.jpresence_dict={}
        
        wspace.jpresence_dict[str(user)]=time.time() + float(self.persistence_timeout*60)
        wspace._p_changed=1

InitializeClass(JPresenceBox)


def addJPresenceBox(dispatcher, id, REQUEST=None, **kw):
    """Add a LdapAppBrowser Box."""
    ob = JPresenceBox(id, **kw)
    dispatcher._setObject(id, ob)
    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)
