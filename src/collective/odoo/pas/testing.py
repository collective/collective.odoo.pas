# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import collective.odoo.pas


class CollectiveOdooPasLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=collective.odoo.pas)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.odoo.pas:default')


COLLECTIVE_ODOO_PAS_FIXTURE = CollectiveOdooPasLayer()


COLLECTIVE_ODOO_PAS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_ODOO_PAS_FIXTURE,),
    name='CollectiveOdooPasLayer:IntegrationTesting'
)


COLLECTIVE_ODOO_PAS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_ODOO_PAS_FIXTURE,),
    name='CollectiveOdooPasLayer:FunctionalTesting'
)


COLLECTIVE_ODOO_PAS_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_ODOO_PAS_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='CollectiveOdooPasLayer:AcceptanceTesting'
)
