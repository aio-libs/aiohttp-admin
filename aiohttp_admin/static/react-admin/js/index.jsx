import React from 'react';
import { render } from 'react-dom';

import { AioHttpAdmin } from './components/Admin/Admin';
import { loginIsRequired } from './utils/loginIsRequired';


// add listener for redirect user from login page if user is authorized and
// vice versa
loginIsRequired();
window.addEventListener('popstate', loginIsRequired);


render(
  <AioHttpAdmin />,
  document.getElementById('root')
);
