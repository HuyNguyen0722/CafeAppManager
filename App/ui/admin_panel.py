import traceback
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QMessageBox,
    QDateEdit,
    QCalendarWidget,
    QFormLayout,
    QScrollArea,
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QSizePolicy,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QDate
import os
import datetime
from decimal import Decimal

import matplotlib

matplotlib.use("QtAgg")  # Hoặc Qt6Agg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from utils.data_manager import (
    get_users,
    add_user,
    update_user,
    delete_user,
    get_menu,
    add_menu_item,
    update_menu_item,
    delete_menu_item,
    get_receipts,
    get_attendance_records,
    calculate_salary,
    PROJECT_ROOT,
)
from ui.admin_dialogs import UserDialog, MenuItemDialog


# --- Lớp vẽ biểu đồ ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)

    def update_plot(self, dates, sales):
        self.axes.cla()  # Xóa biểu đồ cũ
        if dates and sales:
            self.axes.bar(dates, sales, color="#007bff")
            self.axes.set_title("Doanh thu theo ngày")
            self.axes.set_ylabel("Tổng doanh thu (VND)")
            self.axes.figure.autofmt_xdate()  # Tự xoay ngày cho đẹp
        else:
            self.axes.text(
                0.5,
                0.5,
                "Không có dữ liệu",
                horizontalalignment="center",
                verticalalignment="center",
                transform=self.axes.transAxes,
            )
        self.draw()


# --- Dialog chi tiết hóa đơn ---
class ReceiptDetailDialog(QDialog):
    def __init__(self, receipt_data, parent=None):
        super().__init__(parent)
        self.receipt_data = receipt_data
        self.setWindowTitle(
            f"Chi tiết Hóa đơn: {self.receipt_data.get('id','N/A')[:8]}..."
        )
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)

        # Thông tin chung
        form_layout = QFormLayout()
        form_layout.addRow("ID Hóa đơn:", QLabel(self.receipt_data.get("id", "N/A")))
        form_layout.addRow(
            "Nhân viên:", QLabel(self.receipt_data.get("employee", "N/A"))
        )
        form_layout.addRow(
            "Bàn số:", QLabel(str(self.receipt_data.get("table_id", "N/A")))
        )
        ts = "N/A"
        try:
            if self.receipt_data.get("timestamp"):
                ts = datetime.datetime.fromisoformat(
                    self.receipt_data["timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass  # Ignore if timestamp format is wrong
        form_layout.addRow("Thời gian:", QLabel(ts))
        layout.addLayout(form_layout)

        # Bảng chi tiết
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(
            ["Tên món", "Số lượng", "Đơn giá", "Thành tiền"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        items = self.receipt_data.get("items", {})
        self.items_table.setRowCount(len(items))
        for row, (item_name, details) in enumerate(items.items()):
            quantity = details.get("quantity", 0)
            price = details.get("price", 0)
            subtotal = quantity * price
            self.items_table.setItem(row, 0, QTableWidgetItem(str(item_name)))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{price:,.0f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{subtotal:,.0f}"))
        layout.addWidget(self.items_table)

        # Tổng tiền
        total_label = QLabel(f"TỔNG CỘNG: {self.receipt_data.get('total', 0):,.0f} VND")
        total_label.setObjectName("totalReceiptLabel")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setStyleSheet(
            """#totalReceiptLabel {font-size: 18px; font-weight: bold; color: #28a745; padding-top: 10px;} QTableWidget {border-radius: 0px;}"""
        )


# --- Bảng điều khiển Admin ---
class AdminPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        self.tabs = QTabWidget()

        # Tạo các tab widget
        self.users_tab = QWidget()
        self.menu_tab = QWidget()
        self.stats_tab = QWidget()
        self.attendance_tab = QWidget()
        self.salary_tab = QWidget()

        # Thêm tab vào QTabWidget
        self.tabs.addTab(self.users_tab, "👥 Quản lý Nhân viên")
        self.tabs.addTab(self.menu_tab, "🍔 Quản lý Thực đơn")
        self.tabs.addTab(self.stats_tab, "📈 Thống kê Doanh thu")
        self.tabs.addTab(self.attendance_tab, "🗓️ Quản lý Chấm công")
        self.tabs.addTab(self.salary_tab, "💰 Báo cáo Lương")

        main_layout.addWidget(self.tabs)

        # Khởi tạo UI cho từng tab
        self.init_users_tab()
        self.init_menu_tab()
        self.init_stats_tab()
        self.init_attendance_tab()
        self.init_salary_tab()

        self.apply_stylesheet()

    def refresh_data(self):
        """Tải lại dữ liệu cho tất cả các tab."""
        self.load_users_data()
        self.load_menu_data()
        self.load_statistics_data()
        self.load_attendance_data()
        self.update_salary_filters()  # Chỉ cần cập nhật filter lương

    # --- Tab Quản lý Nhân viên ---
    def init_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        layout.setContentsMargins(10, 15, 10, 10)
        # Nút bấm
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
        layout.addLayout(button_layout)
        # Bảng
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(
            [
                "Tên đăng nhập",
                "Họ và tên",
                "Địa chỉ",
                "Gmail",
                "Ngày sinh",
                "Vị trí",
                "Lương/giờ",
            ]
        )
        self.users_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.users_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )  # Username
        self.users_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )  # Role
        self.users_table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents
        )  # Salary
        self.users_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )  # Stretch Rows
        self.users_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )  # Allow vertical expand
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        layout.addWidget(self.users_table)
        self.load_users_data()

    def load_users_data(self):
        users = get_users()
        self.users_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.users_table.setItem(
                row, 0, QTableWidgetItem(user.get("username", "N/A"))
            )
            self.users_table.setItem(row, 1, QTableWidgetItem(user.get("name", "N/A")))
            self.users_table.setItem(
                row, 2, QTableWidgetItem(user.get("address", "N/A"))
            )
            self.users_table.setItem(row, 3, QTableWidgetItem(user.get("gmail", "N/A")))
            self.users_table.setItem(row, 4, QTableWidgetItem(user.get("dob", "N/A")))
            self.users_table.setItem(row, 5, QTableWidgetItem(user.get("role", "N/A")))
            rate = user.get("hourly_rate", 0.0)
            rate_str = (
                "Chủ quán"
                if user.get("role") == "admin"
                else (f"{rate:,.0f}" if rate is not None else "N/A")
            )
            self.users_table.setItem(row, 6, QTableWidgetItem(rate_str))

    def add_new_user(self):
        dialog = UserDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                if "password" not in data or not data["password"]:
                    QMessageBox.warning(
                        self, "Lỗi", "Khi tạo user mới, mật khẩu là bắt buộc."
                    )
                    return
                try:
                    add_user(data)
                    self.load_users_data()
                    self.update_salary_filters()  # Cập nhật filter lương
                except ValueError as e:
                    QMessageBox.warning(
                        self, "Lỗi", str(e)
                    )  # Hiển thị lỗi trùng username
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {e}")

    def edit_selected_user(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(
                self, "Chưa chọn", "Vui lòng chọn một nhân viên để sửa."
            )
            return
        selected_row = selected_rows[0].row()
        username_item = self.users_table.item(selected_row, 0)
        if not username_item:
            return  # Should not happen, but safety check
        username = username_item.text()
        user_data = next(
            (u for u in get_users() if u.get("username") == username), None
        )

        if user_data:
            dialog = UserDialog(user_data, parent=self)
            if dialog.exec():
                new_data = dialog.get_data()
                if new_data:
                    # Giữ mật khẩu cũ nếu người dùng không nhập mới
                    if "password" not in new_data or not new_data["password"]:
                        new_data["password"] = user_data.get("password")  # Lấy pass cũ
                    try:
                        update_user(username, new_data)
                        self.load_users_data()
                        self.update_salary_filters()  # Cập nhật filter lương
                    except Exception as e:
                        QMessageBox.critical(self, "Lỗi", f"Lỗi cập nhật user: {e}")

    def delete_selected_user(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(
                self, "Chưa chọn", "Vui lòng chọn một nhân viên để xóa."
            )
            return
        selected_row = selected_rows[0].row()
        username_item = self.users_table.item(selected_row, 0)
        if not username_item:
            return
        username = username_item.text()

        # Lấy username người đang đăng nhập từ MainWindow (parent)
        current_user_username = ""
        parent_widget = self.parent()  # Should be MainWindow if nested correctly
        if hasattr(parent_widget, "user_data"):
            current_user_username = parent_widget.user_data.get("username")

        if username == current_user_username:
            QMessageBox.warning(self, "Lỗi", "Bạn không thể xóa chính mình.")
            return
        if username == "admin":
            QMessageBox.critical(self, "Lỗi", "Không thể xóa tài khoản 'admin' gốc.")
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận",
            f"Bạn có chắc muốn xóa nhân viên '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_user(username)
                self.load_users_data()
                self.update_salary_filters()  # Cập nhật filter lương
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi xóa user: {e}")

    # --- Tab Quản lý Thực đơn ---
    def init_menu_tab(self):
        main_tab_layout = QHBoxLayout(self.menu_tab)
        main_tab_layout.setContentsMargins(10, 15, 10, 10)
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(0, 0, 0, 0)
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
        layout.addLayout(button_layout)
        self.menu_table = QTableWidget()
        self.menu_table.setColumnCount(4)
        self.menu_table.setHorizontalHeaderLabels(["ID", "Tên món", "Giá (VND)", "Ảnh"])
        self.menu_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.menu_table.horizontalHeader().setStretchLastSection(True)
        self.menu_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.menu_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.menu_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.menu_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.menu_table.setAlternatingRowColors(True)
        layout.addWidget(self.menu_table)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_widget.setFixedWidth(250)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        preview_title = QLabel("Xem trước ảnh")
        preview_title.setObjectName("previewTitle")
        self.image_preview_label = QLabel("Chọn một món để xem ảnh")
        self.image_preview_label.setFixedSize(230, 230)
        self.image_preview_label.setObjectName("imagePreview")
        right_layout.addWidget(preview_title)
        right_layout.addWidget(self.image_preview_label)
        main_tab_layout.addWidget(left_widget, 1)
        main_tab_layout.addWidget(right_widget)
        self.load_menu_data()
        self.menu_table.itemSelectionChanged.connect(self.display_menu_image)

    def load_menu_data(self):
        menu = get_menu()
        self.menu_table.setRowCount(len(menu))
        for row, item in enumerate(menu):
            self.menu_table.setItem(row, 0, QTableWidgetItem(item.get("id", "N/A")))
            self.menu_table.setItem(row, 1, QTableWidgetItem(item.get("name", "N/A")))
            self.menu_table.setItem(
                row, 2, QTableWidgetItem(f"{item.get('price', 0):,.0f}")
            )
            self.menu_table.setItem(row, 3, QTableWidgetItem(item.get("image", "")))

    def add_new_menu_item(self):
        dialog = MenuItemDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                add_menu_item(data)
                self.load_menu_data()

    def edit_selected_menu_item(self):
        selected_rows = self.menu_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một món để sửa.")
            return
        selected_row = selected_rows[0].row()
        item_id_item = self.menu_table.item(selected_row, 0)
        if not item_id_item:
            return
        item_id = item_id_item.text()
        item_data = next((i for i in get_menu() if i.get("id") == item_id), None)
        if item_data:
            dialog = MenuItemDialog(item_data, parent=self)
            if dialog.exec():
                data = dialog.get_data()
                if data:
                    update_menu_item(item_id, data)
                    self.load_menu_data()

    def delete_selected_menu_item(self):
        selected_rows = self.menu_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một món để xóa.")
            return
        selected_row = selected_rows[0].row()
        item_id_item = self.menu_table.item(selected_row, 0)
        item_name_item = self.menu_table.item(selected_row, 1)
        if not item_id_item or not item_name_item:
            return
        item_id = item_id_item.text()
        item_name = item_name_item.text()
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            f"Bạn có chắc muốn xóa món '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_menu_item(item_id)
            self.load_menu_data()
            self.image_preview_label.clear()
            self.image_preview_label.setText("Chọn một món để xem ảnh")

    def display_menu_image(self):
        selected_rows = self.menu_table.selectionModel().selectedRows()
        if not selected_rows:
            self.image_preview_label.setText("Chọn một món để xem ảnh")
            self.image_preview_label.clear()
            return

        selected_row = selected_rows[0].row()
        image_path_item = self.menu_table.item(selected_row, 3)

        if not image_path_item or not image_path_item.text():
            self.image_preview_label.setText("Món này không có ảnh")
            self.image_preview_label.clear()
            return

        image_path = image_path_item.text()
        # PROJECT_ROOT trỏ vào thư mục App
        full_image_path = os.path.join(PROJECT_ROOT, image_path) if image_path else ""

        # --- THÊM DEBUG ---
        print(f"Debug AdminPreview: Trying path: '{full_image_path}'")
        image_exists = False
        if full_image_path:
            image_exists = os.path.exists(full_image_path)
        print(f"Debug AdminPreview: Path exists? {image_exists}")
        # --- HẾT DEBUG ---

        if full_image_path and image_exists:  # Dùng biến đã kiểm tra
            try:  # Thêm try-except
                pixmap = QPixmap(full_image_path)
                if pixmap.isNull():
                    print(
                        f"LỖI AdminPreview: QPixmap bị null cho file: {full_image_path}"
                    )
                    self.image_preview_label.setText(f"Ảnh bị lỗi:\n{image_path}")
                    self.image_preview_label.clear()
                else:
                    print(f"Debug AdminPreview: Tải ảnh thành công.")
                    self.image_preview_label.setPixmap(
                        pixmap.scaled(
                            self.image_preview_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
            except Exception as e:
                print(f"LỖI AdminPreview: Exception khi tải QPixmap: {e}")
                traceback.print_exc()
                self.image_preview_label.setText(f"Ảnh bị lỗi:\n{image_path}")
                self.image_preview_label.clear()
        else:
            if full_image_path:
                print(
                    f"CẢNH BÁO AdminPreview: File ảnh không tồn tại: {full_image_path}"
                )
            self.image_preview_label.setText(f"Không tìm thấy ảnh:\n{image_path}")
            self.image_preview_label.clear()

    # --- Tab Thống kê Doanh thu ---
    def init_stats_tab(self):
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(10, 15, 10, 10)
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.start_date_input)
        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date_input)
        self.load_stats_button = QPushButton("Tải dữ liệu")
        self.load_stats_button.setObjectName("loadStatsButton")
        self.load_stats_button.clicked.connect(self.load_statistics_data)
        filter_layout.addWidget(self.load_stats_button)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        # Summary
        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(0, 10, 0, 10)
        self.total_revenue_label = QLabel("Tổng doanh thu: 0 VND")
        self.total_revenue_label.setObjectName("totalRevenueLabel")
        summary_layout.addWidget(self.total_revenue_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        # Content (Chart + Table)
        content_layout = QHBoxLayout()
        self.stats_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        content_layout.addWidget(self.stats_canvas, 2)
        receipt_scroll = QScrollArea()
        receipt_scroll.setWidgetResizable(True)
        self.receipts_table = QTableWidget()
        self.receipts_table.setColumnCount(4)
        self.receipts_table.setHorizontalHeaderLabels(
            ["ID Hóa đơn", "Nhân viên", "Ngày", "Tổng tiền"]
        )
        self.receipts_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.receipts_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.receipts_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.receipts_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.receipts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.receipts_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.receipts_table.itemDoubleClicked.connect(self.show_receipt_detail)
        receipt_scroll.setWidget(self.receipts_table)
        content_layout.addWidget(receipt_scroll, 1)
        layout.addLayout(content_layout, 1)
        self.load_statistics_data()

    def load_statistics_data(self):
        start_date = self.start_date_input.date().toPyDate()
        end_date = self.end_date_input.date().toPyDate()
        all_receipts = get_receipts()

        self.filtered_receipts_cache = []
        sales_by_date = {}
        total_revenue = Decimal("0.0")

        self.receipts_table.setRowCount(0)

        for receipt in all_receipts:
            # TRY phải thẳng hàng với FOR
            try:
                # Code bên trong TRY thụt vào 1 mức
                timestamp_str = receipt.get("timestamp")
                receipt_total = Decimal(str(receipt.get("total", 0.0)))
                receipt_employee = receipt.get("employee", "N/A")
                receipt_id_short = receipt.get("id", "N/A")[:8] + "..."

                if not timestamp_str:
                    continue

                receipt_dt = datetime.datetime.fromisoformat(timestamp_str)
                receipt_date = receipt_dt.date()

                if start_date <= receipt_date <= end_date:
                    self.filtered_receipts_cache.append(receipt)
                    total_revenue += receipt_total

                    row = self.receipts_table.rowCount()
                    self.receipts_table.insertRow(row)
                    self.receipts_table.setItem(
                        row, 0, QTableWidgetItem(receipt_id_short)
                    )
                    self.receipts_table.setItem(
                        row, 1, QTableWidgetItem(receipt_employee)
                    )
                    self.receipts_table.setItem(
                        row, 2, QTableWidgetItem(receipt_date.strftime("%Y-%m-%d"))
                    )
                    self.receipts_table.setItem(
                        row, 3, QTableWidgetItem(f"{receipt_total:,.0f} VND")
                    )

                    date_str = receipt_date.strftime("%Y-%m-%d")
                    sales_by_date[date_str] = (
                        sales_by_date.get(date_str, Decimal("0.0")) + receipt_total
                    )

            # EXCEPT phải thẳng hàng với TRY
            except Exception as e:
                print(f"Lỗi xử lý hóa đơn ID {receipt.get('id','N/A')}: {e}")

        self.total_revenue_label.setText(f"Tổng doanh thu: {total_revenue:,.0f} VND")
        sorted_dates = sorted(sales_by_date.keys())
        sorted_sales = [float(sales_by_date[date]) for date in sorted_dates]
        self.stats_canvas.update_plot(sorted_dates, sorted_sales)

    def show_receipt_detail(self, item):
        selected_row = item.row()
        try:
            if 0 <= selected_row < len(self.filtered_receipts_cache):
                receipt_data = self.filtered_receipts_cache[selected_row]
                dialog = ReceiptDetailDialog(receipt_data, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Lỗi", "Chỉ số hàng không hợp lệ.")
        except Exception as e:
            QMessageBox.critical(
                self, "Lỗi", f"Lỗi không xác định khi xem chi tiết: {e}"
            )

    # --- Tab Quản lý Chấm công ---
    def init_attendance_tab(self):
        layout = QVBoxLayout(self.attendance_tab)
        layout.setContentsMargins(10, 15, 10, 10)
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.att_start_date_input = QDateEdit()
        self.att_start_date_input.setCalendarPopup(True)
        self.att_start_date_input.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.att_start_date_input)
        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.att_end_date_input = QDateEdit()
        self.att_end_date_input.setCalendarPopup(True)
        self.att_end_date_input.setDate(QDate.currentDate())
        filter_layout.addWidget(self.att_end_date_input)
        filter_layout.addWidget(QLabel("Nhân viên:"))
        self.att_user_filter = QComboBox()
        self.att_user_filter.addItem("Tất cả")
        filter_layout.addWidget(self.att_user_filter)
        self.load_att_button = QPushButton("Xem Chấm công")
        self.load_att_button.setObjectName("loadAttendanceButton")
        self.load_att_button.clicked.connect(self.load_attendance_data)
        filter_layout.addWidget(self.load_att_button)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        # Table
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(
            ["Nhân viên", "Ngày", "Giờ Check-in", "Giờ Check-out"]
        )
        self.attendance_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.attendance_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.attendance_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.attendance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.attendance_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.attendance_table.setAlternatingRowColors(True)
        layout.addWidget(self.attendance_table)
        self.load_attendance_data()

    def load_attendance_data(self):
        # Cập nhật filter user
        if hasattr(self, "att_user_filter"):
            current_selection = self.att_user_filter.currentText()
            self.att_user_filter.blockSignals(
                True
            )  # Tạm khóa signal để tránh trigger lại load_attendance_data
            self.att_user_filter.clear()
            self.att_user_filter.addItem("Tất cả")
            users = get_users()
            usernames = sorted(
                [u.get("username", "N/A") for u in users]
            )  # Lấy username an toàn
            self.att_user_filter.addItems(usernames)
            index = self.att_user_filter.findText(current_selection)
            if index != -1:
                self.att_user_filter.setCurrentIndex(index)
            self.att_user_filter.blockSignals(False)  # Mở lại signal

        # Lấy giá trị filter
        start_date = self.att_start_date_input.date().toPyDate()
        end_date = self.att_end_date_input.date().toPyDate()
        selected_user = self.att_user_filter.currentText()

        all_records = get_attendance_records()
        self.attendance_table.setRowCount(0)
        all_records.sort(key=lambda x: x.get("check_in_time", ""), reverse=True)

        for record in all_records:
            # TRY phải thẳng hàng với FOR
            try:
                # Code bên trong TRY thụt vào 1 mức
                check_in_str = record.get("check_in_time")
                check_out_str = record.get("check_out_time")
                record_user = record.get("username", "N/A")

                if not check_in_str:
                    continue

                check_in_dt = datetime.datetime.fromisoformat(check_in_str)
                record_date = check_in_dt.date()

                if not (start_date <= record_date <= end_date):
                    continue
                if selected_user != "Tất cả" and record_user != selected_user:
                    continue

                row = self.attendance_table.rowCount()
                self.attendance_table.insertRow(row)

                check_in_time_str = check_in_dt.strftime("%H:%M:%S")
                check_out_time_str = "Chưa Check-out"
                if check_out_str:
                    try:
                        check_out_dt = datetime.datetime.fromisoformat(check_out_str)
                        check_out_time_str = check_out_dt.strftime("%H:%M:%S")
                    except ValueError:
                        check_out_time_str = "Lỗi Giờ Ra"

                self.attendance_table.setItem(row, 0, QTableWidgetItem(record_user))
                self.attendance_table.setItem(
                    row, 1, QTableWidgetItem(record_date.strftime("%Y-%m-%d"))
                )
                self.attendance_table.setItem(
                    row, 2, QTableWidgetItem(check_in_time_str)
                )
                self.attendance_table.setItem(
                    row, 3, QTableWidgetItem(check_out_time_str)
                )

            # EXCEPT phải thẳng hàng với TRY
            except ValueError as ve:
                print(
                    f"Lỗi định dạng thời gian trong bản ghi {record.get('id','N/A')}: {ve}"
                )
            except Exception as e:
                print(f"Lỗi xử lý bản ghi chấm công {record.get('id','N/A')}: {e}")

    # --- Tab Báo cáo Lương ---
    def init_salary_tab(self):
        layout = QVBoxLayout(self.salary_tab)
        layout.setContentsMargins(10, 15, 10, 10)
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.salary_start_date_input = QDateEdit()
        self.salary_start_date_input.setCalendarPopup(True)
        today = QDate.currentDate()
        self.salary_start_date_input.setDate(QDate(today.year(), today.month(), 1))
        filter_layout.addWidget(self.salary_start_date_input)
        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.salary_end_date_input = QDateEdit()
        self.salary_end_date_input.setCalendarPopup(True)
        self.salary_end_date_input.setDate(today)
        filter_layout.addWidget(self.salary_end_date_input)
        filter_layout.addWidget(QLabel("Nhân viên:"))
        self.salary_user_filter = QComboBox()
        self.salary_user_filter.addItem("Tất cả")
        filter_layout.addWidget(self.salary_user_filter)
        self.calculate_salary_button = QPushButton("Tính lương")
        self.calculate_salary_button.setObjectName("calculateSalaryButton")
        self.calculate_salary_button.clicked.connect(self.load_salary_report)
        filter_layout.addWidget(self.calculate_salary_button)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        # Table
        self.salary_table = QTableWidget()
        self.salary_table.setColumnCount(5)
        self.salary_table.setHorizontalHeaderLabels(
            ["Nhân viên", "Kỳ làm việc", "Tổng giờ", "Lương/giờ", "Tổng lương (VND)"]
        )
        self.salary_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.salary_table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.salary_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.salary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.salary_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.salary_table.setAlternatingRowColors(True)
        layout.addWidget(self.salary_table)
        self.update_salary_filters()

    def load_salary_report(self):
        start_date = self.salary_start_date_input.date().toPyDate()
        end_date = self.salary_end_date_input.date().toPyDate()
        selected_user = self.salary_user_filter.currentText()
        self.salary_table.setRowCount(0)
        users_to_calculate = []
        if selected_user == "Tất cả":
            users_to_calculate = [
                u.get("username")
                for u in get_users()
                if u.get("role") != "admin" and u.get("username")
            ]  # Lọc admin và None
        elif selected_user:
            users_to_calculate.append(selected_user)  # Chỉ tính nếu user được chọn

        for username in users_to_calculate:
            try:
                salary_data = calculate_salary(username, start_date, end_date)
                row = self.salary_table.rowCount()
                self.salary_table.insertRow(row)
                period_str = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
                total_hours_str = f"{salary_data.get('total_hours', 0.0):.2f}"
                hourly_rate_str = f"{salary_data.get('hourly_rate', 0.0):,.0f}"
                total_salary_str = f"{salary_data.get('total_salary', Decimal('0.0')):,.0f}"  # Lấy an toàn

                self.salary_table.setItem(row, 0, QTableWidgetItem(username))
                self.salary_table.setItem(row, 1, QTableWidgetItem(period_str))
                self.salary_table.setItem(row, 2, QTableWidgetItem(total_hours_str))
                self.salary_table.setItem(row, 3, QTableWidgetItem(hourly_rate_str))
                self.salary_table.setItem(row, 4, QTableWidgetItem(total_salary_str))

            except ValueError as e:
                print(
                    f"Lỗi khi tính lương cho {username}: {e}"
                )  # Lỗi logic (vd: user k tồn tại)
            except Exception as e:
                print(f"Lỗi không xác định khi tính lương cho {username}: {e}")
                QMessageBox.warning(
                    self,
                    "Lỗi",
                    f"Gặp lỗi khi tính lương cho {username}. Chi tiết xem ở console.",
                )

    def update_salary_filters(self):
        if hasattr(self, "salary_user_filter"):
            current_selection = self.salary_user_filter.currentText()
            self.salary_user_filter.blockSignals(True)
            self.salary_user_filter.clear()
            self.salary_user_filter.addItem("Tất cả")
            users = [
                u for u in get_users() if u.get("role") != "admin" and u.get("username")
            ]
            usernames = sorted([u["username"] for u in users])
            self.salary_user_filter.addItems(usernames)
            index = self.salary_user_filter.findText(current_selection)
            if index != -1:
                self.salary_user_filter.setCurrentIndex(index)
            self.salary_user_filter.blockSignals(False)

    def apply_stylesheet(self):
        self.setStyleSheet(
            """
            AdminPanel { background-color: #ffffff; } QTabWidget::pane { border: 1px solid #e0e0e0; border-top: none; }
            QTabBar::tab { padding: 12px 25px; background-color: #f8f9fa; border: 1px solid #e0e0e0; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 14px; font-weight: bold; color: #495057; }
            QTabBar::tab:selected { background-color: #ffffff; color: #007bff; border-bottom: 1px solid #ffffff; } QTabBar::tab:!selected:hover { background-color: #e9ecef; }
            QTableWidget { border: 1px solid #e9ecef; gridline-color: #f1f3f5; font-size: 14px; border-radius: 8px; } QTableWidget::item { padding: 12px; border-bottom: 1px solid #f1f3f5; }
            QTableWidget::item:selected { background-color: #e7f3ff; color: #0056b3; } QTableWidget::alternate-background { background-color: #f8f9fa; }
            QHeaderView::section { background-color: #f1f3f5; padding: 12px; border: none; border-bottom: 2px solid #e0e0e0; font-size: 14px; font-weight: bold; }
            QPushButton { padding: 10px 15px; border-radius: 6px; font-size: 14px; font-weight: bold; border: none; margin-bottom: 10px; } QPushButton:hover { opacity: 0.9; }
            QPushButton#addUserButton, QPushButton#addButton { background-color: #28a745; color: white; } QPushButton#addUserButton:hover, QPushButton#addButton:hover { background-color: #218838; }
            QPushButton#editUserButton, QPushButton#editButton { background-color: #007bff; color: white; } QPushButton#editUserButton:hover, QPushButton#editButton:hover { background-color: #0056b3; }
            QPushButton#deleteUserButton, QPushButton#deleteButton { background-color: #dc3545; color: white; } QPushButton#deleteUserButton:hover, QPushButton#deleteButton:hover { background-color: #c82333; }
            #previewTitle { font-size: 16px; font-weight: bold; color: #343a40; padding-bottom: 10px; border-bottom: 1px solid #e9ecef; }
            #imagePreview { background-color: #f8f9fa; border: 1px dashed #ced4da; border-radius: 8px; color: #6c757d; qproperty-alignment: 'AlignCenter'; qproperty-wordWrap: true; margin-top: 10px; }
            QDateEdit, QComboBox { padding: 8px; border: 1px solid #ced4da; border-radius: 6px; } QPushButton#loadStatsButton, QPushButton#loadAttendanceButton, QPushButton#calculateSalaryButton { background-color: #007bff; color: white; margin-bottom: 0; }
            QPushButton#loadStatsButton:hover, QPushButton#loadAttendanceButton:hover, QPushButton#calculateSalaryButton:hover { background-color: #0056b3; } #totalRevenueLabel { font-size: 20px; font-weight: bold; color: #28a745; padding: 10px; background-color: #f8f9fa; border-radius: 8px; }
            QScrollArea { border: 1px solid #e9ecef; border-radius: 8px; }
        """
        )
