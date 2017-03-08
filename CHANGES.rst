Changelog
=========
1.0a4 (unreleased)
------------------
- fix missing queryUtility import in odoopas enumerateUsers
- fix search method from oerplib with Odoo 10 (Oerplib shoud be updated!)

1.0a3 (unreleased)
------------------
- Removed wrong imports
- Update odoo connection utility on setup changes

1.0a2 (unreleased)
------------------
Refactored the whole machinery.
- Now it creats an utility with the Odoo connector configuration and the bas xmlrpc/jsonrpx configuration
- Now it get cookie or login/pwd to credentials.
- Authentication on credentials is made through xmlrpc by maing an authentication on Odoo
- updateCredentials by adding th session cookie of Odoo.
- further requests might be done by rest requests (jsonrpc)

1.0a1 (unreleased)
------------------

- Initial release.
  [Martronic-SA]
