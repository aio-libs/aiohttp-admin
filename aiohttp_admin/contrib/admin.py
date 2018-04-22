import json


__all__ = ['Schema', ]


class Schema:
    """
    The main abstraction for registering tables and presenting data in
    admin-on-rest format.
    """

    def __init__(self, title='Admin'):
        self.title = title
        self.endpoints = []

    def register(self, Endpoint):
        """
        Register a wrapped `ModelAdmin` class as the endpoint for admin page.

        @schema.register
        class User(admin.ModelAdmin):
            pass

        """
        self.endpoints.append(Endpoint())

        return Endpoint

    def to_json(self):
        """
        Prepare data for the initial state of the admin-on-rest
        """
        endpoints = []
        for endpoint in self.endpoints:
            list_fields = endpoint.fields
            resource_type = endpoint.Meta.resource_type
            table = endpoint.Meta.table

            data = endpoint.to_dict()
            data['fields'] = resource_type.get_type_of_fields(
                list_fields,
                table,
            )
            endpoints.append(data)

        data = {
            'title': self.title,
            'endpoints': sorted(endpoints, key=lambda x: x['name']),
        }

        return json.dumps(data)

    @property
    def resources(self):
        """
        Return list of all registered resources.
        """
        resources = []

        for endpoint in self.endpoints:
            resource_type = endpoint.Meta.resource_type
            table = endpoint.Meta.table
            url = endpoint.name

            resources.append((resource_type, {'table': table, 'url': url}))

        return resources
