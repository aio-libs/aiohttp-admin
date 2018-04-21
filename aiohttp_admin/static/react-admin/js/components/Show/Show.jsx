import React from 'react';
import PropTypes from 'prop-types';

import {
    TextInput,
    Show,
    SimpleForm,
    LongTextInput,
} from 'admin-on-rest';


export const BaseShow = (props) => (
    <Show {...props}>
        <SimpleForm>
            <TextInput source="title" />
            <LongTextInput source="body" />
        </SimpleForm>
    </Show>
);
