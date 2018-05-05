import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import IconButton from 'material-ui/IconButton';
import ContentShow from 'material-ui/svg-icons/image/remove-red-eye';


export const ShowButton = ({ basePath = '', record = {} }) => (
  <IconButton
    containerElement={<Link to={`${basePath}/${record.id}/show`} />}
    style={{ overflow: 'inherit' }}
  >
    <ContentShow />
  </IconButton>
);


ShowButton.propTypes = {
  basePath: PropTypes.string,
  record: PropTypes.object,
};


ShowButton.defaultProps = {
  style: { padding: '0 12px' },
};
