import logging
import sys
from Products.CMFCore.utils import getToolByName
from zope.i18nmessageid import MessageFactory
_p = MessageFactory('plone')
_z3cf = MessageFactory('z3c.form')
from collective.odoo.pas import _
from zope.component.hooks import getSite
from z3c.form import form, field, button, subform
from plone.z3cform.layout import wrap_form
from plone.autoform.form import AutoExtensibleForm
from Products.Five.browser import BrowserView
from collective.odoo.pas import interfaces
from oerplib import OERP, error
LOG = logging.getLogger(__name__)
        
class Overview(BrowserView):

    def __call__( self ):
        self.settings = interfaces.IOdooPasSettings( self.context )
        return super( Overview, self).__call__()
    
    def __init__(self, context, request): 
        self.context = getToolByName(context, 'portal_url').getPortalObject()
        self.request = request

    def getVersion( self ):
        qi = getToolByName(self.context, 'portal_quickinstaller')
        return qi.getProductVersion('collective.odoo.pas')


class OdooPasSettings(AutoExtensibleForm, form.EditForm):
    schema = interfaces.IOdooPasSettings
        
    def getContent(self):
        return getSite()

    @button.buttonAndHandler(_p('label_apply_changes'), name='apply')
    def handleApply(self, action):
        super(OdooPasSettings, self).handleApply(self, action)

    @button.buttonAndHandler(_p('label_cancel'), name='cancel')
    def handleCancel(self, action):
        return self.request.response.redirect(self.context.absolute_url()+'/@@manage-odoo-overview')

    def update(self):
        super(OdooPasSettings, self).update()
        try:
            config = interfaces.IOdooPasSettings(self.getContent())
            conn = OERP(server=config.http_host, database=config.dbname, port=config.http_address)
            main_user = conn.login(user=config.username, passwd=config.password)
            self.status = _('Connection done! Your Odoo version is: ${version}. Authentication established.', mapping={'version':conn.version})
        except:
            "Unexpected error:", sys.exc_info()[0]
            self.status = _('Unable to connect to your openerp data base: ${error}', mapping={'error':sys.exc_info()[0]})
            pass

