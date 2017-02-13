# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from collective.odoo.pas.testing import COLLECTIVE_ODOO_PAS_INTEGRATION_TESTING  # noqa
from plone import api

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.odoo.pas is properly installed."""

    layer = COLLECTIVE_ODOO_PAS_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.odoo.pas is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'collective.odoo.pas'))

    def test_browserlayer(self):
        """Test that ICollectiveOdooPasLayer is registered."""
        from collective.odoo.pas.interfaces import (
            ICollectiveOdooPasLayer)
        from plone.browserlayer import utils
        self.assertIn(ICollectiveOdooPasLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = COLLECTIVE_ODOO_PAS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['collective.odoo.pas'])

    def test_product_uninstalled(self):
        """Test if collective.odoo.pas is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'collective.odoo.pas'))

    def test_browserlayer_removed(self):
        """Test that ICollectiveOdooPasLayer is removed."""
        from collective.odoo.pas.interfaces import ICollectiveOdooPasLayer
        from plone.browserlayer import utils
        self.assertNotIn(ICollectiveOdooPasLayer, utils.registered_layers())
