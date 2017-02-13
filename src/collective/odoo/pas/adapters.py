# -*- coding: utf-8 --
import logging
from persistent import Persistent
from zope import component, schema
from zope.interface import implementer, provider
from zope.component import adapter
from zope.annotation import factory
from Products.CMFCore.interfaces import ISiteRoot
import interfaces

LOG = logging.getLogger(__name__)

@implementer(interfaces.IOdooPasSettings)
@adapter(ISiteRoot)
class OdooPasSettingsAdapter(Persistent):
  
    def __init__(self, **kwargs):
        iface = interfaces.IOdooPasSettings
        for field in [iface.get(name) for name in iface.names() if schema.interfaces.IField.providedBy(iface.get(name))]:
            setattr(self, field.__name__, kwargs.get(field.__name__, field.default))

OdooPasSettings = factory(OdooPasSettingsAdapter)
