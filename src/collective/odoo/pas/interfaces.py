# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface
from zope import schema
from . import _

class ICollectiveOdooPasLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IOdooState(Interface):
    """Odoo state will allow you to keep an odoo session open and use it to dialog with Odoo"""

class IOdooPasUtility(Interface):
    """Utility that manages the connection, initialized once on first traversing"""

class IOdooPasSettings(Interface):

    name = schema.TextLine(
        title = _(u"Name"),
        description=_(u"A unique name for this config."),
        required = True
    )

    http_host = schema.TextLine(
        title = _(u"Host URL of your Odoo (localhost)"),
        required = True
    )

    http_address = schema.Int(
        title = _(u"Address of your Odoo (8060)"),
        required = True
    )

    username = schema.TextLine(
        title = _(u"User name for accessing your Odoo database."),
        required = True
    )

    password = schema.TextLine(
        title = _(u"Password for the username"),
        required = True
    )

    dbname = schema.TextLine(
        title = _(u"Name of your Odoo database"),
        required = True
    )
