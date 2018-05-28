import React from 'react';

import { ShowField } from '../components/Fields/ShowField';


export function getFields(fields) {
  return Object.keys(fields).map(function(key, index) {

    return (
      <ShowField
        key={index}
        source={fields[key].name}
      />
    );
  });
}
