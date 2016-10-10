(function init() {
    var loginPanel = document.getElementById('login-panel');
    var form = document.getElementById('login-form');
    var errorMsg = document.getElementById('error-message');

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        var url = form.getAttribute('action');
        var data = {
            'username': form.username.value,
            'password': form.password.value
        };
        ajaxRequest(url, data, onSuccess, onError);
    });

    function ajaxRequest(url, data, successCallback, errorCallback) {
        var xhr = new XMLHttpRequest();

        xhr.open('POST', url);
        xhr.setRequestHeader('Content-type', 'application/json');

        xhr.onload = function () {
            if (xhr.status === 200) {
                successCallback(xhr);
            } else {
                var response = JSON.parse(xhr.responseText);
                errorCallback(response.error);
            }
        };
        xhr.onerror = function () {
            errorCallback('Connection error. Try again later');
        };

        xhr.send(JSON.stringify(data));
    }

    function onSuccess(xhr) {
        var response = JSON.parse(xhr.responseText);
        var token = xhr.getResponseHeader('X-Token');
        errorMsg.innerHTML = '';
        window.localStorage.setItem('aiohttp_admin_token', token);
        window.location = response['location'];
    }

    function onError(message) {
        errorMsg.innerHTML = message;
        loginPanel.classList.remove('animate');
        void loginPanel.offsetWidth;   // triggering reflow /* The actual magic */
        loginPanel.classList.add('animate');
    }
})();