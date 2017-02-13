import logging
from Products.CMFCore.utils import getToolByName
from zope.component import getAllUtilitiesRegisteredFor, getUtility, getGlobalSiteManager
from zope.interface import implementer
from urllib2 import Request, urlopen, URLError
import urllib, urllib2
import time
from urllib import urlencode
import cookielib
from urlparse import urlparse
from oerplib.rpc.jsonrpclib import Proxy
from oerplib import OERP, error
from cookielib import Cookie, CookieJar
import interfaces
LOG = logging.getLogger(__name__)

class OdooProxy(Proxy):

    def __init__(self, host, port, timeout=120, ssl=False, deserialize=True, cookie=None):
        super(OdooProxy, self).__init__(host, port, timeout=timeout, ssl=ssl, deserialize=deserialize)
        self.cookie_jar = cookielib.CookieJar()
        if cookie:
            self.cookie_jar.set_cookie(cookie)
        self._opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookie_jar))


@implementer(interfaces.IOdooPasUtility)
class OdooPasUtility(OERP):
    name = None
    username = None
    password = None
    http_host = None
    http_address = None
    
    def __init__(self, site):
        config = interfaces.IOdooPasSettings(site)
        self.name = config.name
        self.username = config.username
        self.password = config.password
        self.http_host = config.http_host
        self.http_address = config.http_address
        self.dbname = config.dbname
        super(OdooPasUtility, self).__init__(server=config.http_host, database=config.dbname, protocol='xmlrpc',
                 port=config.http_address)
    
    def login(self, user=None, passwd=None, database=None):
        if not user:
            user=self.username
        if not passwd:
            passwd=self.password
        return super(OdooPasUtility, self).login(user, passwd, database)
        
    def getSessionCookie(self, request=None):
        if not request:
            return None
        session_id = request.cookies.get('session_id')
        if not session_id:
            return None
        cookie = cookielib.Cookie(version=0,
                                  name="session_id",
                                  value=session_id,
                                  port=str(self.http_address),
                                  port_specified=False,
                                  domain=self.http_host,
                                  domain_specified=False,
                                  domain_initial_dot=False,
                                  path='/',
                                  path_specified=True,
                                  secure=False,
                                  expires=None,
                                  discard=True,
                                  comment=None,
                                  comment_url=None,
                                  rest={'HttpOnly': None},
                                  rfc2109=False)
        return cookie

    def getSessionInfo(self, request=None):
        return self.callProxy(url='/web/session/get_shop_session_info', params={})

    def getProxy(self, request=None, response=None):
        cookie = self.getSessionCookie(request)
        if not cookie:
            LOG.info('NO Session cookie found')
            cnt = OdooProxy(host = self.http_host,
                            port = self.http_address)
            session_info = cnt(url='/web/session/get_session_info', params={})
            session_id = session_info['result']['session_id']
            cookie = cnt.cookie_jar._cookies[self.config.http_host]['/']['session_id']
            if request and not response:
                request.RESPONSE.setCookie('session_id', cookie.value.replace('"',''), path='/', expires=cookie.expires)
            if response:
                response.setCookie('session_id', cookie.value.replace('"',''), path='/', expires=cookie.expires)
        else:
            LOG.info('Session cookie found')
        cookie.port = self.http_address
        cookie.domain = self.http_host
        cnt = OdooProxy(host = self.http_host,
                        port = self.http_address,
                        cookie=cookie)
        session_info = cnt(url='/web/session/get_session_info', params={})
        if not session_info.get('db'):
            session_info = cnt(url='/web/session/authenticate', params={'db':self.dbname, 'login':'', 'password':''})
        return cnt

    def callProxy(self, url, params, request=None):
        resp = self.proxy(request)(url=url, params=params)
        if resp.get('error'):
            self.pu.addPortalMessage(_('proxy_message_error', default="There has been an error on the server."), type='error')
            LOG.info('ERROR with URL:'+str(url)+', params:'+str(params)+'->'+str(resp.get('error')))
            return None
        return resp['result']


def registerOdooConnection(site):
    processor = OdooPasUtility(site)
    gsm = getGlobalSiteManager()
    gsm.registerUtility(processor, interfaces.IOdooPasUtility)
    LOG.info('Odoo PAS Utility registered')
    return getUtility(interfaces.IOdooPasUtility)


def initConnections(site, event):
    # this is called on first Plone traverse
    portal_quickinstaller = getToolByName(site, 'portal_quickinstaller')
    if portal_quickinstaller.isProductInstalled('collective.odoo.pas'):
        if not getAllUtilitiesRegisteredFor(interfaces.IOdooPasUtility):
            registerOdooConnection(site)

