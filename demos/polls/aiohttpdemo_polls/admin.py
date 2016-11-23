from pathlib import Path

from aiohttpdemo_polls import db
from aiohttp_admin.layout_utils import generate_config


base_url = '/admin'
entities = [
    ("question", "id", db.question),
    ("choice", "id", db.choice),
]

config_str = generate_config(entities, base_url)
path = Path(__file__).parent.absolute()

config_location = path / '..' / 'static/js/config2.js'
with open(str(config_location), 'w') as f:
    f.write(config_str)
