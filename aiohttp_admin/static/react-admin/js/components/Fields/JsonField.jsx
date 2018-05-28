import React from 'react';
import PropTypes from 'prop-types';


export function JsonField({ record = {}, source }) {
  const render = res => JSON.stringify(res[source], null, 2);

  return <span>{render(record)}</span>;
}

JsonField.propTypes = {
  source: PropTypes.string,
  record: PropTypes.object,
};

export default JsonField;
