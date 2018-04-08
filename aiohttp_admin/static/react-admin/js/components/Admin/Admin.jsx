import React, { Component } from 'react';
import { Admin, Resource } from 'admin-on-rest';
import Icon from 'material-ui/svg-icons/action/bookmark-border';

import { BaseList } from '../List/List';
import authClient from '../../libs/authClient';
import { restClient } from '../../libs/restClient';

// styles
import './Admin.sass';

const { state } = window.appData;


function getResourcesByState(state) {
  if (state.endpoints) {
    return  (
      state.endpoints.map((data, index) => (
        <Resource
          key={index}
          name={data.name}
          icon={Icon}
          list={(newProps) => <BaseList {...newProps} data={data} />}
          sort={{ field: 'id', order: 'DESC' }}
        />
      ))
    );
  }

  return null;
}


export class AioHttpAdmin extends Component {

  render() {
    return (
      <Admin
        title={state.title}
        locale="en"
        authClient={authClient}
        restClient={restClient}
      >
        {getResourcesByState(state)}
      </Admin>
    );
  }
}
