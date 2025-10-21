from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, 
    QPushButton, QLabel, QTabWidget, QHBoxLayout, QFrame,
    QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.data_manager import get_tables, save_tables
from ui.order_dialog import OrderDialog
from ui.admin_panel import AdminPanel

class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle(f"Hệ thống Cafe - Nhân viên: {self.user_data['username']}")
        self.setGeometry(100, 100, 1000, 650) 
        
        self.tables_data = get_tables()

        if self.user_data.get('role') == 'admin':
            self.setup_admin_ui()
        else:
            self.setup_staff_ui()
        
        self.apply_stylesheet()
        self.update_tables_display()


    def setup_staff_ui(self):
        """Thiết lập giao diện cho nhân viên."""
        tables_widget = self.create_tables_widget()
        self.setCentralWidget(tables_widget)

    def setup_admin_ui(self):
        """Thiết lập giao diện cho quản trị viên với panel điều hướng bên trái."""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Navigation Panel (Left Sidebar) ---
        nav_panel = QFrame()
        nav_panel.setObjectName("navPanel")
        nav_panel.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(10, 20, 10, 10)
        nav_layout.setSpacing(10)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        app_title = QLabel("CafeManager")
        app_title.setObjectName("navTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(app_title)
        
        # Navigation Buttons
        self.tables_nav_button = QPushButton("🍽️  Sơ đồ bàn")
        self.tables_nav_button.setObjectName("navButton")
        self.tables_nav_button.setCheckable(True)
        
        self.admin_nav_button = QPushButton("⚙️  Bảng Quản lý")
        self.admin_nav_button.setObjectName("navButton")
        self.admin_nav_button.setCheckable(True)

        nav_layout.addWidget(self.tables_nav_button)
        nav_layout.addWidget(self.admin_nav_button)

        # --- Content Panel (Right Side) ---
        self.stacked_widget = QStackedWidget()
        self.tables_widget = self.create_tables_widget()
        self.admin_panel = AdminPanel()
        
        self.stacked_widget.addWidget(self.tables_widget)
        self.stacked_widget.addWidget(self.admin_panel)

        # Add panels to main layout
        main_layout.addWidget(nav_panel)
        main_layout.addWidget(self.stacked_widget, 1)

        # --- Button Logic ---
        self.tables_nav_button.clicked.connect(self.switch_to_tables)
        self.admin_nav_button.clicked.connect(self.switch_to_admin)
        
        # Initial state
        self.switch_to_tables()
        
        self.setCentralWidget(main_widget)
        
    def switch_to_tables(self):
        self.stacked_widget.setCurrentIndex(0)
        self.tables_nav_button.setChecked(True)
        self.admin_nav_button.setChecked(False)

    def switch_to_admin(self):
        self.stacked_widget.setCurrentIndex(1)
        self.tables_nav_button.setChecked(False)
        self.admin_nav_button.setChecked(True)

    def create_tables_widget(self):
        """Tạo widget chứa sơ đồ bàn."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        # Add a title for the tables view
        title_label = QLabel("Tổng quan Sơ đồ bàn")
        title_label.setObjectName("viewTitle")
        main_layout.addWidget(title_label)
        
        self.tables_grid = QGridLayout()
        self.table_buttons = {}

        for table in self.tables_data:
            table_id = table['id']
            button = QPushButton(f"Bàn {table_id}")
            button.setMinimumSize(130, 130)
            button.clicked.connect(lambda ch, t_id=table_id: self.open_order_dialog(t_id))
            self.table_buttons[table_id] = button
            
            row = (table_id - 1) // 5 
            col = (table_id - 1) % 5
            self.tables_grid.addWidget(button, row, col)
            
        main_layout.addLayout(self.tables_grid)
        return widget

    def update_tables_display(self):
        """Cập nhật giao diện các bàn (màu sắc, text)."""
        self.tables_data = get_tables() # Always get fresh data
        for table in self.tables_data:
            button = self.table_buttons[table['id']]
            status = table['status']
            employee = table.get('employee', 'Trống')
            
            button.setText(f"Bàn {table['id']}\n{status}\nNV: {employee}")
            
            if status == "Trống":
                button.setProperty("status", "empty")
            else:
                button.setProperty("status", "occupied")
            
            button.style().unpolish(button)
            button.style().polish(button)

    def open_order_dialog(self, table_id):
        table_index = next(i for i, t in enumerate(self.tables_data) if t['id'] == table_id)
        
        dialog = OrderDialog(self.tables_data[table_index], self.user_data['username'], self)
        if dialog.exec():
            save_tables(self.tables_data)
            self.update_tables_display()
            if hasattr(self, 'admin_panel'):
                self.admin_panel.refresh_data()


    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #ffffff;
                font-family: Inter;
            }
            #viewTitle {
                font-size: 24px;
                font-weight: bold;
                color: #343a40;
                padding-bottom: 10px;
            }
            QPushButton[status] {
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 12px;
                padding: 10px;
                line-height: 1.5;
            }
            QPushButton[status]:hover {
                border: 3px solid rgba(255, 255, 255, 0.7);
            }
            QPushButton[status="empty"] {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #34d399, stop: 1 #10b981);
                border: 1px solid #059669;
            }
            QPushButton[status="occupied"] {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #fb923c, stop: 1 #f97316);
                border: 1px solid #ea580c;
            }
            
            /* --- Styles for Admin Navigation Panel --- */
            #navPanel {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
            #navTitle {
                font-size: 22px;
                font-weight: bold;
                color: #343a40;
                padding-bottom: 20px;
            }
            QPushButton#navButton {
                background: transparent;
                border: none;
                padding: 15px 20px;
                font-size: 15px;
                font-weight: bold;
                color: #495057;
                text-align: left;
                border-radius: 8px;
            }
            QPushButton#navButton:hover {
                background: #f1f3f5;
            }
            QPushButton#navButton:checked {
                background: #e9ecef;
                color: #007bff;
            }
        """)

