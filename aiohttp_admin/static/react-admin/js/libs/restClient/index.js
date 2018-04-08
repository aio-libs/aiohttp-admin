import { fetchUtils } from 'admin-on-rest';

import simpleRestClient from './restClient';


const {restUrl, tokenName} = window.appData;


const httpClient = (url, options = {}) => {
  if (!options.headers) {
    options.headers = new Headers({ Accept: 'application/json' });
  }

  options.headers.set('Authorization', localStorage.getItem(tokenName));
  return fetchUtils.fetchJson(url, options);
};


export const restClient = simpleRestClient(restUrl, httpClient);
