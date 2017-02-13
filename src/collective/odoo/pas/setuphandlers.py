# -*- coding: utf-8 -*-
import logging
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
from zope.component import getSiteManager
from zope.component.hooks import getSite
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

LOG = logging.getLogger(__name__)

@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller"""
        return [
            'collective.odoo.pas:uninstall',
        ]

def post_install(context):
    """Post install script"""
    site = getSite()
    gsm = getSiteManager(site)
    uf = site.acl_users
    
    LOG.debug("\ncollective.odoo.pas Plugin setup")

    plone_pas = uf.manage_addProduct['collective.odoo.pas']
    LOG.info(plone_pas)
    found = uf.objectIds(['OdooPAS plugin'])
    if not found:
        plone_pas.addOdooPASPlugin('odoo_pas', 'OdooPAS plugin')
    activatePluginInterfaces(site, 'odoo_pas')

def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
