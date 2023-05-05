=======
CHANGES
=======

.. towncrier release notes start

0.1.0a1 (2023-04-23)
====================

- Removed ``auth_policy`` parameter from ``setup()``, this is no longer needed.
- Added a default ``identity_callback`` for simple applications, so it is no longer a required schema item.
- Added ``Permissions.all`` enum value (which should replace ``tuple(Permissions)``).
- Added validators to inputs (e.g. required, minValue etc. See examples/validators.py).
- Added extensive permission controls (see examples/permissions.py).
- Added ``admin["permission_re"]`` regex object to test if permission strings are valid.
- Added buttons for the user to change visible columns in the list view.
- Added initial support for ORM (1-to-many) relationships.
- Added option to add simple bulk update buttons.
- Added option to customise resource icons in sidebar.
- Added option to customise admin title and resource labels.
- Added support for non-id primary keys.
- Added default favicon.
- Included JS map file.
- Fixed autocomplete behaviour in reference inputs (e.g. for foreign keys).
- Fixed handling of date/datetime inputs.

0.1.0a0 (2023-02-27)
====================

- Migrated to react-admin and completely reinvented the API.
