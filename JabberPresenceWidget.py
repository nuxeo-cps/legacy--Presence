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

# A Widget that can be used in the common layout to add presence information

from Globals import InitializeClass
from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.BasicWidgets import CPSStringWidget
from Products.CPSSchemas.Widget import CPSWidgetType
from Products.CPSSchemas.WidgetTypesTool import WidgetTypeRegistry
from Products.CMFCore.utils import getToolByName

class CPSJabberWidget(CPSStringWidget):
    """A Jabber widget that indicate presence"""
    meta_type = "CPS Jabber Widget"

    _properties = CPSStringWidget._properties 
    
    field_types = ('CPS String Field',)

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""
        if mode == 'view':
            # get Presence Status    
            # First get Creator
            widget_id = self.getWidgetId()
            err, creator = self._extractValue(datastructure[widget_id])
            if creator:
                presence_tool=getToolByName(self,"portal_presence")
                JabStatus=presence_tool.getUserPresence(creator)
                if JabStatus.has_key('JID'):
                    if JabStatus['Connected']==1:
                        return "<img src=online.gif> <A href='xmpp:%s'>%s</A> (%s)" % (JabStatus['JID'],JabStatus['JID'],JabStatus['Status'])
                    elif JabStatus['Connected']==0:
                        return "<img src=offline.gif> %s (%s)" % (JabStatus['JID'],JabStatus['Status'])
                    else:
                        return ""
                else:
                    return ""
            else:
                return ""
            return JabStatus
        elif mode == 'edit':
            return ""
        raise RuntimeError('unknown mode %s' % mode)

InitializeClass(CPSJabberWidget)

class CPSJabberWidgetType(CPSWidgetType):
    """URL widget type."""
    meta_type = "CPS Jabber Widget Type"
    cls = CPSJabberWidget

InitializeClass(CPSJabberWidgetType)

WidgetTypeRegistry.register(CPSJabberWidgetType)