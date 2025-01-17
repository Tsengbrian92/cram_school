from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 資料庫配置
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Aa0901155900",  # 替換為你的資料庫密碼
    "database": "studentif"  # 替換為你的資料庫名稱
}

@app.route('/api/register', methods=['POST'])
def register():
    # 接收前端傳遞的資料
    data = request.json
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    # 驗證資料是否完整
    if not all([username, password, name, email, phone]):
        return jsonify({"message": "請完整填寫所有欄位！"}), 400

    # 驗證電子郵件格式
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    if not re.match(email_regex, email):
        return jsonify({"message": "請輸入正確的 Gmail 地址！"}), 400

    try:
        # 連接到 MySQL 資料庫
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 插入資料到 account 表
        query = """
            INSERT INTO account (username, password, name, email, phone)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (username, password, name, email, phone))
        connection.commit()

        # 關閉資料庫連接
        cursor.close()
        connection.close()

        return jsonify({"message": "帳號創建成功"}), 201
    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        return jsonify({"message": "帳號創建失敗"}), 500

if __name__ == '__main__':
    app.run(debug=True)
