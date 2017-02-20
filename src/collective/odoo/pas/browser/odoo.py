import sys, traceback
import logging
import zope.interface
from zope.interface import implements
import zope.component
import xmlrpclib
import zope.schema.interfaces
from zope import component, schema, interface
from zope.component import getMultiAdapter
from zope.schema import getFieldsInOrder, getFieldNames
from zope.schema.interfaces import IList
from zope.schema.fieldproperty import FieldProperty
from z3c.form.object import SubformAdapter, makeDummyObject
from z3c.form.interfaces import INPUT_MODE, DISPLAY_MODE, IFormLayer
from z3c.form.widget import FieldWidget
from z3c.form import form, field, button, subform, datamanager
from z3c.form.i18n import MessageFactory as _z3c
from plone.dexterity.browser import add
from plone.memoize.view import memoize
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import normalizeString, safe_unicode, utf8_portal, getSiteEncoding
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneLocalesMessageFactory as PLMF
from zope.component.hooks import getSite
from zope.i18nmessageid import MessageFactory
from Products.Five.browser import BrowserView
from plone.autoform.form import AutoExtensibleForm

_p = MessageFactory('plone')
_z3cf = MessageFactory('z3c.form')
from urllib2 import Request, urlopen, URLError
import urllib, urllib2
import time
from urllib import urlencode
import cookielib
from urlparse import urlparse
from oerplib.rpc.jsonrpclib import Proxy
from oerplib import OERP
from cookielib import Cookie, CookieJar
try:
    import json
except:
    import simplejson as json

from collective.odoo.pas import interfaces, _

LOG = logging.getLogger(__name__)

class OdooProxy(Proxy):

    def __init__(self, host, port, timeout=120, ssl=False, deserialize=True, cookie=None):
        super(OdooProxy, self).__init__(host, port, timeout=timeout, ssl=ssl, deserialize=deserialize)
        self.cookie_jar = cookielib.CookieJar()
        if cookie:
            self.cookie_jar.set_cookie(cookie)
        self._opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookie_jar))


class OdooState(BrowserView):

    implements(interfaces.IOdooState)

    def __init__(self, context, request):
        super(OdooState, self).__init__(context, request)
        self.conn = getUtility(interfaces.IOdooPasUtility)
        self.proxy = self.conn.getProxy(request)
        lid = self.request.locale.id
        self.locale = lid.language
        if lid.territory:
            self.locale += '_'+lid.territory

