import React from 'react';
import PropTypes from 'prop-types';

import {
  Create,
  SimpleForm,
} from 'admin-on-rest';

import { getInputs } from '../../utils/inputs';


export const BaseCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      {getInputs(props.data.createPage)}
    </SimpleForm>
  </Create>
);

BaseCreate.propTypes = {
  data: PropTypes.objectOf({
    createPage: PropTypes.object,
  })
};

export default BaseCreate;
