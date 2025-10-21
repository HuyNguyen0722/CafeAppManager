from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt

from utils.data_manager import (
    get_users, add_user, update_user, delete_user,
    get_menu, add_menu_item, update_menu_item, delete_menu_item
)
from ui.admin_dialogs import UserDialog, MenuItemDialog

class AdminPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.tabs = QTabWidget()
        
        # --- Create Tabs ---
        self.users_tab = QWidget()
        self.menu_tab = QWidget()
        
        self.tabs.addTab(self.users_tab, "Quản lý Nhân viên")
        self.tabs.addTab(self.menu_tab, "Quản lý Thực đơn")
        
        main_layout.addWidget(self.tabs)
        
        # --- Initialize UI for each tab ---
        self.init_users_tab()
        self.init_menu_tab()
        
        self.apply_stylesheet()

    def refresh_data(self):
        """Public method to reload all data in the panel."""
        self.load_users_data()
        self.load_menu_data()

    # --- Users Tab ---
    def init_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Button layout
        button_layout = QHBoxLayout()
        add_user_button = QPushButton("➕ Thêm Nhân viên")
        add_user_button.setObjectName("addUserButton")
        edit_user_button = QPushButton("✏️ Sửa Nhân viên")
        edit_user_button.setObjectName("editUserButton")
        delete_user_button = QPushButton("🗑️ Xóa Nhân viên")
        delete_user_button.setObjectName("deleteUserButton")
        
        add_user_button.clicked.connect(self.add_new_user)
        edit_user_button.clicked.connect(self.edit_selected_user)
        delete_user_button.clicked.connect(self.delete_selected_user)

        button_layout.addWidget(add_user_button)
        button_layout.addWidget(edit_user_button)
        button_layout.addWidget(delete_user_button)
        button_layout.addStretch()
        
        # Table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(2)
        self.users_table.setHorizontalHeaderLabels(["Tên đăng nhập", "Vai trò"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True) # Enable alternating colors

        layout.addLayout(button_layout)
        layout.addWidget(self.users_table)
        
        self.load_users_data()

    def load_users_data(self):
        users = get_users()
        self.users_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(user['username']))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['role']))

    def add_new_user(self):
        dialog = UserDialog(parent=self) 
        if dialog.exec():
            add_user(dialog.get_data())
            self.load_users_data()

    def edit_selected_user(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một nhân viên để sửa.")
            return
            
        selected_row = selected_rows[0].row()
        username = self.users_table.item(selected_row, 0).text()
        
        users = get_users()
        user_data = next((u for u in users if u['username'] == username), None)

        if user_data:
            dialog = UserDialog(user_data, parent=self) 
            if dialog.exec():
                update_user(username, dialog.get_data())
                self.load_users_data()

    def delete_selected_user(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một nhân viên để xóa.")
            return
            
        selected_row = selected_rows[0].row()
        username = self.users_table.item(selected_row, 0).text()
        
        reply = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa nhân viên '{username}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_user(username)
            self.load_users_data()

    # --- Menu Tab ---
    def init_menu_tab(self):
        layout = QVBoxLayout(self.menu_tab)
        layout.setContentsMargins(10, 15, 10, 10)
        
        button_layout = QHBoxLayout()
        add_item_button = QPushButton("➕ Thêm Món")
        add_item_button.setObjectName("addButton")
        edit_item_button = QPushButton("✏️ Sửa Món")
        edit_item_button.setObjectName("editButton")
        delete_item_button = QPushButton("🗑️ Xóa Món")
        delete_item_button.setObjectName("deleteButton")

        add_item_button.clicked.connect(self.add_new_menu_item)
        edit_item_button.clicked.connect(self.edit_selected_menu_item)
        delete_item_button.clicked.connect(self.delete_selected_menu_item)

        button_layout.addWidget(add_item_button)
        button_layout.addWidget(edit_item_button)
        button_layout.addWidget(delete_item_button)
        button_layout.addStretch()

        self.menu_table = QTableWidget()
        self.menu_table.setColumnCount(4)
        self.menu_table.setHorizontalHeaderLabels(["ID", "Tên món", "Giá (VND)", "Ảnh"])
        self.menu_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.menu_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.menu_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.menu_table.setAlternatingRowColors(True) # Enable alternating colors

        layout.addLayout(button_layout)
        layout.addWidget(self.menu_table)
        
        self.load_menu_data()

    def load_menu_data(self):
        menu = get_menu()
        self.menu_table.setRowCount(len(menu))
        for row, item in enumerate(menu):
            self.menu_table.setItem(row, 0, QTableWidgetItem(item.get('id', 'N/A')))
            self.menu_table.setItem(row, 1, QTableWidgetItem(item.get('name', 'N/A')))
            self.menu_table.setItem(row, 2, QTableWidgetItem(f"{item.get('price', 0):,.0f}"))
            self.menu_table.setItem(row, 3, QTableWidgetItem(item.get('image', '')))

    def add_new_menu_item(self):
        dialog = MenuItemDialog(parent=self) 
        if dialog.exec():
            add_menu_item(dialog.get_data())
            self.load_menu_data()

    def edit_selected_menu_item(self):
        selected_rows = self.menu_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một món để sửa.")
            return

        selected_row = selected_rows[0].row()
        item_id = self.menu_table.item(selected_row, 0).text()
        
        menu = get_menu()
        item_data = next((i for i in menu if i.get('id') == item_id), None)

        if item_data:
            dialog = MenuItemDialog(item_data, parent=self) 
            if dialog.exec():
                update_menu_item(item_id, dialog.get_data())
                self.load_menu_data()

    def delete_selected_menu_item(self):
        selected_rows = self.menu_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một món để xóa.")
            return

        selected_row = selected_rows[0].row()
        item_id = self.menu_table.item(selected_row, 0).text()
        item_name = self.menu_table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa món '{item_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_menu_item(item_id)
            self.load_menu_data()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            AdminPanel {
                background-color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-top: none;
            }
            QTabBar::tab {
                padding: 12px 25px;
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                color: #495057;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #007bff;
                border-bottom: 1px solid #ffffff;
            }
            QTabBar::tab:!selected:hover {
                background-color: #e9ecef;
            }
            QTableWidget {
                border: 1px solid #e9ecef;
                gridline-color: #f1f3f5;
                font-size: 14px;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f1f3f5;
            }
            QTableWidget::item:selected {
                background-color: #e7f3ff;
                color: #0056b3;
            }
            QTableWidget::alternate-background {
                background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #f1f3f5;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                padding: 10px 15px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton#addUserButton, QPushButton#addButton {
                background-color: #28a745;
                color: white;
            }
            QPushButton#addUserButton:hover, QPushButton#addButton:hover {
                background-color: #218838;
            }
            QPushButton#editUserButton, QPushButton#editButton {
                background-color: #007bff;
                color: white;
            }
            QPushButton#editUserButton:hover, QPushButton#editButton:hover {
                background-color: #0056b3;
            }
            QPushButton#deleteUserButton, QPushButton#deleteButton {
                background-color: #dc3545;
                color: white;
            }
            QPushButton#deleteUserButton:hover, QPushButton#deleteButton:hover {
                background-color: #c82333;
            }
        """)

