import React from 'react';
import PropTypes from 'prop-types';
import {
    Datagrid,
    List,
    TextField,
    DateField,
    NumberField,
} from 'admin-on-rest';


const DATA_TYPES = {
  'integer': TextField,
  'number': NumberField,
  'string': TextField,
  'date': DateField,
};


function getFields(fields) {
  return Object.keys(fields).map(function(key, index) {
    const type_field = fields[key];
    let Component;

    if (DATA_TYPES.hasOwnProperty(type_field)) {
      Component = DATA_TYPES[type_field];
    } else {
      Component = TextField;
    }

    return <Component key={index} source={key} />;
  });
}


export const BaseList = props => (
  <List {...props}
    title={`List of ${props.resource}`}
  >
    <Datagrid>
        {getFields(props.data.fields)}
    </Datagrid>
  </List>
);


BaseList.propTypes = {
  resource: PropTypes.string.isRequired,
  data: PropTypes.shape({
    fields: PropTypes.object
  }),
};
