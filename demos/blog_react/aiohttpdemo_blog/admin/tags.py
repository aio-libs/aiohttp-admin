from aiohttp_admin.contrib import models
from aiohttp_admin.backends.sa import PGResource

from .main import schema
from ..db import tag


@schema.register
class Tags(models.ModelAdmin):
    fields = ('id', 'name', 'published', )

    class Meta:
        resource_type = PGResource
        table = tag
