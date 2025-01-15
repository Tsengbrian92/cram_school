async function submitAttendance() {
    // 取得輸入值
    const studentId = document.getElementById('studentId').value;
    const password = document.getElementById('password').value;
    const messageDiv = document.getElementById('message');

    // 簡單驗證輸入是否為空
    if (!studentId || !password) {
        messageDiv.style.display = 'block';
        messageDiv.className = 'message error';
        messageDiv.textContent = '請輸入帳號和密碼！';
        return;
    }

    // 模擬後端 API 請求
    try {
        const response = await fetch('http://localhost:3000/api/attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                studentId,
                password
            })
        });

        const result = await response.json();

        if (response.ok) {
            // 成功點名
            messageDiv.style.display = 'block';
            messageDiv.className = 'message success';
            messageDiv.textContent = `點名成功！${result.message}`;
        } else {
            // 點名失敗
            messageDiv.style.display = 'block';
            messageDiv.className = 'message error';
            messageDiv.textContent = `錯誤：${result.message}`;
        }
    } catch (error) {
        // 處理網絡錯誤
        messageDiv.style.display = 'block';
        messageDiv.className = 'message error';
        messageDiv.textContent = '伺服器無回應，請稍後再試！';
    }
}
