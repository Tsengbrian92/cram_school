from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
import mysql.connector
import os
import re
from datetime import datetime, timedelta

# 初始化 Flask 應用
app = Flask(__name__)

# 啟用跨域支持
CORS(app)

# 配置 JWT 密鑰
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_secret_key")  # 請替換為你的密鑰
jwt = JWTManager(app)


db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Aa0901155900",  # 替換為你的資料庫密碼
    "database": "studentif" # 替換為你的資料庫名稱
}


# 登入 API
@app.route('/api/login', methods=['POST'])
def login():
    # 獲取前端傳遞的 JSON 數據
    data = request.json
    username = data.get("username")
    password = data.get("password")

    # 在終端機顯示收到的帳號和密碼
    # print(f"收到的帳號: {username}, 密碼: {password}")
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # 查詢帳號和密碼是否正確
    query = "SELECT password FROM account WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    
   
    # 關閉資料庫連線
    cursor.close()
    connection.close()

    # 驗證帳號和密碼
    if result and result[0] == password:
        # 生成 JWT Token
        token = create_access_token(identity=username)
        return jsonify({"access_token": token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401
    
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    # 驗證所有欄位是否填寫
    missing_fields = [field for field, value in {
        "newUsername": username,
        "newPassword": password,
        "name": name,
        "email": email,
        "phone": phone
    }.items() if not value]

    if missing_fields:
        return jsonify({"message": f"以下欄位未填寫：{', '.join(missing_fields)}"}), 400
    # 驗證資料完整性
    if not all([username, password, name, email, phone]):
        return jsonify({"message": "請完整填寫所有欄位！"}), 400

    # 驗證帳號長度
    if len(username) < 5:
        return jsonify({"message": "帳號必須至少 5 個字以上！"}), 400
    # 驗證密碼格式
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    if not re.match(password_regex, password):
        return jsonify({"message": "密碼必須至少 8 個字以上，包含大小寫字母和數字！"}), 400
    # 驗證電子郵件格式
    email_regex = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    if not re.match(email_regex, email):
        return jsonify({"message": "請輸入正確的 Gmail 地址！"}), 400

    # 驗證電話號碼格式
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({"message": "請輸入正確的電話號碼！"}), 400

    try:
        # 連接到資料庫
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 檢查是否有重複的 username
        cursor.execute("SELECT id FROM account WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"message": "該帳號名稱已被使用，請更換！"}), 400

        # 檢查是否有重複的 email
        cursor.execute("SELECT id FROM account WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "該電子郵件已被使用，請更換！"}), 400

        # 檢查是否有重複的 phone
        cursor.execute("SELECT id FROM account WHERE phone = %s", (phone,))
        if cursor.fetchone():
            return jsonify({"message": "該電話號碼已被使用，請更換！"}), 400

        # 插入資料到資料庫
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = """
            INSERT INTO account (username, password, name, email, phone)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (username, password, name, email, phone))
        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({"message": "帳號創建成功"}), 201
    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        return jsonify({"message": "帳號創建失敗"}), 500


# 教師頁面登陸
@app.route('/api/t_login', methods=['POST'])
def t_login():
    # 獲取前端傳遞的 JSON 數據
    data = request.json
    username = data.get("username")
    password = data.get("password")

    # 在終端機顯示收到的帳號和密碼
    # print(f"收到的帳號: {username}, 密碼: {password}")
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # 查詢帳號和密碼是否正確
    query = "SELECT password FROM t_account WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    
   
    # 關閉資料庫連線
    cursor.close()
    connection.close()

    # 驗證帳號和密碼
    if result and result[0] == password:
        # 生成 JWT Token
        token = create_access_token(identity=username)
        return jsonify({"access_token": token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401



@app.route('/api/create-class', methods=['POST'])
def create_class_with_schedule():
    """
    創建班級並同時建立對應的課程時刻表和點名表。
    """
    data = request.json
    class_code = data.get("class_code")
    class_name = data.get("class_name")
    teacher_name = data.get("teacher_name")
    start_date = data.get("start_date")
    class_count = data.get("class_count")
    max_students = data.get("max_students")
    schedule = data.get("schedule")

    # 檢查必填字段
    if not all([class_code, class_name, teacher_name, start_date, class_count, max_students, schedule]):
        return jsonify({"message": "請完整填寫所有欄位！"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 確保 class_count 是整數
        class_count = int(class_count)

        # 計算結束日期
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = start_date_obj + timedelta(weeks=class_count - 1)
        end_date = end_date_obj.strftime("%Y-%m-%d")

        # 插入班級資料
        query_class = """
        INSERT INTO classes (class_code, class_name, teacher_name, start_date, end_date, class_count, students_count, max_students)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_class, (class_code, class_name, teacher_name, start_date, end_date, class_count, 0, max_students))

        # 插入課程時刻表資料
        query_schedule = """
        INSERT INTO class_schedule (class_code, class_day, class_time)
        VALUES (%s, %s, %s)
        """
        for item in schedule:
            cursor.execute(query_schedule, (class_code, item["day"], item["time"]))

        # 創建點名表
        create_attendance_table(cursor, class_code, start_date, class_count)
        create_class_students_table(cursor, class_code)
        connection.commit()
        return jsonify({"message": "班級與時刻表創建成功！"}), 201

    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400

    except mysql.connector.Error as err:
        return jsonify({"message": f"資料庫錯誤: {err}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()




def create_class_students_table(cursor, class_code):
    """
    根據班級代碼創建學生表
    """
    table_name = f"class_{class_code}_students"

    create_table_query = f"""
    CREATE TABLE {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id VARCHAR(20) NOT NULL UNIQUE,
        student_name VARCHAR(100) NOT NULL,
        student_email VARCHAR(100) NOT NULL,
        student_phone VARCHAR(15),
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_query)

def create_attendance_table(cursor, class_code, start_date, class_count):
    """
    創建點名表，基於開課日期和課程堂數。
    """
    try:
        # 確保 class_count 是整數
        class_count = int(class_count)

        # 將 start_date 轉換為日期類型
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(class_count):
            # 計算每堂課的日期
            current_date = (start_date_obj + timedelta(days=i * 7)).strftime("%Y_%m_%d")

            # 動態生成列名
            attendance_column = f"`attendance_{current_date}` ENUM('出席', '遲到', '缺席') DEFAULT '缺席'"
            time_column = f"`time_{current_date}` TIME"

            # 創建表格（如果尚未存在）
            query_create = f"""
            CREATE TABLE IF NOT EXISTS `{class_code}_attendance` (
                student_id INT NOT NULL,
                {attendance_column},
                {time_column},
                PRIMARY KEY (student_id, {attendance_column.split(' ')[0]})
            )
            """
            cursor.execute(query_create)

    except ValueError:
        raise ValueError("class_count 必須是可轉換為整數的值！")


   
@app.route('/api/get-classes', methods=['GET'])
def get_classes():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT class_code AS id, class_name AS name, teacher_name AS teacher, students_count AS students FROM classes"
        cursor.execute(query)
        classes = cursor.fetchall()

        return jsonify(classes), 200

    except mysql.connector.Error as err:
        return jsonify({"message": f"資料庫錯誤: {err}"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/get-class-info', methods=['GET'])
def get_class_info():
    # 獲取前端傳遞的 classId
    class_id = request.args.get('classId')

    if not class_id:
        return jsonify({"error": "缺少 classId 參數"}), 400

    try:
        # 建立資料庫連線
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查詢班級資訊
        query = """
        SELECT * FROM classes WHERE class_code = %s
        """
        cursor.execute(query, (class_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "班級不存在"}), 404

        # 返回班級資訊
        return jsonify({
            "class_name": result['class_name'],
            "teacher_name": result['teacher_name'],
            "start_date": result['start_date'],
            "end_date": result['end_date'],
            "students_count": result['students_count'],
            "max_students": result['max_students']
        })

    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

    finally:
        # 關閉連線
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/get-students', methods=['GET'])
def get_students():
    class_code = request.args.get('classId')
    if not class_code:
        return jsonify({"message": "班級代碼缺失"}), 400

    table_name = f"class_{class_code}_students"

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM `{table_name}`"
        cursor.execute(query)
        students = cursor.fetchall()

        if not students:
            return jsonify({"message": "目前無學生", "students": []})

        return jsonify({"students": students})
    except mysql.connector.Error as err:
        return jsonify({"message": f"資料庫錯誤: {err}"}), 500
    except Exception as e:
        return jsonify({"message": f"伺服器錯誤: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
