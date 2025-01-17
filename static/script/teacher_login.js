let accessToken = null;

// 登入邏輯

document.getElementById('login-button').addEventListener('click', () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
 
    if (!username || !password) {
        alert("請輸入帳號和密碼！");
        return;
    }

    fetch('http://127.0.0.1:5000/api/t_login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('請檢查帳號或密碼');
        }
        return response.json();
    })
    .then(data => {
        accessToken = data.access_token;
        alert('成功登錄！');
        window.location.href = 'home.html';

    })
    .catch(error => alert(error.message));
});

