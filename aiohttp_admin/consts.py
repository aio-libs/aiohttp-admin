import pathlib


PROJ_ROOT = pathlib.Path(__file__).parent.resolve()
TEMPLATES_ROOT = PROJ_ROOT / 'templates'
APP_KEY = 'aiohttp_admin'
TEMPLATE_APP_KEY = 'aiohttp_admin.templates'
