export function loginIsRequired() {
  const { tokenName, mainUrl } = window.appData;
  const fullPath = window.location.toString();
  const isLoginPage = fullPath.includes('#/login');

  if (!localStorage.getItem(tokenName) && !isLoginPage) {
    window.location.replace(`${mainUrl}#/login`);
  } else if (localStorage.getItem(tokenName) && isLoginPage) {
    window.location.replace(mainUrl);
  }
}
