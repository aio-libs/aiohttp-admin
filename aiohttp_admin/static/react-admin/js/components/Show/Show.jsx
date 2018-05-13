import React from 'react';
import PropTypes from 'prop-types';
import {
  Show,
  SimpleShowLayout
} from 'admin-on-rest';

import { getFields } from '../../utils/fields';


export const BaseShow = (props) => (
  <Show {...props}>
    <SimpleShowLayout>
      {getFields(props.data.showPage)}
    </SimpleShowLayout>
  </Show>
);

BaseShow.propTypes = {
  data: PropTypes.objectOf({
    showPage: PropTypes.object,
  }),
};

export default BaseShow;
