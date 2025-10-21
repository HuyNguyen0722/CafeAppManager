import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from utils.data_manager import migrate_menu_to_include_ids # Import the new function

def main():
    """Hàm chính để chạy ứng dụng."""
    app = QApplication(sys.argv)

    migrate_menu_to_include_ids()

    login_dialog = LoginDialog()
    
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        current_user = login_dialog.user_data
        window = MainWindow(current_user)
        window.show()
        sys.exit(app.exec())

if __name__ == '__main__':
    main()

