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

##parameters=category=None
# $Id$
"""Return  available box types."""

items = [
    {'category': 'ldapcontentbox',
     'title': 'Boite LDAP des applications',
     'desc': 'Liste des applications depuis le LDAP',
     'types': [{'provider': 'ACOSSSSO',
                'id': 'default',
                'desc': 'Listage des applications autorisées'},
               ]
     },
    ]

if category:
    for item in items:
        if item['category'] == category:
            return item

return items
 