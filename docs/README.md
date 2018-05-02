# The docs for the new admin realization

## Library Installation
```
pip install aiohttp_django
```

## ModelAdmin
```python
@schema.register
class Tags(models.ModelAdmin):
    fields = ('id', 'name', 'published', )

    class Meta:
        resource_type = PGResource
        table = tag
```

`ModelAdmin.fields` by default it's primary key

`ModelAdmin.can_create` if it's `True` then show create button (by default is `True`)

`ModelAdmin.can_edit` if it's `True` then show edit button (by default is `True`)

`ModelAdmin.can_delete` if it's `True` then show delete button (by default is `True`)

`ModelAdmin.per_page` count of items in a list page (by default is `10`)
