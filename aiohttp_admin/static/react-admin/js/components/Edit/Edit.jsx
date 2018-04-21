import React from 'react';
import PropTypes from 'prop-types';

import {
    Datagrid,
    List,
    TextField,
    DateField,
    NumberField,
    BooleanField,
    FunctionField,
    TabbedForm,
    FormTab,
    TextInput,
    DateInput,
    ReferenceManyField,
    NbItemsField,
    EditButton,
    ProductReferenceField,
    StarRatingField,
    SegmentsInput,
    NullableBooleanInput,
    Edit
} from 'admin-on-rest';


export const BaseEdit = (props) => (
    <Edit title="Title" {...props}>
        <TabbedForm>
            <FormTab label="resources.customers.tabs.identity">
                <TextInput source="id" style={{ display: 'block' }} />
                <TextInput source="title" style={{ display: 'block', width: 'auto' }} />
                <TextInput source="name" style={{ display: 'block', width: 'auto' }} />
                <TextInput source="PICTURES" style={{ display: 'block', width: 'auto' }} />
            </FormTab>
        </TabbedForm>
    </Edit>
);
