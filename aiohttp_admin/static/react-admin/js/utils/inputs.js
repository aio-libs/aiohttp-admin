import React from 'react';

import { COMPONENTS } from '../constants';


export function getInputs(fields) {
  return Object.keys(fields).map(function(key, index) {
    let Component = COMPONENTS[fields[key].type] || COMPONENTS.TextInput;

    return (
      <Component.component
        key={index}
        source={fields[key].name}
        style={Component.style}
        {...Component.props}
      />
    );
  });
}
