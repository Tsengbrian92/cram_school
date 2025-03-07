from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import mysql.connector
import bcrypt
import os
from datetime import datetime, timedelta


import logging
logging.basicConfig(level=logging.DEBUG)





app = Flask(__name__)
CORS(app)

# 設定 JWT
app.config["JWT_SECRET_KEY"] = os.getenv("STUDENT_JWT_SECRET", "student_secret_key")  
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5)

jwt = JWTManager(app)

# 資料庫配置
db_config = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "Aa0901155900",  # 替換為你的資料庫密碼
    "database": "studentif"  # 替換為你的資料庫名稱
}

@app.errorhandler(422)
def handle_unprocessable_entity(e):
    return jsonify({"message": "Unprocessable Entity", "error": str(e)}), 422

# 登入 API
@app.route('/api/t_login', methods=['POST'])
def teacher_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "請輸入帳號與密碼"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查詢教師帳號
        query = "SELECT password FROM t_account WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result and bcrypt.checkpw(password.encode('utf-8'), result['password'].encode('utf-8')):
            # 生成 Token
            token = create_access_token(identity=username)
            return jsonify({"access_token": token}), 200
        else:
            return jsonify({"message": "帳號或密碼錯誤"}), 401

    except Exception as e:
        return jsonify({"message": f"發生錯誤：{str(e)}"}), 500

    finally:
        cursor.close()
        connection.close()


# 🔹 教師驗證 API (確認 Token 是否有效)
@app.route('/api/teacher/verify', methods=['GET'])
@jwt_required()
def verify_teacher():
    current_user = get_jwt_identity()
    return jsonify({"message": "教師驗證成功", "username": current_user}), 200

@app.route('/api/get-max-students', methods=['GET'])
def get_max_students():
    class_code = request.args.get('classId')  # 這裡可能是 classId 或 class_code

    if not class_code:
        return jsonify({"message": "缺少 classId 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = "SELECT max_students FROM classes WHERE class_code = %s"
        cursor.execute(query, (class_code,))
        result = cursor.fetchone()

        if result:
            return jsonify({"max_students": result["max_students"]}), 200
        else:
            return jsonify({"message": "查無此班級"}), 404

    except Exception as e:
        return jsonify({"message": f"發生錯誤: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

   
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

@app.route('/api/get-class-students', methods=['GET'])
def get_class_students():
    class_code = request.args.get('class_code')

    if not class_code:
        return jsonify({"error": "缺少 class_code 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查詢班級學生表，獲取學生學號
        query = f"SELECT student_id, student_name, student_email, student_phone FROM class_{class_code}_students"
        cursor.execute(query)
        students = cursor.fetchall()

        return jsonify(students), 200

    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        return jsonify({"error": "伺服器錯誤，請稍後再試"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/api/get-non-class-students', methods=['GET'])
def get_non_class_students():
    class_code = request.args.get('class_code')

    if not class_code:
        return jsonify({"error": "缺少 class_code 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 1️⃣ 先獲取班級內的學生 ID
        query_get_class_students = f"SELECT student_id FROM class_{class_code}_students"
        cursor.execute(query_get_class_students)
        class_students = cursor.fetchall()
        class_student_ids = {student["student_id"] for student in class_students}  # 轉成 Set

        # 2️⃣ 查詢 `account` 表，排除班級內的學生
        query_get_all_students = "SELECT username AS student_id, name, email, phone FROM account"
        cursor.execute(query_get_all_students)
        all_students = cursor.fetchall()

        # 3️⃣ 過濾掉已經在班級內的學生
        non_class_students = [student for student in all_students if student["student_id"] not in class_student_ids]

        return jsonify(non_class_students), 200

    except Exception as e:
        return jsonify({"error": f"發生錯誤：{str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route('/api/update-class-students', methods=['POST'])
def update_class_students():
    data = request.json
    class_code = data.get('classCode')
    added_students = data.get('addedStudents', [])
    removed_students = data.get('removedStudents', [])

    if not class_code:
        return jsonify({"error": "缺少 class_code 參數"}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # **1️⃣ 處理新增的學生**
        for student in added_students:
            student_id = student['username']

            # 檢查是否已經在班級學生表
            cursor.execute(f"SELECT * FROM class_{class_code}_students WHERE student_id = %s", (student_id,))
            result = cursor.fetchone()
            
            if not result:
                # 插入學生到班級學生表
                insert_student_query = f"""
                INSERT INTO class_{class_code}_students (student_id, student_name, student_email, student_phone)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_student_query, (student_id, student['name'], student['email'], student['phone']))

            # 檢查是否已經在點名表
            cursor.execute(f"SELECT * FROM {class_code}_attendance WHERE student_id = %s", (student_id,))
            attendance_result = cursor.fetchone()

            if not attendance_result:
                # 插入學生到點名表（初始狀態為 `缺席`）
                add_attendance_query = f"""
                INSERT INTO {class_code}_attendance (student_id)
                VALUES (%s)
                """
                cursor.execute(add_attendance_query, (student_id,))

        # **2️⃣ 處理刪除的學生**
        for student in removed_students:
            student_id = student['username']

            # **從班級學生表刪除**
            delete_query = f"DELETE FROM class_{class_code}_students WHERE student_id = %s"
            cursor.execute(delete_query, (student_id,))

            # **從點名表刪除**
            delete_attendance_query = f"DELETE FROM {class_code}_attendance WHERE student_id = %s"
            cursor.execute(delete_attendance_query, (student_id,))

        # **3️⃣ 更新班級學生數**
        update_count_query = f"""
        UPDATE classes
        SET students_count = (SELECT COUNT(*) FROM class_{class_code}_students)
        WHERE class_code = %s
        """
        cursor.execute(update_count_query, (class_code,))

        connection.commit()
        return jsonify({"message": "班級學生資料更新成功！"}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({"message": f"發生錯誤：{str(e)}"}), 500

    finally:
        cursor.close()
        connection.close()


# 🔹 定義一週的日期對應
WEEKDAYS = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}

@app.route('/api/create-class', methods=['POST'])
def create_class():
    data = request.json

    class_code = data.get("class_code")
    class_name = data.get("class_name")
    teacher_name = data.get("teacher_name")
    max_students = data.get("max_students")
    class_count = data.get("class_count")
    start_date = data.get("start_date")
    schedule = data.get("schedule")  # 包含 { day, start_time, end_time }

    if not (class_code and class_name and teacher_name and max_students and class_count and start_date and schedule):
        return jsonify({"message": "缺少必要的參數"}), 400

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # **計算 end_date**
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = start_date_obj + timedelta(weeks=int(class_count))
        end_date = end_date_obj.strftime("%Y-%m-%d")

        # **1️⃣ 新增班級到 `classes` 資料表**
        insert_class_query = """
            INSERT INTO classes (class_code, class_name, teacher_name, max_students, class_count, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_class_query, (class_code, class_name, teacher_name, max_students, class_count, start_date, end_date))

        # **2️⃣ 新增課程時間表到 `class_schedule`**
        for entry in schedule:
            class_day = entry.get("day")
            start_time = entry.get("start_time", "00:00:00")
            end_time = entry.get("end_time", "00:00:00")

            if not class_day:
                return jsonify({"message": "缺少 class_day"}), 400

            insert_schedule_query = """
                INSERT INTO class_schedule (class_code, class_day, start_time, end_time)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_schedule_query, (class_code, class_day, start_time, end_time))

        # **3️⃣ 創建該班級的學生表 (`class_{class_code}_students`)**
        create_students_table_query = f"""
            CREATE TABLE IF NOT EXISTS `class_{class_code}_students` (
                student_id VARCHAR(255) NOT NULL,
                student_name VARCHAR(255),
                student_email VARCHAR(255),
                student_phone VARCHAR(20),
                PRIMARY KEY (student_id)
            )
        """
        cursor.execute(create_students_table_query)

        # **4️⃣ 建立點名表 (`{class_code}_attendance`)**
        attendance_columns = []
        for i in range(int(class_count)):
            class_date = (start_date_obj + timedelta(days=i * 7)).strftime("%Y_%m_%d")
            attendance_columns.append(f"`attendance_{class_date}` ENUM('出席', '遲到', '缺席') DEFAULT '缺席'")
            attendance_columns.append(f"`time_{class_date}` TIME")

        create_attendance_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{class_code}_attendance` (
                student_id VARCHAR(255) NOT NULL,
                {', '.join(attendance_columns)},
                PRIMARY KEY (student_id)
            )
        """
        cursor.execute(create_attendance_table_query)

        connection.commit()
        return jsonify({"message": "班級創建成功！"}), 201

    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        return jsonify({"message": f"資料庫錯誤：{str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)