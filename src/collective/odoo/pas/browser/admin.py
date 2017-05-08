import logging
import sys
from Products.CMFCore.utils import getToolByName
from zope.i18nmessageid import MessageFactory
_p = MessageFactory('plone')
_z3cf = MessageFactory('z3c.form')
from collective.odoo.pas import _
from zope.component.hooks import getSite
from z3c.form import form, field, button, subform
from plone.z3cform import layout
from plone.autoform.form import AutoExtensibleForm
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile, \
    ZopeTwoPageTemplateFile
from collective.odoo.pas import interfaces
from collective.odoo.pas import _
from oerplib import OERP, error
from zope.event import notify
LOG = logging.getLogger(__name__)
        
class Overview(BrowserView):
    title = _(u'Odoo Settings')

    def __call__( self ):
        self.settings = interfaces.IOdooPasSettings( self.context )
        return super( Overview, self).__call__()
    
    def __init__(self, context, request): 
        self.context = getToolByName(context, 'portal_url').getPortalObject()
        self.request = request

    def getVersion( self ):
        qi = getToolByName(self.context, 'portal_quickinstaller')
        return qi.getProductVersion('collective.odoo.pas')


class OdooPasSettingsZ2(AutoExtensibleForm, form.EditForm):
    schema = interfaces.IOdooPasSettings
    title = _(u'Odoo Settings')
    
    def getContent(self):
        return getSite()

    @button.buttonAndHandler(_p('label_apply_changes'), name='apply')
    def handleApply(self, action):
        super(OdooPasSettingsZ2, self).handleApply(self, action)

    @button.buttonAndHandler(_p('label_cancel'), name='cancel')
    def handleCancel(self, action):
        return self.request.response.redirect(self.context.absolute_url()+'/@@manage-odoo-overview')

    def update(self):
        super(OdooPasSettingsZ2, self).update()
        site = self.getContent()    
        try:
            config = interfaces.IOdooPasSettings(site)
            if getattr(config, 'http_host', None):
                conn = OERP(server=config.http_host, database=config.dbname, port=config.http_address)
                main_user = conn.login(user=config.username, passwd=config.password)
                notify(interfaces.OdooPasSettingsModifiedEvent(site))
                self.status = _('Connection done! Your Odoo version is: ${version}. Authentication established.', mapping={'version':conn.version})
        except:
            "Unexpected error:", sys.exc_info()[0]
            self.status = _('Unable to connect to your openerp data base: ${error}', mapping={'error':sys.exc_info()[0]})
            pass


class OdooPasSettingsWrapper(layout.FormWrapper):
    index = ViewPageTemplateFile("templates/odoo-settings-template.pt")
    
OdooPasSettings = layout.wrap_form(OdooPasSettingsZ2, OdooPasSettingsWrapper)
