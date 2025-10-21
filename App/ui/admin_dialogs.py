from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QDialogButtonBox, QComboBox, QMessageBox, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt
import uuid

from utils.data_manager import copy_image_to_data

class UserDialog(QDialog):
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        
        self.setWindowTitle("Thông tin Nhân viên")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit(self.user_data['username'] if self.user_data else "")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Để trống nếu không muốn đổi")
        self.role_input = QComboBox()
        self.role_input.addItems(["staff", "admin"])

        if self.user_data:
            self.username_input.setReadOnly(True) # Cannot change username
            current_role = self.user_data.get('role', 'staff')
            self.role_input.setCurrentText(current_role)
        
        form_layout.addRow("Tên đăng nhập:", self.username_input)
        form_layout.addRow("Mật khẩu mới:", self.password_input)
        form_layout.addRow("Vai trò:", self.role_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(buttons)

    def get_data(self):
        data = {
            "username": self.username_input.text(),
            "role": self.role_input.currentText()
        }
        if self.password_input.text():
            data["password"] = self.password_input.text()
        return data

class MenuItemDialog(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.selected_image_path = None

        self.setWindowTitle("Thông tin Món ăn")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(self.item_data['name'] if self.item_data else "")
        self.price_input = QLineEdit(str(self.item_data['price']) if self.item_data else "")
        self.category_input = QLineEdit(self.item_data['category'] if self.item_data else "")
        self.image_path_label = QLabel(self.item_data.get('image', 'Chưa có ảnh') if self.item_data else "Chưa có ảnh")
        
        select_image_button = QPushButton("Chọn ảnh...")
        select_image_button.clicked.connect(self.select_image)

        form_layout.addRow("Tên món:", self.name_input)
        form_layout.addRow("Giá (VND):", self.price_input)
        form_layout.addRow("Danh mục:", self.category_input)
        form_layout.addRow("Đường dẫn ảnh:", self.image_path_label)
        form_layout.addRow(select_image_button)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(buttons)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh món ăn", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            self.selected_image_path = file_path
            self.image_path_label.setText(file_path)

    def get_data(self):
        price = 0
        try:
            price = float(self.price_input.text())
        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Giá tiền phải là một con số.")
            return None

        data = {
            "id": self.item_data.get('id') if self.item_data else str(uuid.uuid4()),
            "name": self.name_input.text(),
            "price": price,
            "category": self.category_input.text()
        }

        # Handle image path
        if self.selected_image_path:
            # A new image was selected, so copy it and get the new path
            new_image_path = copy_image_to_data(self.selected_image_path)
            if new_image_path:
                data['image'] = new_image_path
        elif self.item_data:
            # No new image, keep the old one if it exists
            data['image'] = self.item_data.get('image', '')
        else:
            # New item without a selected image
            data['image'] = ''
            
        return data

