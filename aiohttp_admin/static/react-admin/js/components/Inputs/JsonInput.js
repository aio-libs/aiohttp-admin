import React from 'react';
import PropTypes from 'prop-types';
import { FieldTitle } from 'admin-on-rest';

import TextField from 'material-ui/TextField';


const JsonInput = ({
  input,
  isRequired,
  label,
  source,
  elStyle,
  resource,
}) => {
  const toString = value => {
    if (value instanceof Object) {
      return JSON.stringify(value, null, 2);
    }
    return value;
  };

  return (
    <TextField
      {...input}
      value={input.value}
      source={source}
      resource={resource}
      multiLine
      fullWidth
      floatingLabelText={
        <FieldTitle
          label={label}
          source={source}
          resource={resource}
          isRequired={isRequired}
        />
      }
      style={elStyle}
    />
  );
};

JsonInput.propTypes = {
  addField: PropTypes.bool.isRequired,
  elStyle: PropTypes.object,
  input: PropTypes.object,
  isRequired: PropTypes.bool,
  label: PropTypes.string,
  resource: PropTypes.string,
  source: PropTypes.string,
  validate: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.arrayOf(PropTypes.func),
  ]),
};

JsonInput.defaultProps = {
  addField: true,
  options: {},
};

export default JsonInput;
