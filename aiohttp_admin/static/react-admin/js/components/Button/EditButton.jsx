import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import IconButton from 'material-ui/IconButton';
import ContentCreate from 'material-ui/svg-icons/content/create';


export const EditButton = ({ basePath = '', record = {} }) => (
  <IconButton
    containerElement={<Link to={`${basePath}/${record.id}`} />}
    style={{ overflow: 'inherit' }}
  >
    <ContentCreate />
  </IconButton>
);


EditButton.propTypes = {
  basePath: PropTypes.string,
  record: PropTypes.object,
};


EditButton.defaultProps = {
  style: { padding: '0 12px' },
};
