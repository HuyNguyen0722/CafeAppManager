import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QObject 

# --- Path Setup ---
# --- SỬA LẠI: Quay về bản gốc ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)
# -----------------------------

# --- SỬA LẠI: Bỏ "App." ra khỏi import ---
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from utils.data_manager import migrate_menu_to_include_ids
# -------------------------------------

# (Lớp AppController giữ nguyên)
class AppController(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.login_dialog = None
        self.main_window = None
        self.start_login()

    def start_login(self):
        if self.main_window:
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None

        self.login_dialog = LoginDialog()
        self.login_dialog.accepted.connect(self.start_main)
        self.login_dialog.rejected.connect(self.app.quit)
        self.login_dialog.show()

    def start_main(self):
        current_user = self.login_dialog.user_data
        self.main_window = MainWindow(current_user)
        self.main_window.logout_requested.connect(self.start_login) 
        self.main_window.show()
        
        if self.login_dialog:
            self.login_dialog.close()
            self.login_dialog.deleteLater()
            self.login_dialog = None

def main():
    """Hàm chính để chạy ứng dụng."""
    app = QApplication(sys.argv)

    default_font = app.font()
    default_font.setPointSize(default_font.pointSize() + 2) 
    app.setFont(default_font)

    migrate_menu_to_include_ids()
    controller = AppController(app)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()