from enum import Enum


class ReactComponent(Enum):
    """
    Represented React components of `admin-on-rest`.
    """

    # fields
    TEXT_FIELD = 'TextField'
    JSON_FIELD = 'JsonField'
    DATE_FIELD = 'DateField'
    NUMBER_FIELD = 'NumberField'
    BOOLEAN_FIELD = 'BooleanField'
    FUNCTION_FIELD = 'FunctionField'
    REFERENCE_MANY_FIELD = 'ReferenceManyField'
    PRODUCT_REFERENCE_FIELD = 'ProductReferenceField'
    STAR_RATING_FIELD = 'StarRatingField'
    MB_ITEMS_FIELD = 'NbItemsField'

    # inputs
    TEXT_INPUT = 'TextInput'
    DATE_INPUT = 'DateInput'
    SEGMENTS_INPUT = 'SegmentsInput'
    NULLABLE_BOOLEAN_INPUT = 'NullableBooleanInput'
    LONG_TEXT_INPUT = 'LongTextInput'
    JSON_INPUT = 'JsonInput'
