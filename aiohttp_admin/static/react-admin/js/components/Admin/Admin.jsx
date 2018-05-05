import React, { Component } from 'react';
import { Admin, Resource, Delete } from 'admin-on-rest';
import Icon from 'material-ui/svg-icons/action/bookmark-border';

import { BaseList } from '../List/List';
import { BaseEdit } from '../Edit/Edit';
import { BaseCreate } from '../Create/Create';
import { BaseShow } from '../Show/Show';
import authClient from '../../libs/authClient';
import { restClient } from '../../libs/restClient';
import Layout from '../Layout/Layout';

// styles
import './Admin.sass';

const { state } = window.appData;


const getAccessMethods = (data) => {
  const { canEdit, canCreate, canDelete } = data;
  let methods = {
    list: newProps => <BaseList {...newProps} data={data} />,
    show: newProps => <BaseShow {...newProps} data={data} />,
  };

  if (canEdit) {
    methods = {
      ...methods,
      edit: newProps => <BaseEdit {...newProps} data={data} />
    };
  }

  if (canCreate) {
    methods = {
      ...methods,
      create: newProps => <BaseCreate {...newProps} data={data} />
    };
  }

  if (canDelete) {
    methods = {
      ...methods,
      remove: Delete
    };
  }

  return methods;
};


function generateResourcesByState(state) {
  if (state.endpoints) {
    return  (
      state.endpoints.map((data, index) => (
        <Resource
          key={index}
          name={data.name}
          icon={Icon}
          sort={{ field: 'id', order: 'DESC' }}
          {...getAccessMethods(data)}
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
          appLayout={Layout}
        >
          {generateResourcesByState(state)}
        </Admin>
    );
  }
}
