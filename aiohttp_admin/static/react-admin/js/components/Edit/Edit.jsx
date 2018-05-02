import React from 'react';
import PropTypes from 'prop-types';

import {
  Datagrid,
  List,
  TextField,
  DateField,
  NumberField,
  BooleanField,
  FunctionField,
  TabbedForm,
  FormTab,
  TextInput,
  DateInput,
  ReferenceManyField,
  NbItemsField,
  EditButton,
  ProductReferenceField,
  StarRatingField,
  SegmentsInput,
  NullableBooleanInput,
  Edit,
  SimpleForm
} from 'admin-on-rest';


export const BaseEdit = (props) => (
  <Edit {...props}>
      <SimpleForm>
        <TextInput source="id" style={{ display: 'block' }} />
      </ SimpleForm>
  </Edit>
);
