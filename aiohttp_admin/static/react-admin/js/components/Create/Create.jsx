import React from 'react';
import PropTypes from 'prop-types';

import {
    TextInput,
    Create,
    SimpleForm,
    LongTextInput,
} from 'admin-on-rest';


export const BaseCreate = (props) => (
    <Create {...props}>
        <SimpleForm>
            <TextInput source="body" />
        </SimpleForm>
    </Create>
);
