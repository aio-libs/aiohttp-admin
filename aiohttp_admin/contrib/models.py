class ModelAdmin:
    """
    The class provides the possibility of declarative describe of information
    about the table and describe all things related to viewing this table on
    the administrator's page.


    class Users(models.ModelAdmin):

        class Meta:
            resource_type = PGResource
            table = users

    """
    can_edit = True
    can_create = True
    can_delete = True
    per_page = 10
    fields = None
    form = None
    edit_form = None
    create_form = None
    show_form = None

    def __init__(self):
        self.name = self.__class__.__name__.lower()
        self._table = self.Meta.table
        self._resource_type = self.Meta.resource_type

    def to_dict(self):
        """
        Return dict with the all base information about the instance.
        """
        data = {
            "name": self.name,
            "canEdit": self.can_edit,
            "canCreate": self.can_create,
            "canDelete": self.can_delete,
            "perPage": self.per_page,
            "showPage": self.generate_data_for_show_page(),
            "editPage": self.generate_data_for_edit_page(),
            "createPage": self.generate_data_for_create_page(),
        }

        return data

    def generate_simple_data_page(self):
        """
        Generate a simple representation of table's fields in dictionary type.

        :return: dict
        """
        return self._resource_type.get_type_for_inputs(self._table)

    def generate_data_for_edit_page(self):
        """
        Generate a custom representation of table's fields in dictionary type
        if exist edit form else use default representation.

        :return: dict
        """

        if not self.can_edit:
            return {}

        if self.edit_form:
            return self.edit_form.to_dict()

        return self.generate_simple_data_page()

    def generate_data_for_show_page(self):
        """
        Generate a custom representation of table's fields in dictionary type
        if exist show form else use default representation.

        :return: dict
        """
        if self.show_form:
            return self.show_form.to_dict()

        return self.generate_simple_data_page()

    def generate_data_for_create_page(self):
        """
        Generate a custom representation of table's fields in dictionary type
        if exist create form else use default representation.

        :return: dict
        """
        if not self.can_create:
            return {}

        if self.create_form:
            return self.create_form.to_dict()

        return self.generate_simple_data_page()
