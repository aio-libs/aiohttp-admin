import React from 'react';
import PropTypes from 'prop-types';

import {
  Edit,
  SimpleForm
} from 'admin-on-rest';

import { getInputs } from '../../utils/inputs';


export const BaseEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      {getInputs(props.data.editPage)}
    </ SimpleForm>
  </Edit>
);

BaseEdit.propTypes = {
  data: PropTypes.objectOf({
    editPage: PropTypes.object,
  })
};

export default BaseEdit;
