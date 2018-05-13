import React from 'react';

import { COMPONENTS } from '../constants';


export function getFields(fields) {
  return Object.keys(fields).map(function(key, index) {
    let Component = COMPONENTS[fields[key]] || COMPONENTS.TextField;

    return (
      <Component.component
        key={index}
        source={key}
        style={Component.style}
        {...Component.props}
      />
    );
  });
}
