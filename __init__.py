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


from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.utils import ContentInit, ToolInit
from Products.CMFCore.CMFCorePermissions import AddPortalContent
from Products.CMFCore import utils as cmfutils

import JPresenceBox
import PresenceTool
import JabberPresenceWidget

registerDirectory('skins', globals())

contentClasses = (JPresenceBox.JPresenceBox,)

tools = (PresenceTool.PresenceTool,)

contentConstructors = (JPresenceBox.addJPresenceBox,PresenceTool.PresenceTool )

fti = (JPresenceBox.factory_type_information +
       ()
       )

def initialize(registrar):

    ContentInit('Presence Portal Boxes',
            content_types = contentClasses,
            permission = AddPortalContent,
            extra_constructors = contentConstructors,
            fti = fti,
            ).initialize(registrar)
    
    cmfutils.ToolInit(
        'Presence Tools',
        tools=tools,
        product_name='Presence',
        icon='tool.gif',
    ).initialize(registrar)
    
    registrar.registerClass(JPresenceBox.JPresenceBox,
                          permission="Add Box Container",
                          constructors=(JPresenceBox.addJPresenceBox,))
