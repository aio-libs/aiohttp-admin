from aiohttp_admin.contrib import models
from aiohttp_admin.backends.sa import PGResource

from .main import schema
from ..db import tag


@schema.register
class Tags(models.ModelAdmin):
    fields = ('id', 'name', 'published', )
    can_edit = False
    can_create = False
    can_delete = False
    per_page = 20

    class Meta:
        resource_type = PGResource
        table = tag
