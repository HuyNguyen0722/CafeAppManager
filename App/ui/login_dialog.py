from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from utils.data_manager import get_users, hash_password

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng nhập - Hệ thống Quản lý Cafe")
        self.setFixedSize(700, 400) # Adjusted size for the new layout
        self.setModal(True)
        self.user_data = None

        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left side (Logo and Brand)
        left_frame = QFrame()
        left_frame.setObjectName("leftFrame")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_label = QLabel("☕")
        logo_label.setObjectName("logoLabel")
        
        title_label = QLabel("Tên Quán Cafe")
        title_label.setObjectName("brandTitle")
        
        subtitle_label = QLabel("Hệ thống Quản lý Bán hàng")
        subtitle_label.setObjectName("brandSubtitle")

        left_layout.addWidget(logo_label)
        left_layout.addWidget(title_label)
        left_layout.addWidget(subtitle_label)
        
        # Right side (Login Form)
        right_frame = QFrame()
        right_frame.setObjectName("rightFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.setContentsMargins(40, 40, 40, 40)

        login_title = QLabel("Đăng nhập")
        login_title.setObjectName("loginTitle")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Đăng nhập")
        self.login_button.clicked.connect(self.handle_login)

        right_layout.addWidget(login_title)
        right_layout.addSpacing(20)
        right_layout.addWidget(QLabel("Tài khoản"))
        right_layout.addWidget(self.username_input)
        right_layout.addSpacing(10)
        right_layout.addWidget(QLabel("Mật khẩu"))
        right_layout.addWidget(self.password_input)
        right_layout.addSpacing(30)
        right_layout.addWidget(self.login_button)
        right_layout.addStretch()

        main_layout.addWidget(left_frame, 1) # 1/3 of the width
        main_layout.addWidget(right_frame, 2) # 2/3 of the width
        
        self.apply_stylesheet()

    def handle_login(self):
        users = get_users()
        username = self.username_input.text()
        password = self.password_input.text()
        hashed_password = hash_password(password)

        for user in users:
            if user['username'] == username and user['password'] == hashed_password:
                self.user_data = user
                self.accept()
                return
        
        QMessageBox.warning(self, "Đăng nhập thất bại", "Tên đăng nhập hoặc mật khẩu không đúng.")

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog {
                font-family: Inter;
            }
            /* --- Left Side --- */
            #leftFrame {
                background-color: #007bff;
            }
            #logoLabel {
                font-size: 80px;
                color: white;
                text-align: center;
                margin-bottom: 10px;
            }
            #brandTitle, #brandSubtitle {
                color: white;
                text-align: center;
            }
            #brandTitle {
                font-size: 24px;
                font-weight: bold;
            }
            #brandSubtitle {
                font-size: 14px;
                color: #e0e0e0;
            }

            /* --- Right Side --- */
            #rightFrame {
                background-color: #ffffff;
            }
            #loginTitle {
                font-size: 28px;
                font-weight: bold;
                color: #333;
                text-align: center;
            }
            QLabel {
                font-size: 14px;
                color: #555;
            }
            QLineEdit {
                padding: 12px;
                font-size: 15px;
                border: 1px solid #ced4da;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

