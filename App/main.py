import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QObject
import traceback # Import traceback để in lỗi chi tiết

# --- Path Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# --- Imports ---
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from utils.data_manager import migrate_menu_to_include_ids

# --- Application Controller ---
class AppController(QObject):
    """Quản lý vòng đời ứng dụng."""
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.login_dialog = None
        self.main_window = None
        print("Debug: AppController khởi tạo, bắt đầu đăng nhập.")
        self.start_login()

    def start_login(self):
        """Hiển thị màn hình đăng nhập."""
        print("Debug: Bắt đầu hàm start_login.")
        # Dọn dẹp cửa sổ chính cũ
        if self.main_window:
            print("Debug: Đóng và xóa MainWindow cũ.")
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None

        print("Debug: Tạo LoginDialog.")
        self.login_dialog = LoginDialog()
        self.login_dialog.accepted.connect(self.start_main)
        self.login_dialog.rejected.connect(self.app.quit) # Thoát nếu cancel
        print("Debug: Hiển thị LoginDialog.")
        self.login_dialog.show()
        print("Debug: Kết thúc hàm start_login.")

    def start_main(self):
        """Hiển thị cửa sổ chính sau khi đăng nhập."""
        print("\nDebug: Bắt đầu hàm start_main.") # Thêm dòng trống cho dễ nhìn
        if not self.login_dialog or not self.login_dialog.user_data:
             print("LỖI: LoginDialog hoặc user_data không tồn tại!")
             self.app.quit()
             return

        current_user = self.login_dialog.user_data
        print(f"Debug: User đăng nhập: {current_user.get('username')}, Role: {current_user.get('role')}")

        try:
            print("Debug: Đang khởi tạo MainWindow...")
            self.main_window = MainWindow(current_user)
            print("Debug: Đã khởi tạo MainWindow.")

            self.main_window.logout_requested.connect(self.start_login)
            print("Debug: Đã kết nối signal logout.")

            print("Debug: Bắt đầu gọi self.main_window.show().")
            self.main_window.show()
            print("Debug: Đã gọi xong self.main_window.show().")

        except Exception as e:
             # In lỗi chi tiết nếu có vấn đề khi tạo hoặc show MainWindow
             print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
             print(f"LỖI NGHIÊM TRỌNG TRONG start_main KHI TẠO/HIỂN THỊ MainWindow: {e}")
             print("-------------------------------------------------------------")
             traceback.print_exc() # In chi tiết stack trace
             print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
             self.app.quit()
             return # Dừng hàm

        if self.login_dialog:
            print("Debug: Đóng và xóa LoginDialog.")
            self.login_dialog.close()
            self.login_dialog.deleteLater()
            self.login_dialog = None

        print("Debug: Kết thúc hàm start_main.")

def main():
    """Hàm chính chạy ứng dụng."""
    app = QApplication(sys.argv)

    # --- Font setup ---
    try:
        default_font = app.font()
        default_font.setPointSize(default_font.pointSize() + 2)
        app.setFont(default_font)
        print("Debug: Đã cài đặt font.")
    except Exception as e:
        print(f"Lỗi khi cài đặt font: {e}")


    # --- Migrate menu ---
    try:
        migrate_menu_to_include_ids()
        print("Debug: Đã kiểm tra/migrate menu IDs.")
    except Exception as e:
        print(f"Lỗi khi migrate menu IDs: {e}")


    # --- Khởi tạo Controller ---
    try:
        print("Debug: Khởi tạo AppController.")
        controller = AppController(app)
        print("Debug: Bắt đầu vòng lặp sự kiện app.exec().")
        sys.exit(app.exec())
    except Exception as e:
        # Bắt lỗi tổng quát cuối cùng nếu có
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"LỖI KHÔNG XÁC ĐỊNH TRONG HÀM MAIN: {e}")
        print("-------------------------------------------------------------")
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        sys.exit(1) # Thoát với mã lỗi


if __name__ == '__main__':
    main()