import logging
import copy
import traceback
from Acquisition import aq_parent
from AccessControl import ClassSecurityInfo, AuthEncoding
from AccessControl.Permissions import manage_users as ManageUsers
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.PropertiedUser import PropertiedUser
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.plugins import *
from Products.PlonePAS.interfaces.capabilities import IDeleteCapability
from Products.PlonePAS.interfaces.capabilities import IPasswordSetCapability
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from Products.PluggableAuthService.utils import createViewName
from Products.PluggableAuthService.plugins.ZODBUserManager import \
    ZODBUserManager as BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import ILoginPasswordHostExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserFactoryPlugin
from Products.PluggableAuthService.interfaces.plugins import IAnonymousUserFactoryPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from Products.PluggableAuthService.interfaces.plugins import IUpdatePlugin
from Products.PluggableAuthService.interfaces.plugins import IValidationPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserAdderPlugin
from Products.PluggableAuthService.interfaces.plugins import IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IRoleEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin
from Products.PluggableAuthService.interfaces.plugins import INotCompetentPlugin
from Products.PluggableAuthService.interfaces.plugins import IChallengeProtocolChooser
from Products.PluggableAuthService.interfaces.plugins import IRequestTypeSniffer
from Products.PlonePAS.plugins.ufactory import PloneUserFactory, PloneUser
from OFS.Cache import Cacheable
import cookielib
import urllib, urllib2
from App.class_init import InitializeClass
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implements
from collective.odoo.pas import interfaces
from oerplib.rpc.jsonrpclib import Proxy
from oerplib import OERP, error
from urllib import quote, unquote
LOG = logging.getLogger(__name__)

manage_addOdooPASPlugin = PageTemplateFile("../www/odoopasAdd", globals(), 
                __name__="manage_addOdooPASPlugin")

def addOdooPASPlugin(self, id, title='', REQUEST=None):
    """Add OdooPAS plugin to a Pluggable Authentication Service.
    """
    p=OdooPASPlugin(id, title)
    self._setObject(p.getId(), p)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect("%s/manage_workspace"
                "?manage_tabs_message=OdooPAS+plugin+added." %
                self.absolute_url())

_marker = ['INVALID_VALUE']

class OdooPartner(PloneUser):
    """Odoo Partner"""

    
class OdooPASPlugin(BasePlugin, Cacheable):
    """Odoo authentication plugin.
    """

    meta_type = "OdooPAS plugin"
    security = ClassSecurityInfo()
    cookie_name = 'session_id'
    login_path = 'login_form'
    
    implements(IUserManagement, IUserIntrospection, IDeleteCapability, IPasswordSetCapability,
               ILoginPasswordHostExtractionPlugin, IUserAdderPlugin, IUserEnumerationPlugin, IUserFactoryPlugin,
               ICredentialsUpdatePlugin, ICredentialsResetPlugin, IAuthenticationPlugin)

    security.declarePrivate('getPropertiesForUser')
    def getPropertiesForUser(self, user, request=None):
        LOG.info('getPropertiesForUser')
        LOG.info(user)
        return {}

    security.declarePrivate('createUser')
    def createUser(self, user_id, name):
        keywords = {'user_id':user_id, 'name':name}
        view_name = createViewName('enumerateUsers', user_id or name)
        cached_info = self.ZCacheable_get( view_name=view_name
                                         , keywords=keywords
                                         , default=None
                                         )
        if cached_info is not None:
            data = cached_info
            partner = OdooPartner(user_id, name)
            self.ZCacheable_set(data, view_name=view_name, keywords=keywords)
            partner.addPropertysheet( 'odoo', data )
            return partner
        users = []
        conn = getUtility(interfaces.IOdooPasUtility)
        main_user = conn.login()
        args = [('login', '=', user_id)]
        uids = conn.search('res.users', args=args)
        if not uids:
            return None
        datas = conn.read('res.users', uids, fields=['login', 'name', 'email', 'partner_id'])
        data = datas[0]
        if data.get('id'):
            del data['id']
        if data.get('partner_id'):
            data['partner_id'] = data['partner_id'][0]
        data['fullname'] = data['name']
        partner = OdooPartner(user_id, name)
        self.ZCacheable_set(data, view_name=view_name, keywords=keywords)
        partner.addPropertysheet( 'odoo', data )
        return partner

    # IAuthenticationPlugin implementation
    security.declarePrivate( 'authenticateCredentials' )
    def authenticateCredentials(self, credentials):
        if not credentials.get('extractor', None) == 'odoo_pas':
            return None
        if credentials.get('login') and credentials.get('password'):
            conn = getUtility(interfaces.IOdooPasUtility)
            try:
                user = conn.auth(credentials.get('login'), credentials.get('password'))
                if user:
                    return credentials.get('login'),credentials.get('login')
            except:
                return None
        elif credentials.get(self.cookie_name):
            cookie_data = credentials.get(self.cookie_name)
            conn = getUtility(interfaces.IOdooPasUtility)
            session = conn.getSessionInfo(cookie=cookie_data)
            if not session:
                return creds
            elif session.get('username'):
                creds.update(session)
        return None

    # ICredentialsUpdatePlugin implementation
    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, new_password):
        """Override standard updateCredentials method
        """
        conn = getUtility(interfaces.IOdooPasUtility)
        if login and new_password:
            try:
                session = conn.proxyAuthenticate(request, response, login, new_password)
                login = session['username']
            except:
                self.resetCredentials(request, response)

    # IExtractionPlugin implementation
    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ Extract credentials from cookie or 'request'. """
        creds = {}
        cookie_data = request.get(self.cookie_name, '')
        # Look in the request.form for the names coming from the login form
        login = request.form.get('__ac_name', '')

        if login and request.form.has_key('__ac_password'):
            creds['login'] = login
            creds['password'] = request.form.get('__ac_password', '')
        elif cookie_data and cookie_data != 'deleted':
            creds[self.cookie_name] = cookie_data
        if creds:
            creds['remote_host'] = request.get('REMOTE_HOST', '')

            try:
                creds['remote_address'] = request.getClientAddr()
            except AttributeError:
                creds['remote_address'] = request.get('REMOTE_ADDR', '')
        return creds

    # ICredentialsResetPlugin implementation
    def resetCredentials(self, request, response):
        response.expireCookie(self.cookie_name, path='/')

    # IUserEnumerationPlugin implementation
    def enumerateUsers(self, id=None, login=None, exact_match=False,
            sort_by=None, max_results=None, **kw):
        user_info = []
        user_ids = []
        plugin_id = self.getId()
        view_name = createViewName('enumerateUsers', id or login)

        # Look in the cache first...
        keywords = copy.deepcopy(kw)
        keywords.update( { 'id' : id
                         , 'login' : login
                         , 'exact_match' : exact_match
                         , 'sort_by' : sort_by
                         , 'max_results' : max_results
                         }
                       )
        if not keywords.get('id') or not keywords.get('login'):
            keywords['id_or_login'] = keywords.get('id') and keywords.get('id') or keywords.get('login')
            del keywords['id']
            del keywords['login']
        try:
            keywords['id'] = int(keywords.get('id'))
        except:
            pass
        cached_info = self.ZCacheable_get( view_name=view_name
                                         , keywords=keywords
                                         , default=None
                                         )
        
        if cached_info is not None:
            return tuple(cached_info)
        users = []
        conn = getUtility(interfaces.IOdooPasUtility)
        conn.login()
        if not isinstance(keywords.get('id'), int):
            login = keywords.get('id_or_login', keywords.get('login'))
            args = []
            if keywords.get('name') and login:
                if exact_match:
                    args = ['|', ('name', '=', keywords.get('name')), ('login', '=', login)]
                else:
                    args = ['|', ('name', 'ilike', keywords.get('name')), ('login', 'ilike', login)]
            elif login:
                if exact_match:
                    args = [('login', '=', login)]
                else:
                    args = [('login', 'ilike', login)]
            uids = conn.search('res.users', args=args)
        else:
            uids = [int(keywords.get('id'))]
        users += conn.browse('res.users', uids)
        out = []
        for user in users:
            out.append({'id':user.login,
                        'login':user.login,
                        'title':user.name,
                        'fullname':user.name,
                        'email':user.email,
                        'description':user.name,
                        'pluginid' :self.getId()})
        self.ZCacheable_set(out, view_name=view_name, keywords=keywords)
        return tuple(out)

#   IUserAdderPlugin implementation
    security.declarePrivate( 'doAddUser' )
    def doAddUser( self, login, password ):
        try:
            self.addUser( login, login, password )
        except KeyError:
            return False
        return True

    security.declareProtected( ManageUsers, 'getUserInfo' )
    def getUserInfo( self, user_id ):

        """ user_id -> {}
        """
        return { 'user_id' : user_id
               , 'login_name' : self._userid_to_login[ user_id ]
               , 'pluginid' : self.getId()
               }

    security.declareProtected( ManageUsers, 'listUserInfo' )
    def listUserInfo( self ):

        """ -> ( {}, ...{} )

        o Return one mapping per user, with the following keys:

          - 'user_id'
          - 'login_name'
        """
        return [ self.getUserInfo( x ) for x in self._user_passwords.keys() ]

    security.declareProtected( ManageUsers, 'getUserIdForLogin' )
    def getUserIdForLogin( self, login_name ):

        """ login_name -> user_id

        o Raise KeyError if no user exists for the login name.
        """
        return self._login_to_userid[ login_name ]

    security.declareProtected( ManageUsers, 'getLoginForUserId' )
    def getLoginForUserId( self, user_id ):

        """ user_id -> login_name

        o Raise KeyError if no user exists for that ID.
        """
        return self._userid_to_login[ user_id ]
        
    security.declarePrivate( 'addUser' )
    def addUser( self, user_id, login_name, password ):
        users = []
        conn = getUtility(interfaces.IOdooPasUtility)
        user = conn.login()
        conn.create('res.users', {'login':user_id, 'new_password':password})
        # enumerateUsers return value has changed
        view_name = createViewName('enumerateUsers')
        self.ZCacheable_invalidate(view_name=view_name)

    ## User Introspection interface

    security.declareProtected(ManageUsers, 'getUserIds')
    def getUserIds(self):
        """
        Return a list of user ids
        """
        return self.listUserIds()

    security.declareProtected(ManageUsers, 'getUserNames')
    def getUserNames(self):
        """
        Return a list of usernames
        """
        return [x['login_name'] for x in self.listUserInfo()]

    security.declareProtected(ManageUsers, 'getUsers')
    def getUsers(self):
        """
        Return a list of users
        """
        uf = self.acl_users
        users = [uf.getUserById(x) for x in self.getUserIds()]
        return users

    security.declarePublic('allowDeletePrincipal')
    def allowDeletePrincipal(self, principal_id):
        return 1

    security.declarePublic('allowPasswordSet')
    def allowPasswordSet(self, principal_id):
        return self.allowDeletePrincipal(principal_id) 

InitializeClass(OdooPASPlugin)

