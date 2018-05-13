import {
  BooleanField,
  DateField,
  DateInput,
  FunctionField,
  NbItemsField,
  NullableBooleanInput,
  NumberField,
  ProductReferenceField,
  ReferenceManyField,
  SegmentsInput,
  StarRatingField,
  TextField,
  TextInput,
} from 'admin-on-rest';

import JsonField from './components/Fields/JsonField';
import JsonInput from './components/Inputs/JsonInput';


export const defaultFieldStyle = {
  maxWidth: '18em',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};


export const COMPONENTS = {
  'TextField': {
    component: TextField,
    props: {},
    style: defaultFieldStyle,
  },
  'JsonField': {
    component: JsonField,
    props: {sortable: false},
    style: {},
  },
  'DateField': {
    component: DateField,
    props: {},
    style: defaultFieldStyle,
  },
  'NumberField': {
    component: NumberField,
    props: {},
    style: defaultFieldStyle,
  },
  'BooleanField': {
    component: BooleanField,
    props: {},
    style: defaultFieldStyle,
  },
  'FunctionField': {
    component: FunctionField,
    props: {},
    style: defaultFieldStyle,
  },
  'ReferenceManyField': {
    component: ReferenceManyField,
    props: {},
    style: defaultFieldStyle,
  },
  'ProductReferenceField': {
    component: ProductReferenceField,
    props: {},
    style: defaultFieldStyle,
  },
  'StarRatingField': {
    component: StarRatingField,
    props: {},
    style: defaultFieldStyle,
  },
  'NbItemsField': {
    component: NbItemsField,
    props: {},
    style: defaultFieldStyle,
  },
  'TextInput': {
    component: TextInput,
    props: {},
    style: defaultFieldStyle,
  },
  'DateInput': {
    component: DateInput,
    props: {},
    style: defaultFieldStyle,
  },
  'SegmentsInput': {
    component: SegmentsInput,
    props: {},
    style: defaultFieldStyle,
  },
  'NullableBooleanInput': {
    component: NullableBooleanInput,
    props: {},
    style: defaultFieldStyle,
  },
  'JsonInput': {
    component: JsonInput,
    props: {defaultValue: {}},
    style: {},
  },
};
