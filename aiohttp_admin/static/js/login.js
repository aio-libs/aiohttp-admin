function login(e) {
    if (e) {
        e.preventDefault();
    }
    var request = new XMLHttpRequest();
    var data = {"username": document.getElementById('username').value,
        "password": document.getElementById('password').value}
    request.open('POST', '/admin/token', true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.onload = function() {
        if (request.status >= 200 && request.status < 400) {
            var respData = JSON.parse(request.responseText);
            var redirect = respData["location"]
            var token = request.getResponseHeader("X-Token");
            window.localStorage.setItem('aiohttp_admin_token', token);
            window.location = redirect;
        } else {
            alert("go wrong status code");
        }
    };
    request.onerror = function() {
        alert("Connection Error");
    };
    request.send(JSON.stringify(data));
}