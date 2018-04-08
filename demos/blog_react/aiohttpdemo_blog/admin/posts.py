from aiohttp_admin.contrib import models
from aiohttp_admin.backends.sa import PGResource

from .main import schema
from ..db import post


@schema.register
class Posts(models.ModelAdmin):
    fields = ('id', 'title',)

    class Meta:
        resource_type = PGResource
        table = post
