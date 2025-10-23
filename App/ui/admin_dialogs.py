from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QDialogButtonBox, QComboBox, QMessageBox, QPushButton, QFileDialog,
    QDateEdit
)
from PyQt6.QtCore import Qt, QDate
import uuid

from utils.data_manager import copy_image_to_data, hash_password # Import hash_password here

class UserDialog(QDialog):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Thông tin Nhân viên")
        layout = QVBoxLayout(self); form_layout = QFormLayout()

        # Input fields
        self.username_input = QLineEdit(self.user_data['username'] if self.user_data else "")
        self.password_input = QLineEdit(); self.password_input.setPlaceholderText("Để trống nếu không muốn đổi")
        self.name_input = QLineEdit(self.user_data.get('name', '') if self.user_data else "")
        self.address_input = QLineEdit(self.user_data.get('address', '') if self.user_data else "")
        self.gmail_input = QLineEdit(self.user_data.get('gmail', '') if self.user_data else "")
        self.dob_input = QDateEdit(); self.dob_input.setDisplayFormat("yyyy-MM-dd"); self.dob_input.setCalendarPopup(True)
        if self.user_data and self.user_data.get('dob'): self.dob_input.setDate(QDate.fromString(self.user_data['dob'], "yyyy-MM-dd"))
        else: self.dob_input.setDate(QDate.currentDate())

        self.role_input = QComboBox()
        self.role_input.addItems(["staff", "parttime", "admin"]) # Added parttime

        self.hourly_rate_input = QLineEdit(str(self.user_data.get('hourly_rate', 0.0)) if self.user_data else "0.0")

        self.role_input.currentTextChanged.connect(self.update_hourly_rate_field)

        if self.user_data:
            self.username_input.setReadOnly(True)
            current_role = self.user_data.get('role', 'staff')
            self.role_input.setCurrentText(current_role)
        else:
             self.role_input.setCurrentText("staff")

        self.update_hourly_rate_field(self.role_input.currentText())

        # Add rows to form
        form_layout.addRow("Tên đăng nhập:", self.username_input)
        form_layout.addRow("Mật khẩu mới:", self.password_input)
        form_layout.addRow("Họ và tên:", self.name_input)
        form_layout.addRow("Địa chỉ:", self.address_input)
        form_layout.addRow("Gmail:", self.gmail_input)
        form_layout.addRow("Ngày sinh:", self.dob_input)
        form_layout.addRow("Vị trí (Vai trò):", self.role_input)
        form_layout.addRow("Mức lương/giờ (VND):", self.hourly_rate_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)

        self.setStyleSheet("""QLineEdit, QDateEdit, QComboBox { padding: 8px; border: 1px solid #ced4da; border-radius: 6px; background-color: #f8f9fa; } QLineEdit:focus, QDateEdit:focus, QComboBox:focus { border-color: #007bff; } QComboBox::drop-down { border: none; }""")

        layout.addLayout(form_layout)
        layout.addWidget(buttons)

    def update_hourly_rate_field(self, role):
        if role == "admin":
            self.hourly_rate_input.setText("0.0")
            self.hourly_rate_input.setReadOnly(True)
            self.hourly_rate_input.setStyleSheet("background-color: #e9ecef;")
        elif role == "staff":
            staff_hourly_rate = 7500000 / (8 * 26)
            default_rate = round(staff_hourly_rate, -2)
            if not self.user_data or self.user_data.get('role') != 'staff':
                 self.hourly_rate_input.setText(str(default_rate))
            else:
                 self.hourly_rate_input.setText(str(self.user_data.get('hourly_rate', default_rate)))
            self.hourly_rate_input.setReadOnly(False)
            self.hourly_rate_input.setStyleSheet("")
        elif role == "parttime":
            default_rate = 30000.0
            if not self.user_data or self.user_data.get('role') != 'parttime':
                 self.hourly_rate_input.setText(str(default_rate))
            else:
                 self.hourly_rate_input.setText(str(self.user_data.get('hourly_rate', default_rate)))
            self.hourly_rate_input.setReadOnly(False)
            self.hourly_rate_input.setStyleSheet("")

    def get_data(self):
        hourly_rate = 0.0
        try:
            hourly_rate = float(self.hourly_rate_input.text())
            if hourly_rate < 0: QMessageBox.warning(self, "Lỗi", "Mức lương không thể là số âm."); return None
        except ValueError: QMessageBox.warning(self, "Lỗi", "Mức lương phải là một con số."); return None

        role = self.role_input.currentText()
        if role == "admin": hourly_rate = 0.0

        data = {
            "username": self.username_input.text(), "role": role,
            "name": self.name_input.text(), "address": self.address_input.text(),
            "gmail": self.gmail_input.text(), "dob": self.dob_input.date().toString("yyyy-MM-dd"),
            "hourly_rate": hourly_rate
        }
        if self.password_input.text():
            data["password"] = hash_password(self.password_input.text()) # Hash password here
        return data

class MenuItemDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.selected_image_path = None
        self.setWindowTitle("Thông tin Món ăn")
        layout = QVBoxLayout(self); form_layout = QFormLayout()

        self.name_input = QLineEdit(self.item_data['name'] if self.item_data else "")
        self.price_input = QLineEdit(str(self.item_data['price']) if self.item_data else "")
        self.category_input = QLineEdit(self.item_data['category'] if self.item_data else "")
        self.image_path_label = QLabel(self.item_data.get('image', 'Chưa có ảnh') if self.item_data else "Chưa có ảnh")
        select_image_button = QPushButton("Chọn ảnh..."); select_image_button.clicked.connect(self.select_image)

        self.setStyleSheet("""QLineEdit { padding: 8px; border: 1px solid #ced4da; border-radius: 6px; background-color: #f8f9fa; } QLineEdit:focus { border-color: #007bff; }""")

        form_layout.addRow("Tên món:", self.name_input)
        form_layout.addRow("Giá (VND):", self.price_input)
        form_layout.addRow("Danh mục:", self.category_input)
        form_layout.addRow("Đường dẫn ảnh:", self.image_path_label)
        form_layout.addRow(select_image_button)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addLayout(form_layout); layout.addWidget(buttons)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh món ăn", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path: self.selected_image_path = file_path; self.image_path_label.setText(file_path)

    def get_data(self):
        price = 0.0
        try: price = float(self.price_input.text())
        except ValueError: QMessageBox.warning(self, "Lỗi", "Giá tiền phải là một con số."); return None
        if price < 0: QMessageBox.warning(self, "Lỗi", "Giá tiền không thể âm."); return None

        data = {
            "id": self.item_data.get('id') if self.item_data else str(uuid.uuid4()),
            "name": self.name_input.text(), "price": price, "category": self.category_input.text()
        }
        if self.selected_image_path:
            new_image_path = copy_image_to_data(self.selected_image_path)
            if new_image_path: data['image'] = new_image_path
        elif self.item_data: data['image'] = self.item_data.get('image', '')
        else: data['image'] = ''
        return data