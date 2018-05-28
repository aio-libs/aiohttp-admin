import React from 'react';
import PropTypes from 'prop-types';
import {
    Datagrid,
    List,
} from 'admin-on-rest';

import { EditButton } from '../Button/EditButton';
import { ShowButton } from '../Button/ShowButton';
import { getFields } from '../../utils/listFields';


export const BaseList = props => (
  <List {...props}
    title={`List of ${props.resource}`}
    perPage={props.data.perPage}
  >
    <Datagrid>
        {getFields(props.data.fields)}
        {props.data.canEdit ? <EditButton /> : <ShowButton />}
    </Datagrid>
  </List>
);


BaseList.propTypes = {
  resource: PropTypes.string.isRequired,
  data: PropTypes.shape({
    fields: PropTypes.object.isRequired,
    canEdit: PropTypes.bool.isRequired,
    perPage: PropTypes.number.isRequired
  }),
};
