# -*- coding: utf-8 -*-
import logging
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
from zope.component import getSiteManager
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
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

    odoo_pas = uf.manage_addProduct['collective.odoo.pas']
    found = uf.objectIds(['OdooPAS plugin'])
    if not found:
        odoo_pas.addOdooPASPlugin('odoo_pas', 'OdooPAS plugin')
    activatePluginInterfaces(site, 'odoo_pas')
    try:
        site.acl_users.odoo_pas.ZCacheable_setManagerId('RAMCache')
    except:
        LOG.info('unable to set RAMCache as default cache for Odoo PAS')
        pass

def uninstall(context):
    """Uninstall script"""
    site = getSite()
    if IAnnotations(site).get('collective.odoo.pas.adapters.OdooPasSettingsAdapter'):
        del IAnnotations(site)['collective.odoo.pas.adapters.OdooPasSettingsAdapter']
    uf = site.acl_users
    uf.manage_delObjects(['odoo_pas'])
    plone_pas = uf.manage_addProduct['collective.odoo.pas']
