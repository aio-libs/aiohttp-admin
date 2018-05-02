import React from 'react';
import PropTypes from 'prop-types';

import {
  Show,
  TextField,
  SimpleShowLayout
} from 'admin-on-rest';


export const BaseShow = (props) => (
  <Show {...props}>
    <SimpleShowLayout>
      <TextField source="id" />
    </SimpleShowLayout>
  </Show>
);
