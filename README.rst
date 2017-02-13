.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

==============================================================================
collective.odoo.pas
==============================================================================

This product adds a Plone Ahthentication Service Plugin that will allow you to share authentication between Plone and Odoo.
Opening a Plone session will automatically open an Odoo session by adding the two cookies.
The Odoo users (not partners) will be listed in the plone group and users form

Features
--------

- Create a user through the standard Plone join form and get the users in Odoo
- Authenticate in Plone unsing Odoo login / pwd
- List Odoo users in Plone


Installation
------------

Install collective.odoo.pas by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.odoo.pas


and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.odoo.pas/issues
- Source Code: https://github.com/collective/collective.odoo.pas
- Documentation: https://docs.plone.org/foo/bar


Support
-------

If you are having issues, please let us know.
We have a mailing list located at: project@example.com


License
-------

The project is licensed under the GPLv2.
