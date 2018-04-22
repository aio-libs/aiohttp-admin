class ModelAdmin:
    """
    The class provides the possibility of declarative describe of information
    about the table and describe all things related to viewing this table on
    the administrator's page.


    class Users(models.ModelAdmin):
        fields = ('id', 'username', )

        class Meta:
            resource_type = PGResource
            table = users

    """

    def __init__(self):
        self.name = self.__class__.__name__.lower()

    def to_dict(self):
        """
        Return dict with the all base information about the instance.
        """

        data = {"name": self.name}

        return data
