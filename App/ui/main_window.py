import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QHBoxLayout,
    QFrame,
    QStackedWidget,
    QFormLayout,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt6.QtGui import QFont, QIcon
import datetime

from utils.data_manager import (
    get_tables,
    save_tables,
    update_user,
    hash_password,
    record_check_in,
    record_check_out,
    get_last_attendance,
)
from ui.order_dialog import OrderDialog
from ui.admin_panel import AdminPanel
from ui.login_dialog import LoginDialog


# (Lớp ChangePasswordDialog giữ nguyên)
class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đổi mật khẩu")
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.new_pass_input = QLineEdit()
        self.new_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.setStyleSheet(
            """QLineEdit {padding: 8px; border: 1px solid #ced4da; border-radius: 6px; background-color: #f8f9fa;} QLineEdit:focus {border-color: #007bff;}"""
        )
        form.addRow("Mật khẩu mới:", self.new_pass_input)
        form.addRow("Xác nhận mật khẩu mới:", self.confirm_pass_input)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def get_passwords(self):
        new_pass = self.new_pass_input.text()
        confirm_pass = self.confirm_pass_input.text()
        if not new_pass or not confirm_pass:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập cả hai trường.")
            return None
        if new_pass != confirm_pass:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu không khớp.")
            return None
        return new_pass


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle(f"Hệ thống Cafe - Nhân viên: {self.user_data['username']}")
        self.setGeometry(50, 50, 1300, 750)
        self.tables_data = get_tables()

        if self.user_data.get("role") == "admin":
            self.setup_admin_ui()
        else:
            self.setup_staff_ui()

        self.apply_stylesheet()
        self.update_tables_display()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timekeeping_clock)
        self.timer.start(1000)
        self.update_timekeeping_status()

    # (setup_staff_ui và setup_admin_ui giữ nguyên)
    def setup_staff_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        nav_panel = QFrame()
        nav_panel.setObjectName("navPanel")
        nav_panel.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(10, 20, 10, 10)
        nav_layout.setSpacing(10)
        app_title = QLabel("CafeManager")
        app_title.setObjectName("navTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(app_title)
        top_nav_widget = QWidget()
        top_nav_layout = QVBoxLayout(top_nav_widget)
        top_nav_layout.setContentsMargins(0, 0, 0, 0)
        top_nav_layout.setSpacing(10)
        top_nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tables_nav_button = QPushButton("🍽️  Sơ đồ bàn")
        self.tables_nav_button.setObjectName("navButton")
        self.tables_nav_button.setCheckable(True)
        self.timekeeping_nav_button = QPushButton("⏱️  Chấm công")
        self.timekeeping_nav_button.setObjectName("navButton")
        self.timekeeping_nav_button.setCheckable(True)
        self.account_nav_button = QPushButton("👤  Tài khoản")
        self.account_nav_button.setObjectName("navButton")
        self.account_nav_button.setCheckable(True)
        top_nav_layout.addWidget(self.tables_nav_button)
        top_nav_layout.addWidget(self.timekeeping_nav_button)
        top_nav_layout.addWidget(self.account_nav_button)
        nav_layout.addWidget(top_nav_widget)
        nav_layout.addStretch()
        self.logout_button = QPushButton("🚪  Đăng xuất")
        self.logout_button.setObjectName("navButton")
        self.logout_button.setProperty("role", "logout")
        self.logout_button.clicked.connect(self.logout_requested.emit)
        nav_layout.addWidget(self.logout_button)
        self.stacked_widget = QStackedWidget()
        self.tables_widget = self.create_tables_widget()
        self.timekeeping_widget = self.create_timekeeping_widget()
        self.account_info_widget = self.create_account_info_widget()
        self.stacked_widget.addWidget(self.tables_widget)
        self.stacked_widget.addWidget(self.timekeeping_widget)
        self.stacked_widget.addWidget(self.account_info_widget)
        main_layout.addWidget(nav_panel)
        main_layout.addWidget(self.stacked_widget, 1)
        self.tables_nav_button.clicked.connect(self.switch_to_tables)
        self.timekeeping_nav_button.clicked.connect(self.switch_to_timekeeping)
        self.account_nav_button.clicked.connect(self.switch_to_account)
        self.switch_to_tables()
        self.setCentralWidget(main_widget)

    def setup_admin_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        nav_panel = QFrame()
        nav_panel.setObjectName("navPanel")
        nav_panel.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(10, 20, 10, 10)
        nav_layout.setSpacing(10)
        app_title = QLabel("CafeManager")
        app_title.setObjectName("navTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(app_title)
        top_nav_widget = QWidget()
        top_nav_layout = QVBoxLayout(top_nav_widget)
        top_nav_layout.setContentsMargins(0, 0, 0, 0)
        top_nav_layout.setSpacing(10)
        top_nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tables_nav_button = QPushButton("🍽️  Sơ đồ bàn")
        self.tables_nav_button.setObjectName("navButton")
        self.tables_nav_button.setCheckable(True)
        self.admin_nav_button = QPushButton("⚙️  Bảng Quản lý")
        self.admin_nav_button.setObjectName("navButton")
        self.admin_nav_button.setCheckable(True)
        self.timekeeping_nav_button = QPushButton("⏱️  Chấm công")
        self.timekeeping_nav_button.setObjectName("navButton")
        self.timekeeping_nav_button.setCheckable(True)
        self.account_nav_button = QPushButton("👤  Tài khoản")
        self.account_nav_button.setObjectName("navButton")
        self.account_nav_button.setCheckable(True)
        top_nav_layout.addWidget(self.tables_nav_button)
        top_nav_layout.addWidget(self.admin_nav_button)
        top_nav_layout.addWidget(self.timekeeping_nav_button)
        top_nav_layout.addWidget(self.account_nav_button)
        nav_layout.addWidget(top_nav_widget)
        nav_layout.addStretch()
        self.logout_button = QPushButton("🚪  Đăng xuất")
        self.logout_button.setObjectName("navButton")
        self.logout_button.setProperty("role", "logout")
        self.logout_button.clicked.connect(self.logout_requested.emit)
        nav_layout.addWidget(self.logout_button)
        self.stacked_widget = QStackedWidget()
        self.tables_widget = self.create_tables_widget()
        self.admin_panel = AdminPanel()
        self.timekeeping_widget = self.create_timekeeping_widget()
        self.account_info_widget = self.create_account_info_widget()
        self.stacked_widget.addWidget(self.tables_widget)
        self.stacked_widget.addWidget(self.admin_panel)
        self.stacked_widget.addWidget(self.timekeeping_widget)
        self.stacked_widget.addWidget(self.account_info_widget)
        main_layout.addWidget(nav_panel)
        main_layout.addWidget(self.stacked_widget, 1)
        self.tables_nav_button.clicked.connect(self.switch_to_tables)
        self.admin_nav_button.clicked.connect(self.switch_to_admin)
        self.timekeeping_nav_button.clicked.connect(self.switch_to_timekeeping)
        self.account_nav_button.clicked.connect(self.switch_to_account)
        self.switch_to_tables()
        self.setCentralWidget(main_widget)

    # (Các hàm switch_to... giữ nguyên)
    def switch_to_tables(self):
        self.stacked_widget.setCurrentIndex(0)
        self.tables_nav_button.setChecked(True)
        if hasattr(self, "admin_nav_button"):
            self.admin_nav_button.setChecked(False)
        self.timekeeping_nav_button.setChecked(False)
        self.account_nav_button.setChecked(False)

    def switch_to_admin(self):
        self.stacked_widget.setCurrentIndex(1)
        self.tables_nav_button.setChecked(False)
        self.admin_nav_button.setChecked(True)
        self.timekeeping_nav_button.setChecked(False)
        self.account_nav_button.setChecked(False)
        if hasattr(self, "admin_panel"):
            self.admin_panel.refresh_data()

    def switch_to_timekeeping(self):
        index = 2 if self.user_data.get("role") == "admin" else 1
        self.stacked_widget.setCurrentIndex(index)
        self.tables_nav_button.setChecked(False)
        if hasattr(self, "admin_nav_button"):
            self.admin_nav_button.setChecked(False)
        self.timekeeping_nav_button.setChecked(True)
        self.account_nav_button.setChecked(False)
        self.update_timekeeping_status()

    def switch_to_account(self):
        index = 3 if self.user_data.get("role") == "admin" else 2
        self.stacked_widget.setCurrentIndex(index)
        self.tables_nav_button.setChecked(False)
        if hasattr(self, "admin_nav_button"):
            self.admin_nav_button.setChecked(False)
        self.timekeeping_nav_button.setChecked(False)
        self.account_nav_button.setChecked(True)

    # --- CẬP NHẬT: Trang Chấm công ---
    def create_timekeeping_widget(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        # --- SỬA LẠI: Bỏ margin trên, căn lề trên ---
        main_layout.setContentsMargins(25, 0, 25, 20)  # Bỏ margin top
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Căn lề trên
        # ----------------------------------------

        title_label = QLabel("Chấm công")
        title_label.setObjectName("viewTitle")
        main_layout.addWidget(title_label)

        # Đồng hồ
        self.clock_label = QLabel("HH:MM:SS")
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.clock_label)

        # Trạng thái
        self.status_label = QLabel("Trạng thái: Chưa check-in")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Nút Check In/Out
        self.check_in_out_button = QPushButton("Bắt đầu Check In")
        self.check_in_out_button.setObjectName("checkInOutButton")
        self.check_in_out_button.setMinimumHeight(60)  # Làm nút to hơn
        self.check_in_out_button.clicked.connect(self.handle_check_in_out)
        main_layout.addWidget(self.check_in_out_button, 0, Qt.AlignmentFlag.AlignCenter)

        # main_layout.addStretch() # Bỏ stretch nếu đã có AlignTop
        return widget

    # (Các hàm handle_check_in_out, update_timekeeping_status, update_timekeeping_clock giữ nguyên)
    def handle_check_in_out(self):
        username = self.user_data["username"]
        try:
            last_record = get_last_attendance(username)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            can_check_in = True
            if last_record and last_record["check_in_time"].startswith(today_str):
                if not last_record.get("check_out_time"):
                    record_check_out(username)
                    QMessageBox.information(
                        self,
                        "Thành công",
                        f"Check-out thành công lúc {datetime.datetime.now().strftime('%H:%M:%S')}",
                    )
                    can_check_in = False
            if can_check_in:
                record_check_in(username)
                QMessageBox.information(
                    self,
                    "Thành công",
                    f"Check-in thành công lúc {datetime.datetime.now().strftime('%H:%M:%S')}",
                )
        except ValueError as e:
            QMessageBox.warning(self, "Lỗi Chấm công", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Hệ thống", f"Lỗi không xác định: {e}")
        self.update_timekeeping_status()

    def update_timekeeping_status(self):
        if not hasattr(self, "check_in_out_button"):
            return
        username = self.user_data["username"]
        last_record = get_last_attendance(username)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        status_text = "Chưa check-in hôm nay"
        button_text = "Bắt đầu Check In"
        button_role = "checkin"
        if last_record and last_record["check_in_time"].startswith(today_str):
            check_in_dt = datetime.datetime.fromisoformat(last_record["check_in_time"])
            if not last_record.get("check_out_time"):
                status_text = f"Đã check-in lúc: {check_in_dt.strftime('%H:%M:%S')}"
                button_text = "Kết thúc Check Out"
                button_role = "checkout"
            else:
                check_out_dt = datetime.datetime.fromisoformat(
                    last_record["check_out_time"]
                )
                status_text = f"Đã hoàn thành ca: {check_in_dt.strftime('%H:%M')} - {check_out_dt.strftime('%H:%M')}"
                button_text = "Đã Check Out"
                button_role = "disabled"
        self.status_label.setText(f"Trạng thái: {status_text}")
        self.check_in_out_button.setText(button_text)
        self.check_in_out_button.setProperty("role", button_role)
        self.check_in_out_button.setEnabled(button_role != "disabled")
        self.check_in_out_button.style().unpolish(self.check_in_out_button)
        self.check_in_out_button.style().polish(self.check_in_out_button)

    def update_timekeeping_clock(self):
        if hasattr(self, "clock_label"):
            now = datetime.datetime.now()
            self.clock_label.setText(now.strftime("%H:%M:%S"))

    # (Các hàm create_account_info_widget, handle_save_info, handle_change_password giữ nguyên)
    def create_account_info_widget(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(25, 0, 25, 20)
        # Bỏ margin top
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Căn lề trên
        title_label = QLabel("Thông tin Tài khoản")
        title_label.setObjectName("viewTitle")
        main_layout.addWidget(title_label)
        form_wrapper = QFrame()
        form_wrapper.setObjectName("accountFormWrapper")
        form_wrapper.setFixedWidth(500)
        form_layout = QFormLayout(form_wrapper)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.acc_username_label = QLineEdit(self.user_data.get("username", "N/A"))
        self.acc_username_label.setReadOnly(True)
        self.acc_name_input = QLineEdit(self.user_data.get("name", "N/A"))
        self.acc_role_label = QLineEdit(self.user_data.get("role", "N/A"))
        self.acc_role_label.setReadOnly(True)
        self.acc_gmail_input = QLineEdit(self.user_data.get("gmail", "N/A"))
        self.acc_address_input = QLineEdit(self.user_data.get("address", "N/A"))
        self.acc_dob_input = QDateEdit()
        self.acc_dob_input.setDisplayFormat("yyyy-MM-dd")
        self.acc_dob_input.setCalendarPopup(True)
        dob_date = QDate.fromString(self.user_data.get("dob", ""), "yyyy-MM-dd")
        if dob_date.isValid():
            self.acc_dob_input.setDate(dob_date)
        else:
            self.acc_dob_input.setDate(QDate.currentDate())
        self.acc_username_label.setProperty("role", "readonly")
        self.acc_role_label.setProperty("role", "readonly")
        form_layout.addRow("Tên đăng nhập:", self.acc_username_label)
        form_layout.addRow("Họ và tên:", self.acc_name_input)
        form_layout.addRow("Vị trí:", self.acc_role_label)
        form_layout.addRow("Gmail:", self.acc_gmail_input)
        form_layout.addRow("Địa chỉ:", self.acc_address_input)
        form_layout.addRow("Ngày sinh:", self.acc_dob_input)
        main_layout.addWidget(form_wrapper)
        button_layout = QHBoxLayout()
        self.save_info_button = QPushButton("Lưu thay đổi")
        self.save_info_button.setObjectName("saveInfoButton")
        self.save_info_button.clicked.connect(self.handle_save_info)
        self.change_pass_button = QPushButton("Đổi mật khẩu")
        self.change_pass_button.setObjectName("changePasswordButton")
        self.change_pass_button.clicked.connect(self.handle_change_password)
        button_layout.addWidget(self.save_info_button)
        button_layout.addWidget(self.change_pass_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        # Bỏ addStretch() ở đây vì đã có AlignTop
        return widget

    def handle_save_info(self):
        try:
            new_data = self.user_data.copy()
            new_data["name"] = self.acc_name_input.text()
            new_data["gmail"] = self.acc_gmail_input.text()
            new_data["address"] = self.acc_address_input.text()
            new_data["dob"] = self.acc_dob_input.date().toString("yyyy-MM-dd")
            update_user(self.user_data["username"], new_data)
            self.user_data = new_data
            QMessageBox.information(
                self, "Thành công", "Cập nhật thông tin cá nhân thành công."
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật thông tin: {e}")

    def handle_change_password(self):
        dialog = ChangePasswordDialog(self)
        if dialog.exec():
            new_password = dialog.get_passwords()
            if new_password:
                try:
                    new_data = self.user_data.copy()
                    new_data["password"] = hash_password(new_password)
                    update_user(self.user_data["username"], new_data)
                    self.user_data["password"] = new_data["password"]
                    QMessageBox.information(
                        self, "Thành công", "Đổi mật khẩu thành công."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self, "Lỗi", f"Không thể cập nhật mật khẩu: {e}"
                    )

    # --- CẬP NHẬT: Trang Sơ đồ bàn ---
    def create_tables_widget(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        # --- SỬA LẠI: Bỏ margin trên, căn lề trên ---
        main_layout.setContentsMargins(25, 20, 25, 20)  # Bỏ margin top
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Căn lề trên
        # ----------------------------------------
        main_layout.setSpacing(20)

        title_label = QLabel("Tổng quan Sơ đồ bàn")
        title_label.setObjectName("viewTitle")
        main_layout.addWidget(title_label)

        self.tables_grid = QGridLayout()
        self.table_buttons = {}
        for table in self.tables_data:
            table_id = table["id"]
            button = QPushButton(f"Bàn {table_id}")
            button.setMinimumSize(130, 130)
            button.clicked.connect(
                lambda ch, t_id=table_id: self.open_order_dialog(t_id)
            )
            self.table_buttons[table_id] = button
            row = (table_id - 1) // 5
            col = (table_id - 1) % 5
            self.tables_grid.addWidget(button, row, col)

        main_layout.addLayout(self.tables_grid)
        # main_layout.addStretch() # Bỏ stretch nếu đã có AlignTop
        return widget

    # (update_tables_display và open_order_dialog giữ nguyên)
    def update_tables_display(self):
        self.tables_data = get_tables()
        for table in self.tables_data:
            if table["id"] not in self.table_buttons:
                continue
            button = self.table_buttons[table["id"]]
            status = table["status"]
            employee = table.get("employee", "Trống")
            button.setText(f"Bàn {table['id']}\n{status}\nNV: {employee}")
            if status == "Trống":
                button.setProperty("status", "empty")
            else:
                button.setProperty("status", "occupied")
            button.style().unpolish(button)
            button.style().polish(button)

    def open_order_dialog(self, table_id):
        table_index = next(
            (i for i, t in enumerate(self.tables_data) if t["id"] == table_id), None
        )
        if table_index is None:
            QMessageBox.critical(self, "Lỗi", f"Không tìm thấy dữ liệu bàn {table_id}.")
            return
        dialog = OrderDialog(
            self.tables_data[table_index], self.user_data["username"], self
        )
        if dialog.exec():
            save_tables(self.tables_data)
            self.update_tables_display()
            if hasattr(self, "admin_panel"):
                self.admin_panel.refresh_data()

    # (apply_stylesheet giữ nguyên)
    def apply_stylesheet(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #ffffff; font-family: Inter; }
            #viewTitle { font-size: 24px; font-weight: bold; color: #343a40; padding-bottom: 10px; }
            QPushButton[status] { color: white; font-size: 15px; font-weight: bold; border-radius: 12px; padding: 10px; line-height: 1.5; }
            QPushButton[status]:hover { border: 3px solid rgba(255, 255, 255, 0.7); }
            QPushButton[status="empty"] { background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #34d399, stop: 1 #10b981); border: 1px solid #059669; }
            QPushButton[status="occupied"] { background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #fb923c, stop: 1 #f97316); border: 1px solid #ea580c; }
            #navPanel { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
            #navTitle { font-size: 22px; font-weight: bold; color: #343a40; padding-bottom: 20px; }
            QPushButton#navButton { background: transparent; border: none; padding: 15px 20px; font-size: 15px; font-weight: bold; color: #495057; text-align: left; border-radius: 8px; }
            QPushButton#navButton:hover { background: #f1f3f5; }
            QPushButton#navButton:checked { background: #e9ecef; color: #007bff; }
            QPushButton#navButton[role="logout"] { color: #dc3545; }
            QPushButton#navButton[role="logout"]:hover { background: #f8d7da; }
            #accountFormWrapper { border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; }
            QFormLayout QLineEdit, QFormLayout QDateEdit { background-color: #ffffff; border: 1px solid #ced4da; padding: 8px; border-radius: 6px; }
            QFormLayout QLineEdit:focus, QFormLayout QDateEdit:focus { border-color: #007bff; }
            QFormLayout QLineEdit[role="readonly"] { background-color: #f8f9fa; }
            #saveInfoButton { background-color: #28a745; color: white; border: none; padding: 10px; margin-top: 15px; border-radius: 6px; font-weight: bold; width: 150px; }
            #saveInfoButton:hover { background-color: #218838; }
            #changePasswordButton { background-color: #007bff; color: white; border: none; padding: 10px; margin-top: 15px; border-radius: 6px; font-weight: bold; width: 150px; }
            #changePasswordButton:hover { background-color: #0056b3; }
            #clockLabel { font-size: 48px; font-weight: bold; color: #343a40; margin: 20px 0; }
            #statusLabel { font-size: 18px; color: #6c757d; margin-bottom: 30px; }
            #checkInOutButton { font-size: 18px; font-weight: bold; color: white; border: none; border-radius: 10px; padding: 15px 40px; }
            #checkInOutButton[role="checkin"] { background-color: #28a745; }
            #checkInOutButton[role="checkin"]:hover { background-color: #218838; }
            #checkInOutButton[role="checkout"] { background-color: #dc3545; }
            #checkInOutButton[role="checkout"]:hover { background-color: #c82333; }
            #checkInOutButton[role="disabled"] { background-color: #6c757d; color: #e0e0e0; }
        """
        )
