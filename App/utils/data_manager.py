import json
import hashlib
import os
import uuid
import shutil
import datetime
from decimal import Decimal, ROUND_HALF_UP  # Dùng Decimal cho tiền tệ

# --- Path Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
MENU_FILE = os.path.join(DATA_DIR, "menu.json")
TABLES_FILE = os.path.join(DATA_DIR, "tables.json")
RECEIPTS_FILE = os.path.join(DATA_DIR, "receipts.json")
RECEIPTS_PRINT_DIR = os.path.join(DATA_DIR, "printed_receipts")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.json")


# --- Helper Functions ---
def _ensure_dir():
    """Đảm bảo các thư mục dữ liệu tồn tại."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    if not os.path.exists(RECEIPTS_PRINT_DIR):
        os.makedirs(RECEIPTS_PRINT_DIR)


def _load_json(file_path, default_data=None):
    """Tải dữ liệu từ file JSON, tạo file nếu chưa có."""
    _ensure_dir()
    if not os.path.exists(file_path):
        if default_data is not None:
            _save_json(file_path, default_data)
        return default_data if default_data is not None else []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Cảnh báo: Lỗi đọc file {file_path}. Sử dụng dữ liệu mặc định.")
        return default_data if default_data is not None else []


def _save_json(file_path, data):
    """Lưu dữ liệu vào file JSON."""
    _ensure_dir()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Lỗi khi lưu file {file_path}: {e}")


def hash_password(password):
    """Mã hóa mật khẩu bằng SHA256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def copy_image_to_data(source_path):
    """Sao chép ảnh vào thư mục data/images và trả về đường dẫn tương đối."""
    if not source_path or not os.path.exists(source_path):
        return ""
    _ensure_dir()
    try:
        _, ext = os.path.splitext(source_path)
        filename = f"{uuid.uuid4()}{ext}"
        destination = os.path.join(IMAGES_DIR, filename)
        shutil.copy(source_path, destination)
        # Trả về đường dẫn tương đối từ thư mục App
        return os.path.join("data", "images", filename)
    except Exception as e:
        print(f"Lỗi khi sao chép ảnh: {e}")
        return ""


# --- User Management ---
def get_users():
    """Lấy danh sách người dùng, tạo mặc định nếu file không tồn tại."""
    # Giả định lương Staff 7.5tr/tháng / (8 giờ/ngày * 26 ngày/tháng)
    staff_hourly_rate = 7500000 / (8 * 26)

    default_users = [
        {
            "username": "admin",
            "password": hash_password("admin"),
            "role": "admin",
            "name": "Adminstrator",
            "address": "123 Main St",
            "gmail": "admin@example.com",
            "dob": "2000-01-01",
            "hourly_rate": 0.0,
        },
        {
            "username": "nhanvienA",
            "password": hash_password("123"),
            "role": "staff",
            "name": "Nhân Viên A",
            "address": "456 Side St",
            "gmail": "nhanvienA@example.com",
            "dob": "2002-05-10",
            "hourly_rate": round(staff_hourly_rate, -2),
        },
    ]
    return _load_json(USERS_FILE, default_users)


def add_user(user_data):
    """Thêm người dùng mới."""
    users = get_users()
    # Kiểm tra trùng username trước khi thêm (tùy chọn)
    if any(u["username"] == user_data["username"] for u in users):
        raise ValueError(f"Tên đăng nhập '{user_data['username']}' đã tồn tại.")
    users.append(user_data)
    _save_json(USERS_FILE, users)


def update_user(username, new_data):
    """Cập nhật thông tin người dùng."""
    users = get_users()
    user_found = False
    for user in users:
        if user["username"] == username:
            user.update(new_data)
            user_found = True
            break
    if user_found:
        _save_json(USERS_FILE, users)
    else:
        print(f"Cảnh báo: Không tìm thấy user '{username}' để cập nhật.")


def delete_user(username):
    """Xóa người dùng."""
    users = get_users()
    original_length = len(users)
    users = [u for u in users if u["username"] != username]
    if len(users) < original_length:
        _save_json(USERS_FILE, users)
    else:
        print(f"Cảnh báo: Không tìm thấy user '{username}' để xóa.")


# --- Menu Management ---
def get_menu():
    """Lấy danh sách món trong thực đơn."""
    return _load_json(MENU_FILE, [])


def add_menu_item(item_data):
    """Thêm món mới."""
    menu = get_menu()
    # Đảm bảo có ID
    if "id" not in item_data or not item_data["id"]:
        item_data["id"] = str(uuid.uuid4())
    menu.append(item_data)
    _save_json(MENU_FILE, menu)


def update_menu_item(item_id, new_data):
    """Cập nhật thông tin món ăn."""
    menu = get_menu()
    item_found = False
    for item in menu:
        if item.get("id") == item_id:
            item.update(new_data)
            item_found = True
            break
    if item_found:
        _save_json(MENU_FILE, menu)
    else:
        print(f"Cảnh báo: Không tìm thấy món với ID '{item_id}' để cập nhật.")


def delete_menu_item(item_id):
    """Xóa món ăn."""
    menu = get_menu()
    original_length = len(menu)
    menu = [item for item in menu if item.get("id") != item_id]
    if len(menu) < original_length:
        _save_json(MENU_FILE, menu)
    else:
        print(f"Cảnh báo: Không tìm thấy món với ID '{item_id}' để xóa.")


def migrate_menu_to_include_ids():
    """Đảm bảo tất cả món ăn đều có ID (cho dữ liệu cũ)."""
    menu = get_menu()
    updated = False
    for item in menu:
        if "id" not in item:
            item["id"] = str(uuid.uuid4())
            updated = True
    if updated:
        _save_json(MENU_FILE, menu)
        print("Đã cập nhật ID cho các món ăn cũ.")


# --- Table Management ---
def get_tables():
    """Lấy trạng thái các bàn."""
    default_tables = [
        {"id": i, "status": "Trống", "order": {}, "employee": None}
        for i in range(1, 16)
    ]
    return _load_json(TABLES_FILE, default_tables)


def save_tables(tables_data):
    """Lưu trạng thái các bàn."""
    _save_json(TABLES_FILE, tables_data)


# --- Receipt Management ---
def get_receipts():
    """Lấy danh sách hóa đơn đã lưu."""
    return _load_json(RECEIPTS_FILE, [])


def save_receipt(receipt_data):
    """Lưu một hóa đơn mới."""
    receipts = get_receipts()
    receipts.append(receipt_data)
    _save_json(RECEIPTS_FILE, receipts)


# --- Attendance Management ---
def get_attendance_records():
    """Lấy tất cả bản ghi chấm công."""
    return _load_json(ATTENDANCE_FILE, [])


def get_last_attendance(username):
    """Lấy bản ghi chấm công gần nhất của user."""
    records = get_attendance_records()
    user_records = [r for r in records if r["username"] == username]
    if not user_records:
        return None
    # Sắp xếp theo check_in_time giảm dần và lấy cái đầu tiên
    user_records.sort(key=lambda x: x.get("check_in_time", ""), reverse=True)
    return user_records[0]


def record_check_in(username):
    """Ghi nhận giờ check-in."""
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    last_record = get_last_attendance(username)
    if last_record and last_record.get("check_in_time", "").startswith(today_str):
        if not last_record.get("check_out_time"):
            raise ValueError("Bạn đã check-in hôm nay rồi nhưng chưa check-out.")

    new_record = {
        "id": str(uuid.uuid4()),
        "username": username,
        "check_in_time": now.isoformat(),
        "check_out_time": None,
    }

    records = get_attendance_records()
    records.append(new_record)
    _save_json(ATTENDANCE_FILE, records)
    return new_record


def record_check_out(username):
    """Ghi nhận giờ check-out."""
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    last_record = get_last_attendance(username)

    if not last_record:
        raise ValueError("Không tìm thấy bản ghi check-in nào.")
    if not last_record.get("check_in_time", "").startswith(today_str):
        raise ValueError("Bạn chưa check-in hôm nay.")
    if last_record.get("check_out_time"):
        raise ValueError("Bạn đã check-out hôm nay rồi.")

    records = get_attendance_records()
    record_updated = None
    for i in range(len(records) - 1, -1, -1):  # Duyệt ngược
        if records[i]["id"] == last_record["id"]:
            records[i]["check_out_time"] = now.isoformat()
            record_updated = records[i]  # Lưu lại bản ghi đã cập nhật
            break

    if not record_updated:
        raise ValueError("Không tìm thấy bản ghi check-in phù hợp để cập nhật.")

    _save_json(ATTENDANCE_FILE, records)
    return record_updated  # Trả về bản ghi đã được cập nhật


# --- Salary Calculation ---
def calculate_salary(username, start_date, end_date):
    """Tính tổng giờ làm và lương cho user trong khoảng thời gian."""
    user_data = next((u for u in get_users() if u["username"] == username), None)
    if not user_data:
        raise ValueError(f"Không tìm thấy người dùng: {username}")

    if user_data.get("role") == "admin":
        return {"total_hours": 0.0, "hourly_rate": 0.0, "total_salary": Decimal("0.0")}

    hourly_rate = Decimal(str(user_data.get("hourly_rate", 0.0)))
    all_records = get_attendance_records()
    total_duration = datetime.timedelta()

    for record in all_records:
        if record["username"] == username:
            try:
                check_in_str = record.get("check_in_time")
                check_out_str = record.get("check_out_time")

                if not check_in_str or not check_out_str:
                    continue  # Bỏ qua nếu thiếu giờ vào/ra

                check_in_time = datetime.datetime.fromisoformat(check_in_str)
                check_out_time = datetime.datetime.fromisoformat(check_out_str)
                record_date = check_in_time.date()

                # Chỉ tính các bản ghi trong khoảng thời gian
                if (
                    start_date <= record_date <= end_date
                    and check_out_time > check_in_time
                ):
                    duration = check_out_time - check_in_time
                    total_duration += duration
            except Exception as e:
                print(f"Bỏ qua bản ghi chấm công lỗi: {record.get('id', 'N/A')} - {e}")

    total_hours = Decimal(total_duration.total_seconds()) / Decimal(3600)
    total_salary = (total_hours * hourly_rate).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    return {
        "total_hours": round(float(total_hours), 2),
        "hourly_rate": float(hourly_rate),
        "total_salary": total_salary,
    }
