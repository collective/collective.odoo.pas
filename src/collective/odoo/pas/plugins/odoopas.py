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
        LOG.info(data)
        data['fullname'] = data['name']
        partner = OdooPartner(user_id, name)
        self.ZCacheable_set(data, view_name=view_name, keywords=keywords)
        partner.addPropertysheet( 'odoo', data )
        return partner

    # IAuthenticationPlugin implementation
    security.declarePrivate( 'authenticateCredentials' )
    def authenticateCredentials(self, credentials):
        login = credentials.get( 'login' )
        password = credentials.get( 'password' )
        if login is None or password is None:
            return None
        LOG.info('authenticateCredentials: '+str(credentials))
        conn = getUtility(interfaces.IOdooPasUtility)
        try:
            user = conn.login(login, password)
            return user.login, user.login
        except error.RPCError as exc:
            LOG.info("Odoo Authentication for %s failed: %s",
                            credentials['login'], exc.message)
        return None

    # ICredentialsUpdatePlugin implementation
    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, new_password):
        """Override standard updateCredentials method
        """
        conn = getUtility(interfaces.IOdooPasUtility)
        cnt = conn.getProxy(request, response)

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
            conn = getUtility(interfaces.IOdooPasUtility)
            cnt = conn.getProxy(request)
            # TODO (When do we have to call that?)
        if creds:
            creds['remote_host'] = request.get('REMOTE_HOST', '')

            try:
                creds['remote_address'] = request.getClientAddr()
            except AttributeError:
                creds['remote_address'] = request.get('REMOTE_ADDR', '')

        return creds

    # IUserEnumerationPlugin implementation
    def enumerateUsers(self, id=None, login=None, exact_match=False,
            sort_by=None, max_results=None, **kw):
        LOG.info('enumerateUsers')
        user_info = []
        user_ids = []
        plugin_id = self.getId()
        view_name = createViewName('enumerateUsers', id or login)


        if isinstance( id, basestring ):
            id = [ id ]

        if isinstance( login, basestring ):
            login = [ login ]

        # Look in the cache first...
        keywords = copy.deepcopy(kw)
        keywords.update( { 'id' : id
                         , 'login' : login
                         , 'exact_match' : exact_match
                         , 'sort_by' : sort_by
                         , 'max_results' : max_results
                         }
                       )
        LOG.info(view_name)
        LOG.info(keywords)
        cached_info = self.ZCacheable_get( view_name=view_name
                                         , keywords=keywords
                                         , default=None
                                         )
        
        if cached_info is not None:
            return tuple(cached_info)
        LOG.info('not cached')
        users = []
        conn = getUtility(interfaces.IOdooPasUtility)
        LOG.info('try login')
        main_user = conn.login()
        LOG.info(main_user)
        args = []
        if keywords.get('name') and keywords.get('login'):
            if exact_match:
                args = ['|', ('name', '=', keywords.get('name')), ('login', '=', keywords.get('login'))]
            else:
                args = ['|', ('name', 'ilike', keywords.get('name')), ('login', 'ilike', keywords.get('login'))]
        elif keywords.get('id', keywords.get('login')):
            if exact_match:
                args = [('login', '=', keywords.get('id', keywords.get('login')))]
            else:
                args = [('login', 'ilike', keywords.get('id', keywords.get('login')))]
        uids = conn.search('res.users', args=args)
        LOG.info(uids)
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
        LOG.info(out)
        LOG.info(view_name)
        LOG.info(keywords)
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
        LOG.info(users)
        return users

    security.declarePublic('allowDeletePrincipal')
    def allowDeletePrincipal(self, principal_id):
        return 1

    security.declarePublic('allowPasswordSet')
    def allowPasswordSet(self, principal_id):
        return self.allowDeletePrincipal(principal_id) 

InitializeClass(OdooPASPlugin)

