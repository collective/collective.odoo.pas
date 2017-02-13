# -*- coding: utf-8 -*-
"""Init and utils."""
from AccessControl.Permissions import add_user_folders
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('collective.odoo.pas')
from plugins import odoopas

def initialize(context):
    """Initializer called when used as a Zope 2 product."""

    context.registerClass(odoopas.OdooPASPlugin,
                          permission=add_user_folders,
                          constructors=(odoopas.manage_addOdooPASPlugin,
                                        odoopas.addOdooPASPlugin),
                          visibility=None
                          )
