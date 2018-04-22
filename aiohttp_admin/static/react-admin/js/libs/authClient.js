import { AUTH_LOGIN, AUTH_LOGOUT, AUTH_CHECK } from 'admin-on-rest';


const { tokenName, tokenUrl, logoutUrl } = window.appData;


export default (type, params) => {
  if (type === AUTH_LOGIN) {
    const { username, password } = params;
    const request = new Request(tokenUrl, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
      headers: new Headers({ 'Content-Type': 'application/json' }),
    });

    return fetch(request)
      .then(response => {
        if (response.status < 200 || response.status >= 300) {
          throw new Error(response.statusText);
        }

        localStorage.setItem(tokenName, response.headers.get('X-Token'));
      });
  }

  if (type === AUTH_LOGOUT) {
    const request = new Request(logoutUrl, {
      method: 'DELETE',
      headers: new Headers({
        'Content-Type': 'application/json',
        'Authorization': localStorage.getItem(tokenName),
      }),
    });

    return fetch(request)
      .then(response => {
        if (response.status < 200 || response.status >= 300) {
          throw new Error(response.statusText);
        }

        localStorage.removeItem(tokenName);
      });
  }
  if (type === AUTH_CHECK) {
    if (localStorage.getItem(tokenName)) {
      return Promise.resolve();
    }

    return Promise.reject();
  }

  return Promise.reject('Unknown method');
};
