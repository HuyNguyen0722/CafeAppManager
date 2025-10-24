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
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt6.QtGui import QFont, QIcon
import datetime
import traceback
import copy  # Import copy for deepcopy

# --- Cấu hình Matplotlib backend ---
import matplotlib

try:
    matplotlib.use("QtAgg")  # Tự động chọn Qt5/Qt6
    print("Debug: Đã cấu hình Matplotlib backend thành công.")
except ImportError:
    print("LỖI: Không thể cấu hình Matplotlib backend. Biểu đồ có thể không hoạt động.")
# ------------------------------------

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

# Import AdminPanel SAU KHI cấu hình matplotlib
from ui.admin_panel import AdminPanel
from ui.login_dialog import LoginDialog


# --- Dialog đổi mật khẩu ---
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
            """
            QLineEdit {padding: 8px; border: 1px solid #ced4da; border-radius: 6px; background-color: #f8f9fa;}
            QLineEdit:focus {border-color: #007bff;}
        """
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


# --- Cửa sổ chính ---
class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, user_data):
        super().__init__()
        print("Debug: Bắt đầu MainWindow.__init__")
        self.user_data = user_data
        self.setWindowTitle(
            f"Hệ thống Cafe - Nhân viên: {self.user_data.get('username','N/A')}"
        )
        self.setGeometry(100, 100, 1300, 750)

        try:
            # tables_data chỉ dùng để khởi tạo create_tables_widget lần đầu
            # update_tables_display sẽ tải lại dữ liệu thật
            self.tables_data = get_tables()
            print("Debug: Tải dữ liệu bàn ban đầu thành công.")
        except Exception as e:
            print(f"LỖI nghiêm trọng khi tải dữ liệu bàn ban đầu: {e}")
            QMessageBox.critical(
                self,
                "Lỗi Dữ liệu",
                f"Không thể tải dữ liệu bàn: {e}. Vui lòng kiểm tra file tables.json.",
            )
            self.tables_data = []  # Khởi tạo rỗng

        # --- Setup UI ---
        role = self.user_data.get("role")
        print(f"Debug: Role người dùng: {role}")
        if role == "admin":
            print("Debug: Gọi setup_admin_ui()...")
            self.setup_admin_ui()
            print("Debug: setup_admin_ui() hoàn thành.")
        else:
            print("Debug: Gọi setup_staff_ui()...")
            self.setup_staff_ui()
            print("Debug: setup_staff_ui() hoàn thành.")

        print("Debug: Áp dụng stylesheet...")
        self.apply_stylesheet()
        print("Debug: Cập nhật hiển thị bàn (lần đầu)...")
        self.update_tables_display()  # Cập nhật và tạo nút lần đầu

        # --- Timer cho đồng hồ chấm công ---
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_timekeeping_clock)
        self.clock_timer.start(1000)

        # --- Timer để tự động refresh bàn (cho đơn online) ---
        self.table_refresh_timer = QTimer(self)
        self.table_refresh_timer.timeout.connect(self.update_tables_display)
        self.table_refresh_timer.start(5000)  # 5000 mili-giây = 5 giây
        print("Debug: Đã khởi động timer 5s để refresh bàn.")

        self.update_timekeeping_status()  # Cập nhật trạng thái chấm công
        print("Debug: Kết thúc MainWindow.__init__")

    # --- Setup UI chung cho Sidebar và StackedWidget ---
    def _setup_base_ui(self):
        """Tạo cấu trúc UI cơ bản dùng chung cho admin và staff."""
        print("Debug: Bắt đầu _setup_base_ui")
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

        self.top_nav_widget = QWidget()
        self.top_nav_layout = QVBoxLayout(self.top_nav_widget)
        self.top_nav_layout.setContentsMargins(0, 0, 0, 0)
        self.top_nav_layout.setSpacing(10)
        self.top_nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        nav_layout.addWidget(self.top_nav_widget)

        nav_layout.addStretch()

        self.logout_button = QPushButton("🚪  Đăng xuất")
        self.logout_button.setObjectName("navButton")
        self.logout_button.setProperty("role", "logout")
        self.logout_button.clicked.connect(self.logout_requested.emit)
        nav_layout.addWidget(self.logout_button)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(nav_panel)
        main_layout.addWidget(self.stacked_widget, 1)

        self.setCentralWidget(main_widget)
        print("Debug: Kết thúc _setup_base_ui")

    # --- Setup UI cho Staff ---
    def setup_staff_ui(self):
        self._setup_base_ui()
        print("Debug: Tạo nút điều hướng Staff...")
        self.tables_nav_button = QPushButton("🍽️  Sơ đồ bàn")
        self.tables_nav_button.setObjectName("navButton")
        self.tables_nav_button.setCheckable(True)
        self.timekeeping_nav_button = QPushButton("⏱️  Chấm công")
        self.timekeeping_nav_button.setObjectName("navButton")
        self.timekeeping_nav_button.setCheckable(True)
        self.account_nav_button = QPushButton("👤  Tài khoản")
        self.account_nav_button.setObjectName("navButton")
        self.account_nav_button.setCheckable(True)
        self.top_nav_layout.addWidget(self.tables_nav_button)
        self.top_nav_layout.addWidget(self.timekeeping_nav_button)
        self.top_nav_layout.addWidget(self.account_nav_button)

        print("Debug: Tạo các trang Staff...")
        self.tables_widget = self.create_tables_widget()
        self.timekeeping_widget = self.create_timekeeping_widget()
        self.account_info_widget = self.create_account_info_widget()

        print("Debug: Thêm trang vào StackedWidget Staff...")
        self.stacked_widget.addWidget(self.tables_widget)  # Index 0
        self.stacked_widget.addWidget(self.timekeeping_widget)  # Index 1
        self.stacked_widget.addWidget(self.account_info_widget)  # Index 2

        print("Debug: Kết nối signal nút Staff...")
        self.tables_nav_button.clicked.connect(self.switch_to_tables)
        self.timekeeping_nav_button.clicked.connect(self.switch_to_timekeeping)
        self.account_nav_button.clicked.connect(self.switch_to_account)
        self.switch_to_tables()

    # --- Setup UI cho Admin ---
    def setup_admin_ui(self):
        self._setup_base_ui()
        print("Debug: Tạo nút điều hướng Admin...")
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
        self.top_nav_layout.addWidget(self.tables_nav_button)
        self.top_nav_layout.addWidget(self.admin_nav_button)
        self.top_nav_layout.addWidget(self.timekeeping_nav_button)
        self.top_nav_layout.addWidget(self.account_nav_button)

        print("Debug: Tạo các trang Admin...")
        self.tables_widget = self.create_tables_widget()
        try:
            print("Debug: Khởi tạo AdminPanel...")
            self.admin_panel = AdminPanel(self)  # Pass self
            print("Debug: Khởi tạo AdminPanel thành công.")
        except Exception as e:
            print(f"LỖI khi khởi tạo AdminPanel: {e}")
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Lỗi AdminPanel",
                f"Không thể khởi tạo bảng quản lý: {e}\nỨng dụng có thể không hoạt động đúng.",
            )
            self.admin_panel = QWidget()
            layout = QVBoxLayout(self.admin_panel)
            layout.addWidget(QLabel("Lỗi tải Bảng Quản lý!"))

        self.timekeeping_widget = self.create_timekeeping_widget()
        self.account_info_widget = self.create_account_info_widget()

        print("Debug: Thêm trang vào StackedWidget Admin...")
        try:
            self.stacked_widget.addWidget(self.tables_widget)  # Index 0
            print("Debug:   + Đã thêm tables_widget")
            self.stacked_widget.addWidget(self.admin_panel)  # Index 1
            print("Debug:   + Đã thêm admin_panel")
            self.stacked_widget.addWidget(self.timekeeping_widget)  # Index 2
            print("Debug:   + Đã thêm timekeeping_widget")
            self.stacked_widget.addWidget(self.account_info_widget)  # Index 3
            print("Debug: Đã thêm xong các trang vào StackedWidget.")
        except Exception as e:
            print(f"LỖI khi thêm widget vào StackedWidget: {e}")
            traceback.print_exc()
            QMessageBox.critical(
                self, "Lỗi UI", f"Lỗi khi thêm trang vào giao diện: {e}"
            )
            return

        print("Debug: Kết nối signal nút Admin...")
        try:
            self.tables_nav_button.clicked.connect(self.switch_to_tables)
            print("Debug:   + Kết nối xong tables_nav_button")
            self.admin_nav_button.clicked.connect(self.switch_to_admin)
            print("Debug:   + Kết nối xong admin_nav_button")
            self.timekeeping_nav_button.clicked.connect(self.switch_to_timekeeping)
            print("Debug:   + Kết nối xong timekeeping_nav_button")
            self.account_nav_button.clicked.connect(self.switch_to_account)
            print("Debug: Đã kết nối xong signal các nút.")
        except Exception as e:
            print(f"LỖI khi kết nối signal nút: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi UI", f"Lỗi khi cài đặt nút bấm: {e}")
            return

        print("Debug: Gọi switch_to_tables() lần đầu...")
        try:
            self.switch_to_tables()  # Hiển thị trang đầu tiên
            print("Debug: Gọi switch_to_tables() thành công.")
        except Exception as e:
            print(f"LỖI khi gọi switch_to_tables() lần đầu: {e}")
            traceback.print_exc()
            QMessageBox.critical(
                self, "Lỗi UI", f"Lỗi khi hiển thị trang đầu tiên: {e}"
            )
            return

        print("Debug: setup_admin_ui() hoàn thành.")

    # --- Chuyển đổi giữa các trang ---
    def _switch_page(self, index, button_to_check):
        """Hàm helper để chuyển trang và cập nhật trạng thái nút."""
        if hasattr(self, "stacked_widget") and self.stacked_widget:
            self.stacked_widget.setCurrentIndex(index)

        buttons = [
            "tables_nav_button",
            "admin_nav_button",
            "timekeeping_nav_button",
            "account_nav_button",
        ]
        for btn_name in buttons:
            button = getattr(self, btn_name, None)
            if button:
                button.setChecked(btn_name == button_to_check)

    def switch_to_tables(self):
        self._switch_page(0, "tables_nav_button")

    def switch_to_admin(self):
        if hasattr(self, "admin_panel"):
            self._switch_page(1, "admin_nav_button")
            if self.admin_panel and isinstance(self.admin_panel, AdminPanel):
                self.admin_panel.refresh_data()

    def switch_to_timekeeping(self):
        index = 2 if self.user_data.get("role") == "admin" else 1
        self._switch_page(index, "timekeeping_nav_button")
        self.update_timekeeping_status()

    def switch_to_account(self):
        index = 3 if self.user_data.get("role") == "admin" else 2
        self._switch_page(index, "account_nav_button")

    # --- Trang Chấm công ---
    def create_timekeeping_widget(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(25, 0, 25, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("Chấm công")
        title_label.setObjectName("viewTitle")
        main_layout.addWidget(title_label)

        self.clock_label = QLabel("HH:MM:SS")
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.clock_label)

        self.status_label = QLabel("Trạng thái: Đang tải...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.check_in_out_button = QPushButton("...")
        self.check_in_out_button.setObjectName("checkInOutButton")
        self.check_in_out_button.setMinimumHeight(60)
        self.check_in_out_button.clicked.connect(self.handle_check_in_out)
        main_layout.addWidget(self.check_in_out_button, 0, Qt.AlignmentFlag.AlignCenter)

        return widget

    def handle_check_in_out(self):
        username = self.user_data.get("username")
        if not username:
            QMessageBox.critical(self, "Lỗi", "Không thể xác định người dùng.")
            return
        try:
            last_record = get_last_attendance(username)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            is_checked_in_today = last_record and last_record.get(
                "check_in_time", ""
            ).startswith(today_str)
            is_checked_out = is_checked_in_today and last_record.get("check_out_time")

            if is_checked_in_today and not is_checked_out:
                record_check_out(username)
                QMessageBox.information(
                    self,
                    "Thành công",
                    f"Check-out thành công lúc {datetime.datetime.now().strftime('%H:%M:%S')}",
                )
            else:
                record_check_in(username)
                QMessageBox.information(
                    self,
                    "Thành công",
                    f"Check-in thành công lúc {datetime.datetime.now().strftime('%H:%M:%S')}",
                )

        except ValueError as e:
            QMessageBox.warning(self, "Lỗi Chấm công", str(e))
        except Exception as e:
            QMessageBox.critical(
                self, "Lỗi Hệ thống", f"Lỗi không xác định khi chấm công: {e}"
            )
            traceback.print_exc()

        self.update_timekeeping_status()

    def update_timekeeping_status(self):
        if not hasattr(self, "check_in_out_button") or not self.check_in_out_button:
            return
        username = self.user_data.get("username")
        if not username:
            return

        status_text = "Chưa check-in hôm nay"
        button_text = "Bắt đầu Check In"
        button_role = "checkin"
        try:
            last_record = get_last_attendance(username)
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            if last_record and last_record.get("check_in_time", "").startswith(
                today_str
            ):
                check_in_dt = datetime.datetime.fromisoformat(
                    last_record["check_in_time"]
                )
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
        except (ValueError, TypeError):
            status_text = "Lỗi dữ liệu chấm công"
            button_role = "disabled"
            print(f"Lỗi: Không thể phân tích thời gian từ bản ghi cuối của {username}")
        except Exception as e:
            print(f"Lỗi khi lấy trạng thái chấm công: {e}")
            status_text = "Lỗi khi tải trạng thái"
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

    # --- Trang Tài khoản ---
    def create_account_info_widget(self):
        print("Debug:   Bắt đầu create_account_info_widget")
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(25, 0, 25, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("Thông tin Tài khoản")
        title_label.setObjectName("viewTitle")
        main_layout.addWidget(title_label)

        form_wrapper = QFrame()
        form_wrapper.setObjectName("accountFormWrapper")
        form_wrapper.setFixedWidth(500)
        form_layout = QFormLayout(form_wrapper)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        try:
            print("Debug:       Tạo acc_username_label")
            self.acc_username_label = QLineEdit(self.user_data.get("username", "N/A"))
            self.acc_username_label.setReadOnly(True)
            self.acc_username_label.setProperty("role", "readonly")
            form_layout.addRow("Tên đăng nhập:", self.acc_username_label)

            print("Debug:       Tạo acc_name_input")
            self.acc_name_input = QLineEdit(self.user_data.get("name", "N/A"))
            form_layout.addRow("Họ và tên:", self.acc_name_input)

            print("Debug:       Tạo acc_role_label")
            self.acc_role_label = QLineEdit(self.user_data.get("role", "N/A"))
            self.acc_role_label.setReadOnly(True)
            self.acc_role_label.setProperty("role", "readonly")
            form_layout.addRow("Vị trí:", self.acc_role_label)

            print("Debug:       Tạo acc_gmail_input")
            self.acc_gmail_input = QLineEdit(self.user_data.get("gmail", "N/A"))
            form_layout.addRow("Gmail:", self.acc_gmail_input)

            print("Debug:       Tạo acc_address_input")
            self.acc_address_input = QLineEdit(self.user_data.get("address", "N/A"))
            form_layout.addRow("Địa chỉ:", self.acc_address_input)

            print("Debug:       Tạo acc_dob_input (QDateEdit)")
            self.acc_dob_input = QDateEdit()
            self.acc_dob_input.setDisplayFormat("yyyy-MM-dd")
            self.acc_dob_input.setCalendarPopup(True)
            dob_str = self.user_data.get("dob", "")
            print(f"Debug:         dob string from user_data: '{dob_str}'")
            dob_date = QDate.fromString(dob_str, "yyyy-MM-dd")
            if dob_date.isValid():
                print(
                    f"Debug:         dob_date hợp lệ, setDate: {dob_date.toString('yyyy-MM-dd')}"
                )
                self.acc_dob_input.setDate(dob_date)
            else:
                print(f"Debug:         dob_date KHÔNG hợp lệ. Đặt ngày hiện tại.")
                self.acc_dob_input.setDate(QDate.currentDate())
            form_layout.addRow("Ngày sinh:", self.acc_dob_input)
            print("Debug:       Đã thêm dob vào form.")

        except Exception as e:
            print(f"LỖI trong khi tạo input field của account_info: {e}")
            traceback.print_exc()
            error_label = QLabel(f"Lỗi tạo trường nhập liệu:\n{e}")
            main_layout.addWidget(error_label)
            return widget

        main_layout.addWidget(form_wrapper)

        # --- Nút bấm ---
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

        print("Debug:   Kết thúc create_account_info_widget")
        return widget

    def handle_save_info(self):
        try:
            username = self.user_data.get("username")
            if not username:
                raise ValueError("Không thể xác định username để cập nhật.")
            new_data = self.user_data.copy()
            new_data["name"] = self.acc_name_input.text()
            new_data["gmail"] = self.acc_gmail_input.text()
            new_data["address"] = self.acc_address_input.text()
            new_data["dob"] = self.acc_dob_input.date().toString("yyyy-MM-dd")
            update_user(username, new_data)
            self.user_data = new_data
            QMessageBox.information(
                self, "Thành công", "Cập nhật thông tin cá nhân thành công."
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật thông tin: {e}")
            traceback.print_exc()

    def handle_change_password(self):
        dialog = ChangePasswordDialog(self)
        if dialog.exec():
            new_password = dialog.get_passwords()
            if new_password:
                try:
                    username = self.user_data.get("username")
                    if not username:
                        raise ValueError("Không thể xác định username để đổi mật khẩu.")
                    new_data = self.user_data.copy()
                    new_data["password"] = hash_password(new_password)
                    update_user(username, new_data)
                    self.user_data["password"] = new_data["password"]
                    QMessageBox.information(
                        self, "Thành công", "Đổi mật khẩu thành công."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self, "Lỗi", f"Không thể cập nhật mật khẩu: {e}"
                    )
                    traceback.print_exc()

    # --- CẬP NHẬT: Trang Sơ đồ bàn ---
    def create_tables_widget(self):
        """Chỉ tạo layout và dict. Việc điền nút sẽ do update_tables_display làm."""
        print("Debug:   Bắt đầu create_tables_widget (chỉ tạo khung)")
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(25, 0, 25, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(20)

        title_label = QLabel("Tổng quan Sơ đồ bàn")
        title_label.setObjectName("viewTitle")
        main_layout.addWidget(title_label)

        # Lưới bàn
        self.tables_grid = QGridLayout()
        self.tables_grid.setSpacing(20)
        main_layout.addLayout(self.tables_grid)

        # Khởi tạo dict trống, nó sẽ được điền trong update_tables_display
        self.table_buttons = {}

        print("Debug:   Kết thúc create_tables_widget (chỉ tạo khung)")
        return widget

    def update_tables_display(self):
        """Đọc file JSON, xóa và TẠO LẠI TOÀN BỘ nút bấm."""
        print("Debug: Bắt đầu update_tables_display (LÀM MỚI TOÀN BỘ)...")
        try:
            self.tables_data = get_tables()  # Lấy dữ liệu mới nhất
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi tải lại dữ liệu bàn: {e}")
            QMessageBox.critical(
                self, "Lỗi Dữ Liệu", f"Không thể tải lại dữ liệu bàn: {e}."
            )
            return

        if not hasattr(self, "tables_grid"):
            print("Lỗi: tables_grid chưa được tạo.")
            return

        # --- XÓA SẠCH NÚT CŨ ---
        # 1. Xóa khỏi dict và deleteLater
        for button in self.table_buttons.values():
            button.deleteLater()
        self.table_buttons.clear()

        # 2. Xóa widget khỏi layout
        while self.tables_grid.count():
            item = self.tables_grid.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        # ------------------------

        print("Debug: Đã xóa nút cũ. Bắt đầu tạo nút mới...")

        row, col = 0, 0
        MAX_COLS = 5

        # Sắp xếp lại: Bàn 1-12 trước, sau đó mới đến các mục 'takeaway'
        table_items = sorted(
            [t for t in self.tables_data if isinstance(t.get("id"), int)],
            key=lambda x: x["id"],
        )
        takeaway_items = sorted(
            [t for t in self.tables_data if str(t.get("id")).startswith("takeaway")],
            key=lambda x: str(x.get("id")),  # Sắp xếp theo 'takeaway1', 'takeaway2'
        )

        all_items_to_display = table_items + takeaway_items

        for table_item_data in all_items_to_display:
            item_id = table_item_data.get("id")
            if item_id is None:
                continue

            button_text = ""
            object_name = ""
            minimum_size = (130, 130)

            status = table_item_data.get("status", "Lỗi")
            employee = table_item_data.get("employee", None)
            order = table_item_data.get("order", {})
            order_count = len(order) if isinstance(order, dict) else 0

            if str(item_id).startswith("takeaway"):
                object_name = "takeawayButtonGrid"
                button_text = f"🥡 {table_item_data.get('name', 'Mang về')} ({item_id})"
                if order_count > 0:
                    button_text += f"\n{status}: {order_count} món\nNV: {employee if employee else 'Trống'}"
                else:
                    # Nếu không có đơn, reset về Sẵn sàng
                    button_text += f"\nSẵn sàng\nNV: Trống"
                    table_item_data["status"] = "Sẵn sàng"  # Tự sửa lỗi status

            elif isinstance(item_id, int):
                object_name = "tableButton"
                button_text = (
                    f"Bàn {item_id}\n{status}\nNV: {employee if employee else 'Trống'}"
                )
            else:
                continue  # Bỏ qua ID lạ

            button = QPushButton(button_text)
            button.setObjectName(object_name)
            button.setMinimumSize(minimum_size[0], minimum_size[1])
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            # Dùng lambda với t_id=item_id để cố định giá trị
            button.clicked.connect(
                lambda ch, t_id=item_id: self.open_order_dialog(t_id)
            )

            # Set style properties
            if object_name == "takeawayButtonGrid":
                if status == "Sẵn sàng" or order_count == 0:
                    button.setProperty("hasOrder", False)
                else:  # "Chờ xử lý"
                    button.setProperty("hasOrder", True)
            elif object_name == "tableButton":
                if status == "Trống":
                    button.setProperty("status", "empty")
                else:
                    button.setProperty("status", "occupied")

            button.style().unpolish(button)
            button.style().polish(button)

            self.table_buttons[item_id] = button  # Thêm nút mới vào dict
            self.tables_grid.addWidget(button, row, col)

            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

        print(
            f"Debug: Kết thúc update_tables_display. Đã tạo {len(self.table_buttons)} nút."
        )

    def open_order_dialog(self, table_id):
        print(f"Debug: Mở OrderDialog cho ID: {table_id}")
        table_data_ref = next(
            (t for t in self.tables_data if t.get("id") == table_id), None
        )
        if table_data_ref is None:
            QMessageBox.critical(
                self, "Lỗi", f"Không tìm thấy dữ liệu cho ID '{table_id}'."
            )
            return

        table_data_copy = copy.deepcopy(table_data_ref)
        dialog = OrderDialog(
            table_data_copy, self.user_data.get("username", "N/A"), self
        )

        if dialog.exec():  # Chỉ cập nhật nếu bấm OK/Thanh toán
            print(f"Debug: OrderDialog cho {table_id} đã đóng với Accepted.")
            updated = False
            for i, t in enumerate(self.tables_data):
                if t.get("id") == table_id:
                    self.tables_data[i] = table_data_copy  # Ghi đè dict gốc
                    updated = True
                    break
            if updated:
                try:
                    save_tables(self.tables_data)  # Lưu lại toàn bộ list
                    print("Debug: Đã lưu tables.json.")
                    self.update_tables_display()  # Cập nhật lại UI ngay
                    if hasattr(self, "admin_panel") and isinstance(
                        self.admin_panel, AdminPanel
                    ):
                        self.admin_panel.refresh_data()
                        print("Debug: Đã refresh AdminPanel.")
                except Exception as e:
                    QMessageBox.critical(
                        self, "Lỗi Lưu", f"Không thể lưu trạng thái bàn: {e}"
                    )
            else:
                print(
                    f"Cảnh báo: Không tìm thấy item ID {table_id} để cập nhật sau dialog."
                )
        else:
            print(f"Debug: OrderDialog cho {table_id} đã bị hủy (Rejected).")

    # --- Stylesheet ---
    def apply_stylesheet(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #ffffff; font-family: Inter; }
            #viewTitle { font-size: 24px; font-weight: bold; color: #343a40; padding-bottom: 10px; }
            
            QPushButton#tableButton, QPushButton#takeawayButtonGrid {
                font-size: 15px; font-weight: bold; border-radius: 12px;
                padding: 10px; line-height: 1.5; min-height: 130px;
                white-space: pre-wrap; /* Đảm bảo xuống dòng */
            }
            QPushButton#tableButton:hover, QPushButton#takeawayButtonGrid:hover {
                border: 3px solid rgba(0, 0, 0, 0.2);
            }
            QPushButton#tableButton[status="empty"] {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34d399, stop:1 #10b981);
                color: white; border: 1px solid #059669;
            }
            QPushButton#tableButton[status="empty"]:hover { background-color: #10b981; }
            QPushButton#tableButton[status="occupied"] {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fb923c, stop:1 #f97316);
                color: white; border: 1px solid #ea580c;
            }
            QPushButton#tableButton[status="occupied"]:hover { background-color: #f97316; }
            
            QPushButton#takeawayButtonGrid {
                background-color: #0d6efd; color: white; border: 1px solid #0a58ca;
            }
            QPushButton#takeawayButtonGrid[hasOrder="true"] {
                background-color: #ffc107; color: #333; border: 1px solid #e0a800;
            }
            QPushButton#takeawayButtonGrid:hover { background-color: #0b5ed7; }
            QPushButton#takeawayButtonGrid[hasOrder="true"]:hover { background-color: #e0a800; }

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
