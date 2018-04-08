from aiohttp_admin.contrib import models
from aiohttp_admin.backends.sa import PGResource

from .main import schema
from ..db import comment


@schema.register
class Comments(models.ModelAdmin):
    fields = ('id', 'post_id', 'created_at', 'body', )

    class Meta:
        resource_type = PGResource
        table = comment
