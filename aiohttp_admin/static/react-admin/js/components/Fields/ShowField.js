import React from 'react';
import PropTypes from 'prop-types';
import get from 'lodash.get';
import { BooleanField } from 'admin-on-rest';


export class ShowField extends  React.Component {
  render () {
    const { source, record = {} } = this.props;
    let data = get(record, source);

    if (data instanceof Object) {
      data = JSON.stringify(data, null, 2);
    } else if (typeof(data) === 'boolean') {
      return (
        <BooleanField
          {...this.props}
          elStyle={{width: '24px', margin: 0}}
        />
      );
    }

    return <span>{data}</span>;
  }
}

ShowField.defaultProps = {
  addLabel: true,
};

ShowField.propTypes ={
  source: PropTypes.string.isRequired,
  record: PropTypes.object,
};

export default ShowField;
