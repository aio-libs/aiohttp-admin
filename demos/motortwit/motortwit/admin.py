from pathlib import Path

from motortwit import db
from aiohttp_admin.layout_utils import generate_config


base_url = '/admin'
entities = [
    ("user", "_id", db.user),
    ("message", "_id", db.message),
    ("follower", "_id", db.follower),
]

config_str = generate_config(entities, base_url)
path = Path(__file__).parent.absolute()

config_location = path / '..' / 'static/js/config2.js'
with open(str(config_location), 'w') as f:
    f.write(config_str)
