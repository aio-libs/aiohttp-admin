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
} from 'admin-on-rest';
import { EditButton } from '../Button/EditButton';
import { ShowButton } from '../Button/ShowButton';


const DATA_TYPES = {
  'integer': TextField,
  'number': NumberField,
  'string': TextField,
  'date': DateField,
  'bool': BooleanField,
  'json': FunctionField,
};

const fieldStyle = {
  maxWidth: '18em',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
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

    if (type_field === 'json') {
      return (
        <FunctionField
          key={index}
          label={key}
          render={res => JSON.stringify(res[key])}
        />
      );
    }

    return <Component key={index} source={key} style={fieldStyle} />;
  });
}


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
