# installation of Acoss  sso skins

import os
from App.Extensions import getPath
from App.Common import package_home
from Products.CMFCore.utils import minimalpath
import Products.Presence
import sys
from Products.CMFCore.TypesTool import ContentFactoryMetadata
from Products.CMFCore.utils import getToolByName
from Products.Presence.JPresenceBox import addJPresenceBox

acosssso_globals=globals()

from re import match
from zLOG import LOG, INFO, DEBUG

def install(self):

    _log = []
    def pr(bla, zlog=1, _log=_log):
        if bla == 'flush':
            return '\n'.join(_log)
        _log.append(bla)
        if (bla and zlog):
            LOG('jabber presence skin install:', INFO, bla)

    def prok(pr=pr):
        pr(" Already correctly installed")

    pr("Starting Jabber Presence Skins install")

    portal = self.portal_url.getPortalObject()

    def portalhas(id, portal=portal):
        return id in portal.objectIds()


    # all skins installation
    pr("Installing skins")
    skins = ('jabber_presence',)
    paths = {
        'jabber_presence': 'skins',
    }
    for skin in skins:
        path = paths[skin]
        path = path.replace('/', os.sep)
        pr(" FS Directory View '%s'" % skin)
        if skin in portal.portal_skins.objectIds():
            dv = portal.portal_skins[skin]
            oldpath = dv.getDirPath()
            if oldpath == path:
                prok()
            else:
                pr("  Correctly installed, correcting path")
                dv.manage_properties(dirpath=path)
        else:
            # XXX: Hack around a CMFCore/DirectoryView bug (?)                        
            BasePath=Products.Presence.__file__.split(os.sep)[:-1]
            BasePath=os.sep.join(BasePath)
            path=os.sep.join((BasePath,path))
            pr("Path=%s" % path)
        
            path = minimalpath(path)

            portal.portal_skins.manage_addProduct['CMFCore'].manage_addDirectoryView(filepath=path, id=skin)
            pr("  Creating skin")

    allskins = portal.portal_skins.getSkinPaths()
    for skin_name, skin_path in allskins:
        if skin_name != 'Basic':
            continue
        path = [x.strip() for x in skin_path.split(',')]
        path = [x for x in path if x not in skins] # strip all
        if path and path[0] == 'custom':
            path = path[:1] + list(skins) + path[1:]
        else:
            path = list(skins) + path
        npath = ', '.join(path)
        portal.portal_skins.addSkinSelection(skin_name, npath)
        pr(" Fixup of skin %s" % skin_name)
    pr(" Resetting skin cache")
    portal._v_skindata = None
    portal.setupCurrentSkin()
    
    pr("End of Jabber Presence Skins install")
        
    ############################################################
    # types installation
    typesTool = getToolByName(self, 'portal_types')
    # Former types deletion
    fti=Products.Presence.fti[0]
    if fti['id'] in typesTool.objectIds():
        pr('*** Object "%s" already existed in the types tool => deleting' % fti['id'])        
        typesTool._delObject(fti['id'])

    # Type re-creation    
    cfm = apply(ContentFactoryMetadata, (), fti)
    typesTool._setObject(fti['id'], cfm)
    pr('Type "%s" registered with the types tool' % fti['id'])


    ##############################################################
    # Create Root Boxe !!!
    pr('Setting up app list box')
    portal=self.portal_url.getPortalObject()
    RootBoxContainer=getattr(portal,'.cps_boxes_root')
    NewBoxId='jpresence'
    
    if NewBoxId in RootBoxContainer.objectIds():
        pr("Box allready present")
    else:
        addJPresenceBox(RootBoxContainer,NewBoxId)
        MyBox = getattr(RootBoxContainer,NewBoxId)
        MyBox.slot='right'
        MyBox.display='default'
        MyBox.box_skin='here/box_lib/macros/sbox'
        MyBox.title='Jabber Presence'
        MyBox.provider='jpresence'
        pr("new box created")
     
    return pr('flush')
